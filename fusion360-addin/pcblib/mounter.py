import adsk.core, adsk.fusion, adsk.cam, traceback, os, importlib, json
from math import pi, cos, sin
from . import placeinfo
placeinfo = importlib.reload(placeinfo)

CMDID = 'PCBMounter'

_app = None
_ui = None

_placeFileButton = None
_componentsFolder = None
_containerComponent = None
_pcbThickness = None
_errMessage = None

_placeFile = None
_verifiedFolderPath = ''
_verifiedFolder = None
_selectedComponent = None

_handlers = []

def registerCommand(app, ui):
    global _app, _ui
    _app = app
    _ui  = ui

    cmdDef = _ui.commandDefinitions.itemById(CMDID)
    if not cmdDef:
        cmdDef = _ui.commandDefinitions.addButtonDefinition(
            CMDID, 
            'Place components on PCB', 
            'Place components on PCB according to mounting infomation exported by Eagle\n',
            './Resources/PCBMounter')

    # Connect to the command created event.
    onCommandCreated = PMCommandCreatedHandler()
    cmdDef.commandCreated.add(onCommandCreated)
    _handlers.append(onCommandCreated)

    return cmdDef

def unregisterCommand(app, ui):
    cmdDef = ui.commandDefinitions.itemById(CMDID)
    if cmdDef:
        cmdDef.deleteMe()

class PMCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global _app, _ui
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)

            global _verifiedFolder, _verifiedFolderPath, _selectedComponent
            _verifiedFolder = None
            _verifiedFolderPath = ''
            _selectedComponent = None

            # Verify that a Fusion design is active.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            if not des:
                _ui.messageBox('A Fusion design must be active when invoking this command.')
                return()

            cmd = eventArgs.command
            cmd.isExecutedWhenPreEmpted = False
            inputs = cmd.commandInputs

            defaultUnits = des.unitsManager.defaultLengthUnits
            attribs = des.attributes

            global _placeFileButton, _componentsFolder, _containerComponent, _pcbThickness, _errMessage
            _containerComponent = inputs.addSelectionInput('containerComponent', 'Insert into', 
                                                           'select component that pcb parts are inserted into')
            _containerComponent.clearSelectionFilter()
            _containerComponent.addSelectionFilter('Occurrences')
            _containerComponent.setSelectionLimits(1)
            _placeFileButton = inputs.addBoolValueInput('placeFileButton', 'Place-info file', False)
            _placeFileButton.text = 'Select a File...'
            _componentsFolder = inputs.addStringValueInput('componentsFolder', 'Components Folder')
            folderAttrib = des.attributes.itemByName(CMDID, _componentsFolder.id)
            if folderAttrib:
                _componentsFolder.value = folderAttrib.value
            lengthValue = adsk.core.ValueInput.createByString('0' + defaultUnits)
            _pcbThickness = inputs.addValueInput('pcbThickness', 'PCB Thickness', defaultUnits, lengthValue)
            _errMessage = inputs.addTextBoxCommandInput('errMessage', '', '', 4, True)
            _errMessage.isFullWidth = True

            # Connect to the command related events.
            onExecute = PMCommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)        
            
            onInputChanged = PMCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)     
            
            onValidateInputs = PMCommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class PMCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global _app, _ui
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            global _componentsFolder, _pcbThickness, _verifiedFolder
            des = adsk.fusion.Design.cast(_app.activeProduct)
            attribs = des.attributes
            attribs.add(CMDID, _componentsFolder.id, _componentsFolder.value)
            
            thickness = getCommandInputValue(_pcbThickness, 'cm')[1]
            placeComponents(_placeFile, _verifiedFolder, thickness)

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class PMCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global _app, _ui
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            cmd = eventArgs.inputs.command
            changedInput = eventArgs.input

            global _placeFileButton, _placeFile, _containerComponent, _selectedComponent
            if changedInput.id == _placeFileButton.id:
                fileDialog = _ui.createFileDialog()
                fileDialog.isMultiSelectEnabled = False
                fileDialog.title = "Select Place-info file"
                fileDialog.filter = 'Place-info file (*.plinfo)'
                fileDialog.filterIndex = 0
                if _placeFile is not None and len(_placeFile) > 0:
                    fileDialog.initialDirectory = os.path.dirname(_placeFile)
                    fileDialog.initialFilename = os.path.basename(_placeFile)
                dialogResult = fileDialog.showOpen()
                if dialogResult == adsk.core.DialogResults.DialogOK:
                    _placeFile = fileDialog.filename
                    _placeFileButton.text = os.path.basename(_placeFile)
            elif changedInput.id == _containerComponent.id:
                if _containerComponent.selectionCount == 0:
                    _selectedComponent = None
                else:
                    entity = _containerComponent.selection(0).entity
                    if entity.classType() == 'adsk::fusion::Occurrence':
                        _selectedComponent = entity.component
                    else:
                        _selectedComponent = None

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class PMCommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            global _app, _ui
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)

            global _placeFile
            global _componentsFolder, _pcbThickness, _errMessage
            container = _componentsFolder.value
            thickness = getCommandInputValue(_pcbThickness, 'cm')[1]

            _placeFileButton = None
            _errMessage.text = ''
            eventArgs.areInputsValid = False

            if _placeFile is None or len(_placeFile) == 0:
                _errMessage.text = 'Please select Place-info files'
            elif thickness <= 0:
                _errMessage.text = 'PCB thickness must be positive number grater than 0.'
            else:
                _errMessage.text = 'Container Component must be path string ' \
                                   'which indicate valid folder in active project, '\
                                   'such as "folder-a/folder-b".'
                folders = list(filter(lambda i: i != '', container.split('/')))
                if len(folders) > 0:
                    global _verifiedFolderPath, _verifiedFolder
                    if _verifiedFolderPath == container:
                        if _verifiedFolder is not None:
                            _errMessage.text = ''
                        eventArgs.areInputsValid = _verifiedFolder is not None
                        return
                    _verifiedFolderPath = container
                    _verifiedFolder = None
                    data = _app.data
                    project = data.activeProject
                    cfolder = project.rootFolder
                    for folderName in folders:
                        if folderName == '':
                            continue
                        try:
                            cfolder = cfolder.dataFolders.itemByName(folderName)
                        except:
                            # it may be in offline state
                            cfolder = None
                        if not cfolder:
                            _verifiedFolder = None
                            return
                    _verifiedFolder = cfolder
                    _errMessage.text = ''
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

def placeComponents(file, folder, thickness):
    folderName = folder.name
    data = placeinfo.load(file)
    
    partsNum = 0
    for key in data:
        partsNum += len(data[key])

    replaces = {}
    repfile_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                                '../Resources/replace.json')
    if os.path.isfile(repfile_path):
        with open(repfile_path, 'r', encoding='utf-8') as f:
            defs = json.load(f)
            replaces = {}
            for key in defs:
                val = defs[key]
                if val in replaces:
                    replaces[val].append(key)
                else:
                    replaces[val] = [key]

    progressDialog = _ui.createProgressDialog()
    progressDialog.cancelButtonText = 'Cancel'
    progressDialog.isBackgroundTranslucent = False
    progressDialog.isCancelButtonShown = True
    progressDialog.show(
        'Progress to place PCB components', 
        '################################################',
        0, partsNum, 0)
    adsk.doEvents()
    progressDialog.message = 'initializing...'

    components = folder.dataFiles
    componentsNum = components.count
    des = adsk.fusion.Design.cast(_app.activeProduct)
    global _selectedComponent
    if _selectedComponent:
        container = _selectedComponent
    else:
        container = des.rootComponent
    msg = '{0} : %p % done (%v/%m)'
    finished = []

    for index in range(0, componentsNum):
        progressDialog.message = msg.format(
            'Browsing folder "{0}" ({1}/{2})...'.format(folderName, index + 1, componentsNum))
        adsk.doEvents()
        dataFile = components.item(index)
        adsk.doEvents()
        if progressDialog.wasCancelled:
            break
        pname = dataFile.name
        if pname in replaces:
            rnames = replaces[pname]
            if not pname in rnames:
                rnames.append(pname)
        else:
            rnames = [pname]

        for name in rnames:
            if name in data:
                progressDialog.message = msg.format(
                    'Placing [{0}]...'.format(name))
                adsk.doEvents()
                loadComponent(container, dataFile, thickness, data[name], progressDialog, msg)
                finished.append(name)
        if progressDialog.progressValue == partsNum:
            break

    progressDialog.hide()

    if progressDialog.progressValue < partsNum and not progressDialog.wasCancelled:
        unfinished = filter(lambda key: not key in finished, data)
        _ui.messageBox('Following parts are not found in your project:\n\n    ' + \
                       '\n    '.join(unfinished))

def loadComponent(container, dataFile, thickness, infos, progress, msg):
    matrix = adsk.core.Matrix3D.create()
    partsName = dataFile.name
    for info in infos:
        x, y, rot, isTop, name = info
        angle = rot / 180 * pi

        progress.message = msg.format(
            'Placing [{0} : {1}]...'.format(name, partsName))
        adsk.doEvents()
        if progress.wasCancelled:
            return

        if isTop:
            matrix.setToAlignCoordinateSystems(
                adsk.core.Point3D.create(0, 0, 0),
                adsk.core.Vector3D.create(1, 0, 0),
                adsk.core.Vector3D.create(0, 1, 0),
                adsk.core.Vector3D.create(0, 0, 1),
                adsk.core.Point3D.create(x / 10, y / 10, thickness),
                adsk.core.Vector3D.create(cos(angle), sin(angle), 0),
                adsk.core.Vector3D.create(cos(angle + pi / 2), sin(angle + pi /2), 0),
                adsk.core.Vector3D.create(0, 0, 1),
            )
        else:
            angle = -angle
            matrix.setToAlignCoordinateSystems(
                adsk.core.Point3D.create(0, 0, 0),
                adsk.core.Vector3D.create(1, 0, 0),
                adsk.core.Vector3D.create(0, 1, 0),
                adsk.core.Vector3D.create(0, 0, 1),
                adsk.core.Point3D.create(x / 10, y / 10, 0),
                adsk.core.Vector3D.create(cos(-angle), sin(-angle), 0),
                adsk.core.Vector3D.create(cos(-(angle + pi / 2)), sin(-(angle + pi /2)), 0),
                adsk.core.Vector3D.create(0, 0, -1),
            )

        occ = container.occurrences.addByInsert(dataFile, matrix, True)
        progress.progressValue += 1
