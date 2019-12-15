PCBModelHelper
===
PCBModelHelper is tool suite in order to help building [Fusion 360](https://www.autodesk.com/products/fusion-360/overview) 3D model of PCB designed by [Eagle](https://www.autodesk.com/products/eagle/overview).

Eagle can manage 3D model for each device in component library and provides a function to export Fusion 360 3D model from board design.
This fucntion is useful to proceed collaborative work between electrical design and mechanical design.<br>
And Fusion 360 provides photo realistic 3D CG renderer also. This rendering quority is very high enough to use product catolog.

However, in case reding 3D model exported by Eagle, the result is quite dissappoointing finish as below example.<br>
Since PCB board surface structure is expressed only one decal image, it's texture is flat and matte. We cannot feel metallic luster of pads or  unevenness of circuit pattern from that image.
in addition, there are many artifact pattern on the board surface, I don't know the reason why.<br>
And further more, all components on the board are also matt texture, because 3D model managed in Eagle library is imported as STEP formated data. Even if original 3D model made by Fusion 360 includes specific apearance metadata, such as albedo and/or heigt map, all metadata except color will be dropped when translating to STEP format.<br>
As a result, rendered image looks like a clay work.

PCBModelHelper helps to make a 3D model which can be photo real rendered by Fusion 360. That model has a realistic appearance and original components 3d models that has complete appearance data are placed on the board.

Please compare between detail of following two examples after click to expand images

<p align="center">
<img alt="example of Eagle" src="https://raw.githubusercontent.com/wiki/opiopan/PCBModelHelper/images/case-eagle.jpg" width=49%>
<img alt="example of PCBModelHelper" src="https://raw.githubusercontent.com/wiki/opiopan/PCBModelHelper/images/case-thistool.jpg" width=49%>
</p>

## Installation
This tool suite include an Eagle ULP scripts and a Fusion 360 Add-on. Eagle ULP script can be run by just specify file path. On the other hand, Fusion 360 Add-on is need to register to Fusion 360 itself.<br>

1. **Clone this git repository**<br>
    ``` shell
    $ git clone https://github.com/opiopan/PCBModelHelper
    ```

2. **Register Add-on program to Fusion 360**<br>
    Enter to Fusion360 Design mode, then execute ```Scripts and Add-ins``` command in ```Add-ins``` panel on ```TOOLS``` tab.

    <p align="center">
    <img alt="step2-1 of installation" src="https://raw.githubusercontent.com/wiki/opiopan/PCBModelHelper/images/install01.jpg" width=400> 
    </p>

    Move to ```Add-ins``` tab in the ```Script and Add-ins``` Dialog.<br>
    After that, push the plus button beside of ```My Add-ins``` label.

    <p align="center">
    <img alt="step2-2 of installation" src="https://raw.githubusercontent.com/wiki/opiopan/PCBModelHelper/images/install02.jpg" width=300>
    </p>

    Folder selecting dialog is shown. Specify ```fusion360-addin``` folder under the root folder of git repository you cloned at step 1.

    <p align="center">
    <img alt="step2-3 of installation" src="https://raw.githubusercontent.com/wiki/opiopan/PCBModelHelper/images/install03.jpg" width=700>
    </p>

    New add-in named ```PCBModelHelper``` is added in ```My Add-ins```. Select this new add-in, then confirm that ```Run on Startup``` is checked. After that, Press  ```Run``` button.

    <p align="center">
    <img alt="step2-4 of installation" src="https://raw.githubusercontent.com/wiki/opiopan/PCBModelHelper/images/install04.jpg" width=300>
    </p>

## How to make a PCB 3D model
Sorry, Now preparing