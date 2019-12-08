#Author-Hioroshi Murayama
#Description-This add-in helps to create a 3D model from Eagle design due to photo-real-renering.

import adsk.core, adsk.fusion, adsk.cam, traceback, os, sys, importlib

_appearance = None

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        sys.path.append(os.path.dirname(os.path.realpath(__file__)))
        from pcblib import appearance
        importlib.reload(appearance)
        global _appearance
        _appearance = appearance

        #with open('/Users/opiopan/Downloads/panels.txt', 'w', encoding='utf-8') as f:
        #    for panel in ui.allToolbarPanels:
        #        f.write('{0} : {1}\n'.format(panel.id, panel.name))

        panel = ui.allToolbarPanels.itemById('UtilityPanel')
        cmd = _appearance.registerCommand(app, ui, panel)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        panel = ui.allToolbarPanels.itemById('UtilityPanel')
        if _appearance:
            _appearance.unregisterCommand(app, ui, panel)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
