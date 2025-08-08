# Author: Ramon Sanchez
# Last Updated: August 2025
#
# This code is a modified version of the original Trace Maker, which was function-based.
# It provides a Tkinter-based GUI for designing circuit traces by manually placing components
# and drawing connections between them.
#
# Key Features:
# - Interactive drawing of circuit traces and component placement
# - Component rotation, deletion, and tagging
# - Tunnel (via) support for multi-layer routing
# - Organized saving and loading of design files
#
# This version focuses on direct interaction and usability, without animation or scripted replay.
# It is ideal for prototyping soft electronics, stretchable circuits, and educational circuit design.

import os
import Tkinter as tk
from Tkinter import *
import tkFileDialog
import ttk
import csv
import pandas as pd
import numpy as np
import math
from time import sleep
from PIL import Image, ImageTk



class TraceMakerApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1900x1000")
        self.root.title("Trace Maker GUI")
        self.scaling_factor = 5  # Scaling factor for the GUI elements to be visible

        # Define the device dimensions
        self.origin_x = 2 # These set a margin for the workspace line to be visible in the interface
        self.origin_y = 2
        self.x_border = 35 * self.scaling_factor + self.origin_x
        self.y_border = 50 * self.scaling_factor + self.origin_y

        # State variables
        self.last_cursor_x = 950  # or your initial cursor tip x
        self.last_cursor_y = 400  # or your initial cursor tip y
        self.background = 'white'
        self.coord_x = []
        self.coord_y = []
        self.x_pin_points = []
        self.y_pin_points = []
        self.component_here = []  # Wherever x_pin_points and y_pin_points are defined, we also add to this vector the component to where the pins correspond to at a given instance
        self.component_tag_here = []  # Wherever x_pin_points and y_pin_points are defined, we also add to this vector the component tag
        self.here = 0
        self.here_comp = 0
        self.comp_selected = 0
        self.tunnel = 0
        self.delete_here = 0
        self.degree = 0
        self.old_comp = 0
        self.pin_instances = 0
        self.same_line = 0
        self.line_tag = 0
        self.load = 0
        self.tag_line_vector = []
        self.tag_comp_vector = [] 
        self.counter = 0

        # File paths
        self.filename = None
        self.filename_pp = 'Pick_and_place_components_with_pads.csv'
        self.filename_pp_coord = None
        self.filename_base = None
        self.filename_pins_selected = None

        # Canvas and UI elements
        self.canvas = tk.Canvas(self.root, width=1900, height=800, bg=self.background)
        self.canvas.pack()
        self.canvas.old_coords = None

        # UI setup
        self.create_ui()

        # Event bindings
        self.root.bind('<ButtonPress-1>', self.draw_line)
        self.root.bind('<ButtonPress-3>', self.save)

    def create_ui(self):
        """Create the UI elements."""

        tk.Button(self.root, text="Save", width=20, height=1, command=self.save).place(x=1100, y=5)
        self.button_via = tk.Button(self.root, text="Tunnel", width=20, height=1, fg="black", command=self.via_tunnel)
        self.button_via.place(x=1100, y=35)
        self.orig_color = self.button_via.cget("background")

        self.button_rotate = tk.Button(self.root, text="Rotate", width=20, height=1, fg="black", command=self.rotate)
        self.button_rotate.place(x=1100, y=65)

        tk.Label(self.root, text="Select component:", background="RoyalBlue2", foreground="black").place(x=1100, y=95)
        self.combo = ttk.Combobox(
            self.root,
            state="readonly",
            values=[
                "FSR", "AM3208", "ATiny85", "Transistor", "Diode", "LED", "Ferrite", "DRV2603", "ADC(16bit)", "ERM",
                "Switch", "BLE", "LMP7701", "MAX4617", "BQ2404", "C0603", "USB", "Battery", "Via", "Pad", "Wire",
                "0.9V", "1.0V", "1.7V", "3.3V", "MCP73831", "CR2450X1", "CR2450X2", "R33", "R330", "R2k", "R10k",
                "R20k", "C0.1uF", "C1uF", "C10uF", "FSR Place"
            ],
            width=20
        )
        self.combo.place(x=1100, y=120)
        self.combo.bind('<<ComboboxSelected>>', self.combo_callback)

        tk.Button(self.root, text="Delete", width=20, height=1, command=self.delete).place(x=1100, y=150)
        tk.Button(self.root, text="Load Design", width=20, height=1, command=self.load_design).place(x=1100, y=180)

        self.entry = tk.Entry(self.root, text="Name Design", width=20)
        self.entry.place(x=1100, y=220)
        self.entry.insert(0, "Enter design name")
        self.entry.bind("<FocusIn>", self.temp_text)
        self.entry.bind("<Return>", self.entry_callback)
        self.create_grid()
        self.canvas.create_rectangle(1075, 0, 1275, 250, fill="RoyalBlue2")

    def create_grid(self):
        """Draw the grid dots on the canvas."""
        x_pixels = 1900
        y_pixels = 1000
        grid_spacing = 10
        for pixels_x in range(1, x_pixels, grid_spacing):
            for pixels_y in range(1, y_pixels, grid_spacing):
                self.canvas.create_oval(pixels_x, pixels_y, pixels_x, pixels_y, fill="#c6c6c6", width=0)

    def temp_text(self, event):
        """Clear the entry field when focused."""
        self.entry.delete(0, "end")

    def draw_line(self,  event=None, x=None, y=None): # Added x and y so it can handle the movie loading events
        #print('Aqui estamos, load es :', self.load)
        """Draw a line between two consecutive points or place a component."""
        #print('X and Y coordinates:', self.x, self.y)
        if event is not None:
            self.x = event.x
            self.y = event.y
        elif x is not None and y is not None:
            self.x = x
            self.y = y
        elif self.x is None or self.y is None:
            # Fallback to last known cursor position
            self.x = self.last_cursor_x
            self.y = self.last_cursor_y

        x_lim = 1075  # [Pixels] this is where the box with buttons is located in the GUI
        y_lim = 200  # [Pixels] this is where the box with buttons is located in the GUI
        
        if self.load == 1:
            #print("Degree non convert:", self.degree)
            self.degree = (self.degree / 180.0) * math.pi
            #print("Degree converted:", self.degree)
        self.degree_here = self.degree * (180.0 / math.pi)

        if self.load == 0:
            self.component_selected = self.combo.get()

        if self.degree != 0 and self.comp_selected == 1 and self.component_selected != "FSR Place":
            if self.load == 0:
                self.x, self.y = self.x_center, self.y_center
        else:
            if self.load == 0 and event is not None:
                self.x, self.y = event.x, event.y

        if self.component_selected == "FSR Place" and self.comp_selected == 1:
            self.x, self.y = event.x, event.y
            self.FSR_placement(self.x, self.y, self.scaling_factor)
            self.old_comp = self.component_selected
            self.comp_selected = 0
            self.canvas.create_text(
                self.x,
                self.y - self.scaling_factor * 2,
                fill="black",
                font=("Helvetic 6 bold"),
                text=self.component_selected,
                tags=(self.tag_name),
            )
        color_line = "gray50"

        if self.comp_selected == 0:
            if self.load == 1:
                self.x = self.x1
                self.y = self.y1

            dist_point_to_pins = []
            if len(self.x_pin_points) > 0:
                for i in range(len(self.x_pin_points)):
                    dist_point_to_pins.append(
                        math.sqrt((self.x_pin_points[i] - self.x) ** 2 + (self.y_pin_points[i] - self.y) ** 2)
                    )

                if min(dist_point_to_pins) < 3.0:
                    minpos = dist_point_to_pins.index(min(dist_point_to_pins))
                    if self.load == 0:
                        self.x = self.x_pin_points[minpos]
                        self.y = self.y_pin_points[minpos]

                    corresponding_component = self.component_here[minpos]
                    corresponding_tag = self.component_tag_here[minpos]

                    if self.pin_instances == 0:
                        a = "w"
                    else:
                        a = "a"

                    with open(self.filename_pins_selected, a) as f:
                        writer = csv.writer(f)
                        data = [self.x, self.y, corresponding_component, corresponding_tag]
                        if a == "w":
                            first_row = ["X", "Y", "Component", "Tag"]
                            writer.writerow(first_row)
                        writer.writerow(data)

                    self.pin_instances += 1

            self.coord_x.append(self.x)
            self.coord_y.append(self.y)

            if self.canvas.old_coords and self.load == 0:
                self.x1, self.y1 = self.canvas.old_coords
                if self.same_line == 0:
                    self.line_tag += 1
                    self.same_line = 1
                self.tag_line = "line_{}".format(self.line_tag)
                while self.tag_line in self.tag_line_vector:
                    self.line_tag += 1
                    self.tag_line = "line_{}".format(self.line_tag)
                if self.tunnel == 1:
                    color_line = "#008080"
                    self.line = self.canvas.create_line(
                        self.x, self.y, self.x1, self.y1, dash=(2, 1), fill=color_line, tags=(self.tag_line)
                    )
                else:
                    self.line = self.canvas.create_line(
                        self.x, self.y, self.x1, self.y1, width=1, fill=color_line, tags=(self.tag_line)
                    )
            self.canvas.old_coords = self.x, self.y

        elif self.comp_selected == 1 and self.component_selected != "FSR Place":
            # Check how many times a component is used, and assign a tag depending on how many there are
            df_pp_comps = pd.read_csv(self.filename_pp_coord)
            comp_list = df_pp_comps.iloc[:][:]
            repeated = 0
            for i in range(len(comp_list)):
                if (
                    df_pp_comps.iloc[i][0] == self.component_selected
                    and df_pp_comps.iloc[i][3] == self.degree_here
                ):
                    repeated += 1
            if self.load == 0:
                self.tag_name = "{}_{}_{}".format(self.component_selected, repeated, self.degree_here)
                if self.tag_name in self.tag_comp_vector:
                    while self.tag_name in self.tag_comp_vector:
                        repeated += 1
                        self.tag_name = "{}_{}_{}".format(self.component_selected, repeated, self.degree_here)
                    self.tag_comp_vector.append(self.tag_name)
                else:
                    self.tag_comp_vector.append(self.tag_name)
            else:
                self.tag_name = self.tag_comp
                

            if self.degree != 0 and self.component_selected == self.old_comp:
                if self.load == 0:
                    self.x1 = self.x_center
                    self.y1 = self.y_center
                    self.x2 = self.x_center
                    self.y2 = self.y_center
                else:
                    self.x1 = self.x
                    self.y1 = self.y
                    self.x2 = self.x
                    self.y2 = self.y
            else:
                if self.load == 0:
                    self.x1 = event.x
                    self.y1 = event.y
                    self.x2 = event.x
                    self.y2 = event.y
                else:
                    self.x1 = self.x
                    self.y1 = self.y
                    self.x2 = self.x
                    self.y2 = self.y

            color = "blue"
            w = 0.25

            if self.here_comp == 0:
                a = "w"
            else:
                a = "a"

            theta = self.degree
            self.x_center = self.x1
            self.y_center = self.y1
            num_points = 20
            (
                self.pins_x_coordinate,
                self.pins_y_coordinate,
                self.x_top,
                self.y_top,
                self.x_bottom,
                self.y_bottom,
                self.x_right,
                self.y_right,
                self.x_left,
                self.y_left,
            ) = self.tracer_coordinates(
                self.filename_pp,
                self.x_center,
                self.y_center,
                num_points,
                self.component_selected,
                theta,
            )
            x_perimeter = [
                np.round_(self.x_top[0], decimals=2),
                np.round_(self.x_top[-1], decimals=2),
                np.round_(self.x_bottom[-1], decimals=2),
                np.round_(self.x_bottom[0], decimals=2),
            ]
            y_perimeter = [
                np.round_(self.y_top[0], decimals=2),
                np.round_(self.y_top[-1], decimals=2),
                np.round_(self.y_bottom[-1], decimals=2),
                np.round_(self.y_bottom[0], decimals=2),
            ]

            # Save location of component in CSV file
            if self.component_selected != self.old_comp and self.load == 0:
                with open(self.filename_pp_coord, a) as f:
                    writer = csv.writer(f)
                    data = [
                        self.component_selected,
                        self.x1,
                        self.y1,
                        int(self.degree_here),
                        x_perimeter,
                        y_perimeter,
                        self.tag_name,
                    ]
                    if a == "w":
                        first_row = [
                            "Component",
                            "X",
                            "Y",
                            "Orientation",
                            "Perimeter X",
                            "Perimeter Y",
                            "Tag",
                        ]
                        writer.writerow(first_row)
                    writer.writerow(data)
            elif self.component_selected == self.old_comp and self.degree == 0 and self.load == 0:
                with open(self.filename_pp_coord, a) as f:
                    writer = csv.writer(f)
                    data = [
                        self.component_selected,
                        self.x1,
                        self.y1,
                        int(self.degree_here),
                        x_perimeter,
                        y_perimeter,
                        self.tag_name,
                    ]
                    if a == "w":
                        first_row = [
                            "Component",
                            "X",
                            "Y",
                            "Orientation",
                            "Perimeter X",
                            "Perimeter Y",
                            "Tag",
                        ]
                        writer.writerow(first_row)
                    writer.writerow(data)

            self.coord_x = []
            self.coord_y = []
            self.here_comp = 1

            # Draw an oval in the given coordinates
            if self.component_selected == "Via":
                color = "green"
                w = 3
                self.canvas.create_oval(
                    self.x1, self.y1, self.x2, self.y2, fill=color, width=w, tags=self.tag_name
                )

            # Draw the component as an obstacle, and the component pins so they're accessible
            x_vector = []
            y_vector = []
            x_vector.extend(self.pins_x_coordinate)
            x_vector.extend(self.x_top)
            x_vector.extend(self.x_bottom)
            x_vector.extend(self.x_right)
            x_vector.extend(self.x_left)
            y_vector.extend(self.pins_y_coordinate)
            y_vector.extend(self.y_top)
            y_vector.extend(self.y_bottom)
            y_vector.extend(self.y_right)
            y_vector.extend(self.y_left)
            x_vector = np.round_(x_vector, decimals=2)
            y_vector = np.round_(y_vector, decimals=2)
            self.x_pin_points.extend(self.pins_x_coordinate)
            self.y_pin_points.extend(self.pins_y_coordinate)
            for pin_lengths_here in range(len(self.pins_x_coordinate)):
                self.component_here.extend([self.component_selected])
                self.component_tag_here.extend([self.tag_name])

            if self.component_selected == "FSR":
                df = pd.read_csv(self.filename_pp)
                for components in range(0, len(df.iloc[:][:])):
                    if df.iloc[components][0] == "FSR":
                        self.canvas.create_oval(
                            self.x_right[0],
                            self.y_top[0],
                            self.x_left[0],
                            self.y_bottom[0],
                            fill="gray",
                            width=1,
                            tags=(self.tag_name),
                        )
                        self.canvas.create_oval(
                            self.pins_x_coordinate[0],
                            self.pins_y_coordinate[0],
                            self.pins_x_coordinate[0],
                            y_vector[0],
                            fill="black",
                            width=2,
                            tags=(self.tag_name),
                        )
                        self.canvas.create_oval(
                            self.pins_x_coordinate[1],
                            self.pins_y_coordinate[1],
                            self.pins_x_coordinate[1],
                            y_vector[1],
                            fill="black",
                            width=2,
                            tags=(self.tag_name),
                        )
            else:
                for i in range(0, len(x_vector)):
                    self.canvas.create_oval(
                        x_vector[i],
                        y_vector[i],
                        x_vector[i],
                        y_vector[i],
                        fill="black",
                        width=1,
                        tags=(self.tag_name),
                    )
            self.canvas.create_text(self.x, self.y-self.scaling_factor*2, fill="black", font=('Helvetic 5 bold'),text=self.component_selected, tags=(self.tag_name)) #black text above the component
            self.old_comp = self.component_selected
            self.comp_selected = 0

    #def end_line(self, event):
        """End the current trace."""
        #self.canvas.old_coords = None
        #print("End of trace")

    def save(self, event=None):
        """End the trace and then Save the trace coordinates to a CSV file."""
        self.canvas.old_coords = None
        print(self.coord_x)
        print(self.coord_y)

        if self.here == 0:
            mode = "w"
        else:
            mode = "a"

        with open(self.filename, mode) as f:
            writer = csv.writer(f)
            # Write the data
            #data = [self.tunnel, self.coord_x[:-1], self.coord_y[:-1], self.tag_line]
            data = [self.tunnel, self.coord_x, self.coord_y, self.tag_line]
            print(data)
            if mode == "w":
                first_row = ["Tunnel", "X", "Y", "Tag"]
                writer.writerow(first_row)
            writer.writerow(data)

        # Reset state variables
        self.coord_x = []
        self.coord_y = []
        self.here = 1
        self.same_line = 0

    def via_tunnel(self):
        """Toggle the tunnel mode."""
        self.canvas.old_coords = None
        self.coord_x = self.coord_x[:-1]
        self.coord_y = self.coord_y[:-1]

        if self.tunnel == 0:
            self.button_via.configure(bg="#bf9000", fg="white")
            self.tunnel = 1
        else:
            self.button_via.configure(bg=self.orig_color, fg="black")
            self.tunnel = 0

    def rotate(self, event=None):
        """Rotate the selected component."""
        self.comp_selected = 1
        self.component_selected = self.combo.get()

        if self.degree == 0:
            self.degree = math.pi / 2
        elif self.degree != 0 and self.component_selected == self.old_comp_selected:
            self.degree += math.pi / 2
        elif self.degree != 0 and self.component_selected != self.old_comp_selected:
            self.degree = math.pi / 2

        # Adjust component and pin lists
        self.component_here = self.component_here[: len(self.x_pin_points) - len(self.pins_x_coordinate)]
        self.x_pin_points = self.x_pin_points[: len(self.x_pin_points) - len(self.pins_x_coordinate)]
        self.y_pin_points = self.y_pin_points[: len(self.y_pin_points) - len(self.pins_x_coordinate)]

        self.canvas.old_coords = None
        self.coord_x = self.coord_x[:-1]
        self.coord_y = self.coord_y[:-1]

        # Delete the current component from the canvas
        self.canvas.delete(self.tag_name)

        # Redraw the component with the new rotation
        self.x = self.x_center
        self.y = self.y_center

        if self.load == 0:
            self.draw_line(event)
        else:
            self.degree = 90
            self.draw_line(None)
        self.old_comp_selected = self.component_selected
        if self.filename_pp_coord is not None:
            try:
                df = pd.read_csv(self.filename_pp_coord)
                tolerance = 1e-2
                row_idx = df[
                    (df['Component'].str.strip() == self.component_selected.strip()) &
                    (np.isclose(df['X'], self.x_center, atol=tolerance)) &
                    (np.isclose(df['Y'], self.y_center, atol=tolerance))
                ].index

                if not row_idx.empty:
                    new_angle = int(self.degree * 180 / math.pi)
                    df.loc[row_idx, 'Orientation'] = new_angle
                    df.to_csv(self.filename_pp_coord, index=False)
                else:
                    print("Could not find matching row to update orientation.")
            except Exception as e:
                print("Error updating CSV orientation:", e)

    def combo_callback(self, event):
        """Handle the selection of a component from the dropdown menu."""
        self.comp_selected = 1
        self.degree = 0
        self.canvas.old_coords = None
        current_value = self.combo.get()
        #print("Selected:", current_value)

    def delete(self, event=None):
        """Delete lines or components."""
        self.canvas.old_coords = None
        self.coord_x = self.coord_x[:-1]
        self.coord_y = self.coord_y[:-1]
        self.x1 = self.coord_x[-1]
        self.y1 = self.coord_y[-1]

        # Check for components near the selected point
        df_pp_comps = pd.read_csv(self.filename_pp_coord)
        comp_list = df_pp_comps.iloc[:][:]
        dist_point_to_component = []
        tag_name_here = None

        for i in range(len(comp_list)):
            x_comp_points = df_pp_comps.iloc[i][1]
            y_comp_points = df_pp_comps.iloc[i][2]
            dist_point_to_component.append(math.sqrt((x_comp_points - self.x1) ** 2 + (y_comp_points - self.y1) ** 2))
            if min(dist_point_to_component) < 10.0:
                minpos = dist_point_to_component.index(min(dist_point_to_component))
                component_delete = df_pp_comps.iloc[i][0]
                tag_name_here = df_pp_comps.iloc[i][6]

                # Remove component from the CSV file
                df_pp_comps = df_pp_comps.drop(df_pp_comps.index[i])
                df_pp_comps.to_csv(self.filename_pp_coord, index=False)

                # Remove pins related to the deleted component
                df_pp_pins = pd.read_csv(self.filename_pins_selected)
                pins_list = df_pp_pins.iloc[:][:]
                pins_match = []
                for pins in range(len(pins_list)):
                    if df_pp_pins.iloc[pins][3] == tag_name_here:
                        pins_match.append(pins)

                if len(pins_match) != 0:
                    df_pp_pins = df_pp_pins.drop(df_pp_pins.index[pins_match])
                    df_pp_pins.to_csv(self.filename_pins_selected, index=False)
                break

        # If no components are near, check for traces
        if tag_name_here is None:
            df_traces = pd.read_csv(self.filename)
            traces_list = df_traces.iloc[:][:]
            dist_point_to_traces = []
            line_points = 40
            found = 0

            for traces in range(len(traces_list)):
                x = np.fromstring(str(df_traces.iloc[traces][1])[1:-1], sep=",")
                y = np.fromstring(str(df_traces.iloc[traces][2])[1:-1], sep=",")
                for segments in range(len(x) - 1):
                    line_length = math.sqrt((x[segments + 1] - x[segments]) ** 2 + (y[segments + 1] - y[segments]) ** 2)
                    angle_seg = self.calculate_angle(x[segments],y[segments],x[segments+ 1],y[segments + 1])
                    seg_len = line_length / line_points
                    for points in range(line_points):
                        seg_len_total = seg_len * (points + 1)
                        if points == 0:
                            x_point_now = x[segments] + seg_len * math.cos(angle_seg)
                            y_point_now = y[segments] + seg_len * math.sin(angle_seg)
                        else:
                            x_point_now = x_point_now + seg_len * math.cos(angle_seg)
                            y_point_now = y_point_now + seg_len * math.sin(angle_seg)
                        dist_point_to_traces.append(math.sqrt((self.x1 - x_point_now) ** 2 + (self.y1 - y_point_now) ** 2))
                    if min(dist_point_to_traces) < 7.0:
                        minpos = traces
                        found = 1
                        tag_name_here = df_traces.iloc[traces][3]
                        df_traces = df_traces.drop(df_traces.index[traces])
                        df_traces.to_csv(self.filename, index=False)
                        break
                if found == 1:
                    break

        # Delete the graphical elements
        self.canvas.delete(tag_name_here)
        self.canvas.delete("line")  # Ensure all lines are deleted
        self.canvas.delete(self.tag_line)
        self.coord_x = self.coord_x[:-1]
        self.coord_y = self.coord_y[:-1]
        

    def load_design(self, event=None):
        """Load a saved design, including components and traces."""
        self.canvas.old_coords = None
        self.load = 1
        self.tag_line_vector = []
        self.tag_comp_vector = []

        # Prompt the user to select a directory
        path = tkFileDialog.askdirectory()
        path = os.path.basename(path)
        print("Path is:", path)

        # Define filenames based on the selected path
        self.filename_pp = "Pick_and_place_components_with_pads.csv"
        self.filename = "{}/Traces_Coordinates_{}.csv".format(path, path)
        self.filename_pp_coord = "{}/PP_List_Coordinates_{}.csv".format(path, path)
        self.filename_base = "{}/Base_Coordinates_{}.csv".format(path, path)
        self.filename_pins_selected = "{}/Pins_Coordinates_{}.csv".format(path, path)

        # Load base coordinates
        origin_x = 2
        origin_y = 2
        df_PP_base = pd.read_csv(self.filename_base)
        x_base_array = np.fromstring(str(df_PP_base.iloc[0][0])[1:-1], sep=",")
        y_base_array = np.fromstring(str(df_PP_base.iloc[0][1])[1:-1], sep=",")
        self.x_border = x_base_array[1] - x_base_array[0]
        self.y_border = y_base_array[1] - y_base_array[0]

        # Load and draw components
        df_PP_Coord = pd.read_csv(self.filename_pp_coord)
        PP_list_len = df_PP_Coord.iloc[:][:]
        print(df_PP_Coord)

        for comps in range(len(PP_list_len)):
            self.component_selected = df_PP_Coord.iloc[comps][0]
            self.x = df_PP_Coord.iloc[comps][1]
            self.y = df_PP_Coord.iloc[comps][2]
            self.degree = df_PP_Coord.iloc[comps][3]
            self.tag_comp = df_PP_Coord.iloc[comps][6]
            self.tag_comp_vector.append(self.tag_comp)
            self.comp_selected = 1
            self.here_comp = 1
            self.draw_line(None)

        # Load and draw traces
        self.comp_selected = 0
        df_PP_Traces = pd.read_csv(self.filename, index_col=False)
        print(df_PP_Traces)
        Traces_list_len = df_PP_Traces.iloc[:][:]
        self.line_tag = 0

        for traces in range(len(Traces_list_len)):
            x = np.fromstring(str(df_PP_Traces.iloc[traces][1])[1:-1], sep=",")
            y = np.fromstring(str(df_PP_Traces.iloc[traces][2])[1:-1], sep=",")
            len_x = len(x)
            self.line_tag += 1

            for segments in range(len_x - 1):
                x1 = x[segments]
                y1 = y[segments]
                x2 = x[segments + 1]
                y2 = y[segments + 1]
                self.tag_line = df_PP_Traces.iloc[traces][3]
                self.tag_line_vector.append(self.tag_line)

                if df_PP_Traces.iloc[traces][0] == 1:
                    color_line = "#bf9000"  # Tunnel color
                    self.canvas.create_line(
                        x1, y1, x2, y2, width=3, fill=color_line, tags=(self.tag_line)
                    )
                else:
                    color_line = "gray50"
                    self.canvas.create_line(
                        x1, y1, x2, y2, width=1, fill=color_line, tags=(self.tag_line)
                    )

                # Add the missing section here
                if segments == len_x - 2:
                    x = np.fromstring(str(df_PP_Traces.iloc[traces][1])[1:-1], sep=",")
                    y = np.fromstring(str(df_PP_Traces.iloc[traces][2])[1:-1], sep=",")
                    x1 = x[segments + 1]
                    y1 = y[segments + 1]
                    self.draw_line(None)

        # Draw the workspace boundary
        self.canvas.create_line(origin_x, origin_y, self.x_border, origin_y, fill="black", width=1)
        self.canvas.create_line(self.x_border, origin_y, self.x_border, self.y_border, fill="black", width=1)
        self.canvas.create_line(self.x_border, self.y_border, origin_x, self.y_border, fill="black", width=1)
        self.canvas.create_line(origin_x, self.y_border, origin_x, origin_y, fill="black", width=1)

        # Reset state variables
        self.load = 0
        self.canvas.old_coords = None
        self.here = 1
        self.coord_x = []
        self.coord_y = []

        # Simulate selecting the component in the dropdown menu
    
    def simulate_scroll_and_select(self, target_component, delay, idx):
        values = self.combo['values']
        # Always start from the top
        if idx == 0:
            self.combo.set(values[0])
            self.combo.update()
        if idx >= len(values):
            print('Component "{}" not found in combobox values!'.format(target_component))
            return
        value = values[idx]
        self.combo.set(value)
        self.combo.update()
        if value == target_component:
            self.combo.event_generate('<<ComboboxSelected>>')
            print('Selected ', value)
            return
        self.root.after(delay, lambda: self.simulate_scroll_and_select(target_component, delay, idx+1))

    def entry_callback(self, event):
        """Handle the creation of a new design folder and initialize files."""
        self.tag_line_vector = []
        self.tag_comp_vector = []
        self.name_folder = self.entry.get()
        path = "./{}".format(self.name_folder)
        os.mkdir(path)
        print("Folder {} created!".format(self.name_folder))

        # Define filenames based on the new folder
        self.filename = "{}/Traces_Coordinates_{}.csv".format(path, self.name_folder)
        self.filename_pp = "Pick_and_place_components_with_pads.csv"
        self.filename_pp_coord = "{}/PP_List_Coordinates_{}.csv".format(path, self.name_folder)
        self.filename_base = "{}/Base_Coordinates_{}.csv".format(path, self.name_folder)
        self.filename_pins_selected = "{}/Pins_Coordinates_{}.csv".format(path, self.name_folder)

        # Draw workspace boundary
        self.canvas.create_line(self.origin_x, self.origin_y, self.x_border, self.origin_y, fill="black", width=1)
        self.canvas.create_line(self.x_border, self.origin_y, self.x_border, self.y_border, fill="black", width=1)
        self.canvas.create_line(self.x_border, self.y_border, self.origin_x, self.y_border, fill="black", width=1)
        self.canvas.create_line(self.origin_x, self.y_border, self.origin_x, self.origin_y, fill="black", width=1)

        # Save base data
        a_list = ["w", "a"]
        for a in a_list:
            with open(self.filename_base, a) as f:
                writer = csv.writer(f)
                x_base = [self.origin_x, self.x_border]
                y_base = [self.origin_y, self.y_border]
                data = [x_base, y_base]
                if a == "w":
                    first_row = ["Base X", "Base Y"]
                    writer.writerow(first_row)
                else:
                    writer.writerow(data)

        # Initialize components list
        with open(self.filename_pp_coord, "w") as f:
            writer = csv.writer(f)
            first_row = ["Component", "X", "Y", "Orientation", "Perimeter X", "Perimeter Y", "Tag"]
            writer.writerow(first_row)

        # Create pin file
        with open(self.filename_pins_selected, "w") as f:
            writer = csv.writer(f)
            first_row = ["X", "Y", "Component", "Tag"]
            writer.writerow(first_row)

        self.canvas.old_coords = None
        self.coord_x = []
        self.coord_y = []

    def tracer_coordinates(self, filename_pp, x_center, y_center, num_points, component_selected, theta):
        """Calculate the coordinates for the selected component."""
        df = pd.read_csv(filename_pp)
        width_ind = 1  # Index for the width of the component
        length_ind = 2  # Index for the length of the component
        pins_ind = 7  # Index for the number of pins
        conn_lead_ind = 8  # Ignore for now
        coordinate_x_ind = 9  # Index for the first x-coordinate of pin #1
        offset_usb = -1  # Offset needed for USB components
        rot_mat = [[math.cos(theta), -1 * math.sin(theta)], [math.sin(theta), math.cos(theta)]]

        # Find the selected component in the CSV file
        for i in range(len(df)):
            if component_selected == df.iloc[i][0]:
                component_from_list = i
                break
        if component_selected != "FSR Place":
            num_pins = int(df.iloc[component_from_list][pins_ind])
            coordinate_y_ind = coordinate_x_ind + num_pins

            # Calculate rotated pin coordinates
            pins_x_coordinate_rotation = []
            pins_y_coordinate_rotation = []
            for val in range(num_pins):
                x = np.array(df.iloc[component_from_list][coordinate_x_ind + val])
                y = np.array(df.iloc[component_from_list][coordinate_y_ind + val])
                pins_x_coordinate_rotation.append(
                    x_center + self.scaling_factor * (x * math.cos(theta) - y * math.sin(theta))
                )
                pins_y_coordinate_rotation.append(
                    y_center - self.scaling_factor * (x * math.sin(theta) + y * math.cos(theta))
                )

            pins_x_coordinate = pins_x_coordinate_rotation
            pins_y_coordinate = pins_y_coordinate_rotation

            if component_selected == 'USB':
                pins_y_coordinate = [y + offset_usb for y in pins_y_coordinate]

            # Define the perimeter as an obstacle
            x_top, y_top = self.calculate_perimeter_top(df, component_from_list, x_center, y_center, theta, num_points)
            x_right, y_right = self.calculate_perimeter_right(df, component_from_list, x_center, y_center, theta, num_points)
            x_bottom, y_bottom = self.calculate_perimeter_bottom(df, component_from_list, x_center, y_center, theta, num_points)
            x_left, y_left = self.calculate_perimeter_left(df, component_from_list, x_center, y_center, theta, num_points)

            # Adjust pin connections based on overlap
            pins_x_coordinate, pins_y_coordinate = self.adjust_pins(
                pins_x_coordinate, pins_y_coordinate, df, component_from_list, x_top, y_top, x_bottom, y_bottom, x_right, y_right, x_left, y_left
            )

            return pins_x_coordinate, pins_y_coordinate, x_top, y_top, x_bottom, y_bottom, x_right, y_right, x_left, y_left

    def calculate_perimeter_top(self, df, component_from_list, x_center, y_center, theta, num_points):
        """Calculate the top perimeter of the component."""
        y_top = y_center + self.scaling_factor * df.iloc[component_from_list][2] / 2
        y_top = y_top * np.ones(num_points)
        x_top = np.linspace(
            x_center - self.scaling_factor * df.iloc[component_from_list][1] / 2,
            x_center + self.scaling_factor * df.iloc[component_from_list][1] / 2,
            num_points
        )
        if len(x_top) > len(y_top):
            x_top = x_top[:-1]
        x_top, y_top = self.rotate_coordinates(x_top, y_top, x_center, y_center, theta)
        return x_top, y_top

    def calculate_perimeter_right(self, df, component_from_list, x_center, y_center, theta, num_points):
        """Calculate the right perimeter of the component."""
        y_right = np.linspace(
            y_center - self.scaling_factor * df.iloc[component_from_list][2] / 2,
            y_center + self.scaling_factor * df.iloc[component_from_list][2] / 2,
            num_points
        )
        x_right = x_center + self.scaling_factor * df.iloc[component_from_list][1] / 2
        x_right = x_right * np.ones(num_points)
        x_right, y_right = self.rotate_coordinates(x_right, y_right, x_center, y_center, theta)
        return x_right, y_right

    def calculate_perimeter_bottom(self, df, component_from_list, x_center, y_center, theta, num_points):
        """Calculate the bottom perimeter of the component."""
        y_bottom = y_center - self.scaling_factor * df.iloc[component_from_list][2] / 2
        y_bottom = y_bottom * np.ones(num_points)
        x_bottom = np.linspace(
            x_center - self.scaling_factor * df.iloc[component_from_list][1] / 2,
            x_center + self.scaling_factor * df.iloc[component_from_list][1] / 2,
            num_points
        )
        if len(x_bottom) > len(y_bottom):
            x_bottom = x_bottom[:-1]
        x_bottom, y_bottom = self.rotate_coordinates(x_bottom, y_bottom, x_center, y_center, theta)
        return x_bottom, y_bottom

    def calculate_perimeter_left(self, df, component_from_list, x_center, y_center, theta, num_points):
        """Calculate the left perimeter of the component."""
        y_left = np.linspace(
            y_center - self.scaling_factor * df.iloc[component_from_list][2] / 2,
            y_center + self.scaling_factor * df.iloc[component_from_list][2] / 2,
            num_points
        )
        x_left = x_center - self.scaling_factor * df.iloc[component_from_list][1] / 2
        x_left = x_left * np.ones(num_points)
        x_left, y_left = self.rotate_coordinates(x_left, y_left, x_center, y_center, theta)
        return x_left, y_left

    def rotate_coordinates(self, x_coords, y_coords, x_center, y_center, theta):
        """Rotate coordinates around a center point."""
        x_rotated, y_rotated = [], []
        for x, y in zip(x_coords, y_coords):
            x_rotated.append(x_center + (x - x_center) * math.cos(theta) - (y - y_center) * math.sin(theta))
            y_rotated.append(y_center + (x - x_center) * math.sin(theta) + (y - y_center) * math.cos(theta))
        return x_rotated, y_rotated

    def adjust_pins(self, pins_x_coordinate, pins_y_coordinate, df, component_from_list, x_top, y_top, x_bottom, y_bottom, x_right, y_right, x_left, y_left):
        """Adjust pin coordinates based on overlap with borders."""
        conn_lead_ind = 8  # Index for connection lead length in the CSV file
        scaling_factor = self.scaling_factor

        # Determine the borders of the component
        x_borders = [x_top[0], x_bottom[0], x_right[0], x_left[0]]
        y_borders = [y_top[0], y_bottom[0], y_right[0], y_left[0]]
        right_border_x = max(x_borders)
        left_border_x = min(x_borders)
        top_border_y = max(y_borders)
        bottom_border_y = min(y_borders)

        # Adjust pin coordinates based on their position relative to the borders
        for pins_total in range(len(pins_x_coordinate)):
            if pins_x_coordinate[pins_total] >= right_border_x:
                # Pin is on the right border
                pins_x_coordinate[pins_total] -= df.iloc[component_from_list][conn_lead_ind] * scaling_factor
            elif pins_x_coordinate[pins_total] <= left_border_x:
                # Pin is on the left border
                pins_x_coordinate[pins_total] += df.iloc[component_from_list][conn_lead_ind] * scaling_factor
            elif pins_y_coordinate[pins_total] >= top_border_y:
                # Pin is on the top border
                pins_y_coordinate[pins_total] -= df.iloc[component_from_list][conn_lead_ind] * scaling_factor
            elif pins_y_coordinate[pins_total] <= bottom_border_y:
                # Pin is on the bottom border
                pins_y_coordinate[pins_total] += df.iloc[component_from_list][conn_lead_ind] * scaling_factor

        return pins_x_coordinate, pins_y_coordinate

    def FSR_placement(self, x, y, scaling_factor):
        """Place FSR sensors in a grid pattern."""

        spacing_between_sensors_x = 20 * scaling_factor
        spacing_between_sensors_y = 25 * scaling_factor
        number_sensors_col = 2  # Sensors column
        number_sensors_row = 2  # Sensors rows

        for pixels_x in range(
            int(x - (number_sensors_col * spacing_between_sensors_x) / 2 + spacing_between_sensors_x / 2),
            int(x + (number_sensors_col * spacing_between_sensors_x) / 2 + spacing_between_sensors_x / 2),
            int(spacing_between_sensors_x),
        ):
            for pixels_y in range(
                int(y - (number_sensors_row * spacing_between_sensors_y) / 2 + spacing_between_sensors_y / 2),
                int(y + (number_sensors_row * spacing_between_sensors_y) / 2 + spacing_between_sensors_y / 2),
                int(spacing_between_sensors_y),
            ):
                self.canvas.create_oval(pixels_x, pixels_y, pixels_x, pixels_y, fill="black", width=0)

    def move_cursor(self, target_x, target_y, duration=300):
        """Move the cursor so that its tip points to the target coordinates over the specified duration."""
        current_coords = self.canvas.coords(self.cursor)
        #print("Cursor moved to:", current_coords)
        # The tip of the arrow is the first point in the polygon
        tip_x = current_coords[0]
        tip_y = current_coords[1]
        steps = 80  # Number of steps for the animation #100 points is smoother
        dx = float(target_x - tip_x) / steps
        dy = float(target_y - tip_y) / steps

        def animate(step):
            if step <= steps:
                self.canvas.move(self.cursor, dx, dy)  # Move the arrow
                self.canvas.tag_raise(self.cursor)  # Ensure the cursor is on top
                self.root.after(duration // steps, animate, step + 1)
            else:
        # Final correction to ensure tip is exactly at target
                current_coords = self.canvas.coords(self.cursor)
                tip_x = current_coords[0]
                tip_y = current_coords[1]
                correction_dx = target_x - tip_x
                correction_dy = target_y - tip_y
                self.canvas.move(self.cursor, correction_dx, correction_dy)
        animate(0)
        current_coords = self.canvas.coords(self.cursor)

    def reset_cursor_tip(self, x, y):
        current_coords = self.canvas.coords(self.cursor)
        tip_x = current_coords[0]
        tip_y = current_coords[1]
        dx = x - tip_x
        dy = y - tip_y
        self.canvas.move(self.cursor, dx, dy)

    def calculate_angle(self,x1, y1, x2, y2):
        # Calculate the difference in x and y coordinates
        offset_value = 0.000001
        dx = x2 - x1 + offset_value
        dy = y2 - y1 + offset_value
        
        #slope = (dy+offset_value)/(dx+offset_value)

        # Use atan2 to calculate the angle in radians
        angle_radians = math.atan2(dy, dx)
        return angle_radians


class FakeEvent(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


if __name__ == "__main__":
    root = tk.Tk()
    app = TraceMakerApp(root)
    root.mainloop()