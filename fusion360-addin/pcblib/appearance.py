import adsk.core, adsk.fusion, adsk.cam, traceback, os

CMDID = 'PCBAppearances'

_app = None
_ui = None

_texWidth = None
_texHeight = None
_copperThickness = None
_texTopColor = None
_texTopHmap = None
_texTopMask = None
_texBottomColor = None
_texBottomHmap = None
_texBottomMask = None
_errMessage = None
_bunchTexButton = None

_texTopColorPath = None
_texTopHmapPath = None
_texTopMaskPath = None
_texBottomColorPath = None
_texBottomHmapPath = None
_texBottomMaskPath = None

_lastdir = None

_handlers = []

def registerCommand(app, ui):
    global _app, _ui
    _app = app
    _ui  = ui

    cmdDef = _ui.commandDefinitions.itemById(CMDID)
    if not cmdDef:
        cmdDef = _ui.commandDefinitions.addButtonDefinition(
            CMDID, 
            'Generate PCB appearances', 
            'Generate appearances for surfaces of PCB\n',
            './Resources/PCBAppearances')

    # Connect to the command created event.
    onCommandCreated = PACommandCreatedHandler()
    cmdDef.commandCreated.add(onCommandCreated)
    _handlers.append(onCommandCreated)

    return cmdDef

def unregisterCommand(app, ui):
    cmdDef = ui.commandDefinitions.itemById(CMDID)
    if cmdDef:
        cmdDef.deleteMe()

class PACommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global _app, _ui
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            
            # Verify that a Fusion design is active.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            if not des:
                _ui.messageBox('A Fusion design must be active when invoking this command.')
                return()
            defaultUnits = des.unitsManager.defaultLengthUnits

            cmd = eventArgs.command
            cmd.isExecutedWhenPreEmpted = False
            inputs = cmd.commandInputs

            global _texHeight, _texWidth, _copperThickness
            global _texTopColor, _texTopHmap, _texTopMask
            global _texBottomColor, _texBottomHmap, _texBottomMask, _errMessage
            lengthValue = adsk.core.ValueInput.createByString('0' + defaultUnits)
            _texWidth = inputs.addValueInput('texWidth', 'Width', defaultUnits, lengthValue)
            _texHeight = inputs.addValueInput('texHeight', 'Height', defaultUnits, lengthValue)
            thicknessValue = adsk.core.ValueInput.createByString('0.05' + defaultUnits)
            _copperThickness = inputs.addValueInput('copperThickness', 'Copper Thickness', defaultUnits, thicknessValue)
            initText = 'Select a image'
            _texTopColor = inputs.addBoolValueInput('texTopColor', 'Top Color Map', False, )
            _texTopColor.text = initText
            _texTopHmap = inputs.addBoolValueInput('texTopHmap', 'Top Height Map', False, )
            _texTopHmap.text = initText
            _texTopMask = inputs.addBoolValueInput('texTopMask', 'Top Cutout Map', False, )
            _texTopMask.text = initText
            _texBottomColor = inputs.addBoolValueInput('texBottomColor', 'Bottom Color Map', False, )
            _texBottomColor.text = initText
            _texBottomHmap = inputs.addBoolValueInput('texBottomHmap', 'Bottom Height Map', False, )
            _texBottomHmap.text = initText
            _texBottomMask = inputs.addBoolValueInput('texBottomMask', 'Bottom Cutout Map', False, )
            _texBottomMask.text = initText
            _errMessage = inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)
            _errMessage.isFullWidth = True
            _bunchTexButton = inputs.addBoolValueInput('bunchTexButton', 'Select Bunch of Bitmaps', False)
            _bunchTexButton.text = 'Select Bunch of Bitmaps'
            _bunchTexButton.isFullWidth = True

            # Connect to the command related events.
            onExecute = PACommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)        
            
            onInputChanged = PACommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)     
            
            onValidateInputs = PACommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class PACommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global _app, _ui
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            generateAppearances()

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class PACommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global _app, _ui
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            cmd = eventArgs.inputs.command
            changedInput = eventArgs.input

            def selectTextureFile(input, current):
                global _lastdir
                fileDialog = _ui.createFileDialog()
                fileDialog.isMultiSelectEnabled = False
                fileDialog.title = "Select a texture map image file"
                fileDialog.filter = 'Image files (*.png;*.jpg;*.jpeg;*.gif)'
                fileDialog.filterIndex = 0
                if current is not None:
                    fileDialog.initialFilename = os.path.basename(current)
                else:
                    fileDialog.initialFilename = ''

                if _lastdir is not None:
                    fileDialog.initialDirectory = _lastdir

                dialogResult = fileDialog.showOpen()
                if dialogResult == adsk.core.DialogResults.DialogOK:
                    fileName = fileDialog.filename
                    input.text = os.path.basename(fileName)
                    _lastdir = os.path.dirname(fileName)
                    return fileName
                else:
                    return current

            global _texTopColorPath, _texTopHmapPath, _texTopMaskPath
            global _texBottomColorPath, _texBottomHmapPath, _texBottomMaskPath
            global _bunchTexButton
            if changedInput.id == 'texTopColor':
                _texTopColorPath = selectTextureFile(changedInput, _texTopColorPath)
            elif changedInput.id == 'texTopHmap':
                _texTopHmapPath = selectTextureFile(changedInput, _texTopHmapPath)
            elif changedInput.id == 'texTopMask':
                _texTopMaskPath = selectTextureFile(changedInput, _texTopMaskPath)
            elif changedInput.id == 'texBottomColor':
                _texBottomColorPath = selectTextureFile(changedInput, _texBottomColorPath)
            elif changedInput.id == 'texBottomHmap':
                _texBottomHmapPath = selectTextureFile(changedInput, _texBottomHmapPath)
            elif changedInput.id == 'texBottomMask':
                _texBottomMaskPath = selectTextureFile(changedInput, _texBottomMaskPath)
            elif changedInput.id == 'bunchTexButton':
                global _lastdir
                dialog = _ui.createFolderDialog()
                dialog.title = "Select a texture map image file"
                if _lastdir is not None:
                    dialog.initialDirectory = _lastdir
                dialogResult = dialog.showDialog()
                if dialogResult == adsk.core.DialogResults.DialogOK:
                    dir = dialog.folder
                    _lastdir = dir if validateBitmapDir(dir) else _lastdir

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class PACommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global _app, _ui
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)

            global _texWidth, _texHeight, _copperThickness, _errMessage
            global _texTopColorPath, _texTopHmapPath, _texTopMaskPath
            global _texBottomColorPath, _texBottomHmapPath, _texBottomMaskPath

            width = getCommandInputValue(_texWidth, 'in')[1]
            height = getCommandInputValue(_texHeight, 'in')[1]
            thickness = getCommandInputValue(_copperThickness, 'in')[1]

            _errMessage.text = ''
            eventArgs.areInputsValid = False

            if width <= 0 or height <= 0:
                _errMessage.text = 'Width and Height must be number grater than 0.'
            elif thickness < 0:
                _errMessage.text = 'Copper thickness must be number grater than 0 or 0.'
            elif _texTopColorPath is None or _texTopHmapPath is None or _texTopMask is None or \
                 _texBottomColorPath is None or _texBottomHmapPath is None or _texBottomMaskPath is None:
                _errMessage.text = 'All texture map image must be specified.'
            else:
                eventArgs.areInputsValid = True

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def getCommandInputValue(commandInput, unit):
    try:
        valCommandInput = adsk.core.ValueCommandInput.cast(commandInput)
        if not valCommandInput:
            return (False, 0)

        # Verify that the expression is valid.
        des = adsk.fusion.Design.cast(_app.activeProduct)
        unitsMgr = des.unitsManager
        
        if unitsMgr.isValidExpression(valCommandInput.expression, unit):
            value = unitsMgr.evaluateExpression(valCommandInput.expression)
            value = unitsMgr.convert(value, 'cm', unit)
            return (True, value)
        else:
            return (False, 0)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def validateBitmapDir(dir):
    global _texTopColor, _texTopHmap, _texTopMask
    global _texBottomColor, _texBottomHmap, _texBottomMask
    global _texTopColorPath, _texTopHmapPath, _texTopMaskPath
    global _texBottomColorPath, _texBottomHmapPath, _texBottomMaskPath
    files = [
        ('pcb-top-base.png', _texTopColor, '_texTopColorPath'),
        ('pcb-top-hmap.png', _texTopHmap, '_texTopHmapPath'),
        ('pcb-top-mask.png', _texTopMask, '_texTopMaskPath'),
        ('pcb-bottom-base.png', _texBottomColor, '_texBottomColorPath'),
        ('pcb-bottom-hmap.png', _texBottomHmap, '_texBottomHmapPath'),
        ('pcb-bottom-mask.png', _texBottomMask, '_texBottomMaskPath'),
    ]
    numExist = 0
    for file in files:
        name = file[0]
        path = os.path.join(dir, name)
        if os.path.isfile(path):
            numExist += 1
            file[1].text = name
            globals()[file[2]] = path
    return numExist > 0     

def generateAppearances():
    global _app, _ui
    design = _app.activeProduct
    matLibs = _app.materialLibraries

    matLibPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                              '../Resources/pcb.adsklib')
    matLib = matLibs.load(os.path.abspath(matLibPath))
    bNative = matLib.isNative;

    target = design.appearances

    for name in ['top-pcb-base', 'top-pcb-metal', 'bottom-pcb-base', 'bottom-pcb-metal']:
        appear =  target.itemByName(name)
        if appear is not None:
            try:
                appear.deleteMe()
            except:
                pass

    global _texWidth, _texHeight, _copperThicknesss
    global _texTopColorPath, _texTopHmapPath, _texTopMaskPath
    global _texBottomColorPath, _texBottomHmapPath, _texBottomMaskPath
    width = getCommandInputValue(_texWidth, 'in')[1]
    height = getCommandInputValue(_texHeight, 'in')[1]
    thickness = getCommandInputValue(_copperThickness, 'in')[1]
    generateAppearancesForSurface(
        width, height, thickness,
        _texTopColorPath, _texTopHmapPath, _texTopMaskPath,
        'top-', target, matLib
    )
    generateAppearancesForSurface(
        width, height, thickness,
        _texBottomColorPath, _texBottomHmapPath, _texBottomMaskPath,
        'bottom-', target, matLib
    )

    for name in ['pcb-base', 'pcb-metal']:
        appear =  target.itemByName(name)
        if appear is not None:
            appear.deleteMe()

    if bNative == False:
        matLib.unload();

def generateAppearancesForSurface(width, height, thickness, base, hmap, mask, prefix, target, matLib):
    # generate base appearance
    org = matLib.appearances.itemByName('pcb-base')
    appear = target.itemByName(prefix + org.name)
    if appear is None:
        appear = target.addByCopy(org, prefix + org.name)
    color = appear.appearanceProperties.itemById('opaque_albedo')
    texture = color.connectedTexture
    updateTexture(texture, width, height, base)
    texture = appear.appearanceProperties.itemById('surface_normal').value
    updateTexture(texture, width, height, hmap, thickness=thickness)
    texture = appear.appearanceProperties.itemById('surface_cutout').value
    updateTexture(texture, width, height, mask)

    # generate metal appearance
    org = matLib.appearances.itemByName('pcb-metal')
    appear = target.itemByName(prefix + org.name)
    if appear is None:
        appear = target.addByCopy(org, prefix + org.name)
    texture = appear.appearanceProperties.itemById('surface_normal').value
    updateTexture(texture, width, height, hmap)

def updateTexture(texture, width, height, path, thickness=None):
    def updateFloatProp(propId, value):
        orgProp = texture.properties.itemById(propId)
        modProp = adsk.core.FloatProperty.cast(orgProp)
        modProp.value = value
    
    updateFloatProp('texture_RealWorldScaleX', width)
    updateFloatProp('texture_RealWorldScaleY', height)
    updateFloatProp('texture_RealWorldOffsetX', -width/2)
    updateFloatProp('texture_RealWorldOffsetY', -height/2)
    if thickness is not None:
        updateFloatProp('bumpmap_Depth', thickness)
    texture.changeTextureImage(path)