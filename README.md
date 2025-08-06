# GUI_StretchableElectronics_BU

# Trace Maker GUI (Python 2.7)

This is a graphical interface for drawing and editing circuit traces by placing components and routing connections between them. Originally developed as a function-based script, this version has been refactored into an interactive GUI built with Tkinter. It is designed for prototyping soft and stretchable electronics, and was developed as part of a research project on rapid fabrication of haptic devices.

This tool is part of a research study submitted to **Science Robotics**, exploring novel fabrication strategies for wearable haptic systems.

---

## Features

* Click-based trace drawing
* Manual component placement via dropdown
* Component rotation and tagging
* Tunnel (via) mode for multi-layer routing
* Save and load designs using structured CSV files
* Supports real-time prototyping workflows

---

## Requirements

* Python 2.7
* Tkinter
* pandas
* numpy
* PIL (Pillow)

---

## How to Use

## Create a New Design

1. Run the script.
2. In the GUI, type a name in the textbox and press Enter to create a new design folder.
3. Select components from the dropdown and click anywhere on the canvas to place them.
4. Draw traces by clicking on connection points or empty canvas space.
5. Click **Save** (or right-click) to store the current trace in the design folder.

## Load an Existing Design

1. Click the **Load Design** button.
2. Navigate to the folder of a previously saved design.
3. Select the folder — **do not click a file**, just select the folder and confirm.
4. The design will be redrawn with all its components and traces.

Two example designs are included:

* `Haptic_Input_Device`
* `Haptic_Output_Device`

These can be used to test the loading feature or to explore how designs are structured.

---

## Setting Device Dimensions

If you're working with a custom substrate size, you can modify the workspace boundary by editing two variables in the code:

In the `__init__` method of `TraceMakerApp`, update the following:

```python
self.x_border = <width in mm> * self.scaling_factor + self.origin_x  
self.y_border = <height in mm> * self.scaling_factor + self.origin_y
```

This sets the width and height of your drawing canvas in millimeters (scaled by a factor of 5 by default).

---

## File Structure

When you create or save a design, a folder will be generated with:

* `Traces_Coordinates_<name>.csv`: stores all drawn traces
* `PP_List_Coordinates_<name>.csv`: stores placed component info
* `Pins_Coordinates_<name>.csv`: stores selected pin connections
* `Base_Coordinates_<name>.csv`: stores device boundaries

These can be opened in any spreadsheet editor or loaded back into the GUI.

---

## Author

**Ramon Sanchez**
Ph.D. in Mechanical Engineering
Specialized in stretchable electronics, haptic devices, and hybrid manufacturing
Boston University 

---

## License

This project is licensed under the MIT License.  
You are free to use, modify, and distribute it, including for commercial and academic purposes.  

Copyright (c) 2025 Ramon Sanchez

