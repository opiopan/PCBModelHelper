#Author-Hioroshi Murayama
#Description-This add-in helps to create a 3D model from Eagle design in order to photo-real-renering.

import adsk.core, adsk.fusion, adsk.cam, traceback, os, sys, importlib

appearance = None
mounter = None

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

        panel = ui.allToolbarPanels.itemById('UtilityPanel')
        cmd = appearance.registerCommand(app, ui, panel)
        cmd = mounter.registerCommand(app, ui, panel)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        panel = ui.allToolbarPanels.itemById('UtilityPanel')
        if appearance:
            appearance.unregisterCommand(app, ui, panel)
        if mounter:
            mounter.unregisterCommand(app, ui, panel)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
