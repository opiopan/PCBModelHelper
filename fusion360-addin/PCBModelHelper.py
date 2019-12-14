#Author-Hioroshi Murayama
#Description-This add-in helps to create a 3D model from Eagle design in order to photo-real-renering.

import adsk.core, adsk.fusion, adsk.cam, traceback, os, sys, importlib

appearance = None
mounter = None

_appearanceCmd = None
_mounterCmd = None

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        sys.path.append(os.path.dirname(os.path.realpath(__file__)))
        global appearance, mounter
        appearance = importlib.import_module("pcblib.appearance")
        appearance = importlib.reload(appearance)
        mounter = importlib.import_module("pcblib.mounter")
        mounter = importlib.reload(mounter)

        global _appearanceCmd, _mounterCmd
        _appearanceCmd = appearance.registerCommand(app, ui)
        _mounterCmd = mounter.registerCommand(app, ui)

        panel = ui.allToolbarPanels.itemById('UtilityPanel')
        panel.controls.addCommand(_appearanceCmd)
        panel.controls.addCommand(_mounterCmd)

        for pid in ['SolidModifyPanel', 'SheetMetalModifyPanel',
                    'SurfaceModifyPanel', 'RenderSetupPanel']:
            panel = ui.allToolbarPanels.itemById(pid)
            panel.controls.addCommand(_appearanceCmd, 'AppearanceCommand', False)

        for pid in ['InsertPanel']:
            panel = ui.allToolbarPanels.itemById(pid)
            panel.controls.addCommand(_mounterCmd)


    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        for pid in ['UtilityPanel', 'SolidModifyPanel', 'SheetMetalModifyPanel',
                    'SurfaceModifyPanel', 'RenderSetupPanel', 'InsertPanel']:
            panel = ui.allToolbarPanels.itemById(pid)
            for cmd in  [_appearanceCmd, _mounterCmd]:
                if cmd:
                    ctrl = panel.controls.itemById(cmd.id)
                    if ctrl:
                        ctrl.deleteMe()

        if appearance:
            appearance.unregisterCommand(app, ui)
        if mounter:
            mounter.unregisterCommand(app, ui)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
