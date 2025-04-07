from tkinter import *
from tkinter import Menu, filedialog, simpledialog
import customtkinter as ct 
from CTkToolTip import *
import cv2
import os
import threading
import pytic #Pololu Motor Controls
import serial #ESP connection
import pickle
import serial.tools.list_ports
import numpy as np  
from datetime import datetime
from pypylon import pylon
from PIL import Image, ImageTk
from pathlib import Path
from time import sleep
from time import time

print(Path.cwd())

# Tkinter appearance settings
ct.set_appearance_mode("Light")  

# Initialize the lock
camera_lock = threading.Lock()
scale = 2
exposure_int = 1000

# File to store the selected path
PERSISTENCE_FILE = "saved_path.pkl"

ct.set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
ct.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ct.CTk):
    def __init__(self):
        super().__init__()
        self.title("SDF Basler")
        self.geometry("800x600")  # Instead of "", set a reasonable default size

        # Make grid layout flexible
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Dictionary to store pages
        self.pages = {}

        # Add pages dynamically
        for Page in (MainMenu, CapturePage):
            page = Page(self)
            self.pages[Page] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page(MainMenu)

    def show_page(self, page_class):
        """Show the selected page"""
        page = self.pages[page_class]
        page.tkraise()

class MainMenu(ct.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        # Configure grid layout for responsiveness
        self.grid_columnconfigure((0, 2), weight=1)  # Padding
        self.grid_columnconfigure(1, weight=3)  # Main content
        self.grid_rowconfigure((0, 2), weight=1)  # Padding
        self.grid_rowconfigure(1, weight=3)  # Main content

        # Create a responsive container
        container = ct.CTkFrame(self)
        container.grid(row=1, column=1, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure((1, 2), weight=3)

        # Title Label
        label = ct.CTkLabel(container, text="Main Menu")
        label.grid(row=0, column=0, pady=10, sticky="nsew")

        # Buttons (resize dynamically)
        btn_page1 = ct.CTkButton(container, text="Data Capture", command=lambda: master.show_page(CapturePage))
        btn_page1.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")


class CapturePage(ct.CTkFrame):
    global tic, tc

    # Motor Initialization
    tic = pytic.PyTic()
    tc = pytic.pytic_protocol.tic_constant

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml') 
    print(config_path)

    def __init__(self, master):
        super().__init__(master)
        for widget in self.winfo_children():
            widget.destroy()

        self.tabview = ct.CTkTabview(self)
        self.tabview.grid(row=0, column=0, columnspan=3, padx = 10, pady = 5, sticky="nsew")

        # Add two tabs
        self.tab1 = self.tabview.add("Data Capture")
        self.tab2 = self.tabview.add("Recent Capture")

        # Configure grid layout for PageOne (parent)
        self.grid_rowconfigure(0, weight=1, uniform=True)
        self.grid_columnconfigure(0, weight=1, uniform=True)
        self.grid_columnconfigure(1, weight=4, uniform=True)  # Middle column
        self.grid_columnconfigure(2, weight=1, uniform=True)
        
        self.tab1.grid_rowconfigure(0, weight=3, uniform=True)
        self.tab1.grid_rowconfigure(1, weight=3, uniform=True)
        self.tab1.grid_rowconfigure(2, weight=1, uniform=True)
        self.tab1.grid_rowconfigure(3, weight=2, uniform= True)
        self.tab1.grid_columnconfigure(0, weight=1, uniform=True)
        self.tab1.grid_columnconfigure(1, weight=4, uniform=True) # Middle column
        self.tab1.grid_columnconfigure(2, weight=1, uniform=True) 

        # Left side panel (top)
        self.left_frame = ct.CTkFrame(self.tab1)
        self.left_frame.grid(row = 0, column = 0, padx = 10, pady = 5, sticky = "nsew")

        self.title = ct.CTkLabel(self.left_frame, text = "TOI Basler GUI", font=ct.CTkFont(size=25, weight="bold"))
        self.title.grid(row = 0, column = 0, padx = 10, pady = 5, sticky = "nsew")

        self.menu = ct.CTkButton(self.left_frame, text = "Go To Menu", command=lambda: master.show_page(MainMenu))
        self.menu.grid(row = 1, column = 0, padx = 10, pady = 2, sticky = "nsew")

        # Create and place a dropdown menu (CTkComboBox)
        self.com_dropdown = ct.CTkComboBox(self.left_frame, values=["Searching..."], command=self.connect_to_port)
        self.com_dropdown.grid(row = 2, column = 0, padx = 10, pady = 2, sticky = "nsew")

        # Create and place a refresh button
        refresh_button = ct.CTkButton(self.left_frame, text="Refresh Ports", command=self.refresh_ports)
        refresh_button.grid(row = 3, column = 0, padx = 10, pady = 2, sticky = "nsew")

        # Populate the dropdown with available COM ports on startup
        self.refresh_ports()

        self.on = ct.CTkButton(self.left_frame, text = "Turn on System", command=self.turn_on)
        self.on.grid(row = 4, column = 0, padx = 10, pady = 2, sticky = "nsew")

        self.path = ct.CTkEntry(self.left_frame, placeholder_text = "Enter folder path or click 'Browse'")
        self.path.grid(row = 5, column = 0, padx = 10, pady = 2, sticky ="nsew")

        self.browse_path = ct.CTkButton(self.left_frame, text = "Browse", command=self.browse_folder)
        self.browse_path.grid(row = 6, column = 0, padx = 10, pady = 2, sticky = "nsew")
        
        # Load the saved path if it exists
        self.load_saved_path()

        # Trigger save on entry modification
        self.path.bind("<FocusOut>", self.save_path)

        self.name_entry = ct.CTkEntry(self.left_frame, placeholder_text= "Enter File Name")
        self.name_entry.grid(row = 7, column = 0, padx = 10, pady = 2, sticky = "nsew")

        # Left side panel (middle)
        self.settings_frame = ct.CTkFrame(self.tab1)
        self.settings_frame.grid(row = 1, column = 0, rowspan = 2, padx = 10, pady = 3, sticky = "nsew")

        self.label_settings = ct.CTkLabel(self.settings_frame, text = "Camera Settings", font=ct.CTkFont(size=15, weight="bold"))
        self.label_settings.grid(row = 0, column = 0, padx = 10, pady = 3, sticky = "nsew")

        self.fps = ct.CTkLabel(self.settings_frame, text = "FPS Limit (Default = 30):")
        self.fps.grid(row = 1, column = 0, padx = 10, pady = 3, sticky = "nsw")

        self.fps_entry = ct.CTkEntry(self.settings_frame, placeholder_text = "Max FPS")
        self.fps_entry.grid(row = 2, column = 0, padx = 10, pady = 3, sticky = "nsew")

        self.fps_button = ct.CTkButton(self.settings_frame, text = "Enter FPS", command = self.fps_calculator)
        self.fps_button.grid(row = 3, column = 0, padx =10, pady = 3, sticky = "nsew")

        self.exposure = ct.CTkLabel(self.settings_frame, text = "Exposure (µs), Default = 1000 µs:")
        self.exposure.grid(row = 4, column = 0, padx = 10, pady = 3, sticky = "nsw")

        self.exposure_entry = ct.CTkEntry(self.settings_frame, placeholder_text = "Exposure Time")
        self.exposure_entry.grid(row = 5, column = 0, padx = 10, pady = 3, sticky ="nsew")

        self.exposure_button = ct.CTkButton(self.settings_frame, text = "Enter Exp. Time", command = self.update_exposure_time)
        self.exposure_button.grid(row = 6, column = 0, padx = 10, pady = 3, sticky = "nsew")

        self.gain = ct.CTkLabel(self.settings_frame, text = "Enter Gain (Default = 0):")
        self.gain.grid(row = 7, column = 0, padx = 10, pady = 3, sticky = "nsw")

        self.gain_entry = ct.CTkEntry(self.settings_frame, placeholder_text = "Gain Value")
        self.gain_entry.grid(row = 8, column = 0, padx = 10, pady = 3, sticky = "nsew")

        self.gain_button = ct.CTkButton(self.settings_frame, text = "Enter Gain", command= self.change_gain)
        self.gain_button.grid(row = 9, column = 0, padx = 10, pady = 3, sticky = "nsew")

        self.white_balance = ct.CTkSwitch(self.settings_frame, text = "Auto White Balance", command = self.white_balance_trigger)
        self.white_balance.grid(row = 10, column = 0, padx = 10, pady = 3, sticky = "nsw")

        tooltip_1 = CTkToolTip(self.white_balance, message="Automatic Continuous White Balance Mode. Unplug camera to reset.")
        
        # Left side panel (bottom)
        self.zoom_frame = ct.CTkFrame(self.tab1)
        self.zoom_frame.grid(row = 3, column = 0, padx = 10, pady = 10, sticky = "nsew")
        
        self.zoom_frame.columnconfigure((0, 1), weight = 1, uniform = True)

        self.zoom_label = ct.CTkLabel(self.zoom_frame, text = "Live View Settings", font=ct.CTkFont(size=15, weight="bold"))
        self.zoom_label.grid(row = 0, column = 0, columnspan = 2, padx = 10, pady = 5, sticky = "nsew")
        
        self.zoom_title = ct.CTkLabel(self.zoom_frame, text = "Zoom:")
        self.zoom_title.grid(row = 1, column = 0, padx =10, pady = 2, sticky = "nsw")
        
        self.zoom_counter = ct.CTkLabel(self.zoom_frame, text="2.0x")  # Default to 2x zoom
        self.zoom_counter.grid(row=1, column=1, padx=10, pady=2, sticky="nsw")

        self.zoom_scale = ct.CTkSlider(self.zoom_frame, from_=2, to=10, command=self.resize)
        self.zoom_scale.set(2)
        self.zoom_scale.grid(row=2, column=0, columnspan=2, padx=10, pady=2, sticky="nsew")
        
        # Add state variables for flip and rotation
        self.flip_horizontal = False
        self.rotation_angle = 0  # 0, 90, 180, 270
    
        self.flip = ct.CTkButton(self.zoom_frame, text = "Flip Image", command = self.toggle_flip)
        self.flip.grid(row = 4, column = 0, padx = 10, pady = 5, sticky = "nsew")
        
        self.rotate = ct.CTkButton(self.zoom_frame, text = "Rotate Image", command = self.toggle_rotation)
        self.rotate.grid(row = 4, column = 1, padx = 10, pady = 5, sticky = "nsew")

        self.switch_var = ct.StringVar(value="off")
        self.dark_mode = ct.CTkSwitch(self.zoom_frame, text="Dark Mode", command=lambda: self.change_appearance_mode_event(self.switch_var.get()), variable=self.switch_var, onvalue="on", offvalue="off")
        self.dark_mode.grid(row = 5, column = 0, columnspan = 2, padx = 10, pady = 2, sticky = "nsw")

        # Main panel, camera feed
        self.main_frame = ct.CTkFrame(self.tab1)
        self.main_frame.grid(row = 0, column = 1, rowspan = 4, padx = 10, pady = 5, sticky = "nsew")

        self.main_frame.rowconfigure(0, weight = 6, uniform=True)
        self.main_frame.rowconfigure(1, weight = 3, uniform=True)
        self.main_frame.columnconfigure(0, weight= 2, uniform=True)
        self.main_frame.columnconfigure(1, weight = 2, uniform=True)
        self.main_frame.columnconfigure(2, weight= 6, uniform = True)
        self.main_frame.columnconfigure(3, weight= 2, uniform= True)

        # Set fixed size for frames
        self.camera_frame = ct.CTkFrame(self.main_frame)
        self.camera_frame.grid(row=0, column=1, columnspan=2, padx=10, pady=5)

        self.feed = ct.CTkLabel(self.camera_frame, text = "")
        self.feed.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5)

        # Do the same for zoom frame
        self.zoom_frame = ct.CTkFrame(self.main_frame)
        self.zoom_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        
        self.zoom = ct.CTkLabel(self.zoom_frame, text = "")
        self.zoom.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5)

        # Right side panel (top)
        self.axial_frame = ct.CTkFrame(self.tab1)
        self.axial_frame.grid(row = 0, column = 2, padx = 10, pady = 5, sticky = "nsew")

        self.axial_label = ct.CTkLabel(self.axial_frame, text = "Video Saving - Axial Scan", font=ct.CTkFont(size=15, weight="bold"))
        self.axial_label.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = "nsew")

        self.range_label = ct.CTkLabel(self.axial_frame, text = "Scan Range Z (mm):")
        self.range_label.grid(row = 1, column = 0, padx = 10, pady = 5, sticky = "nsw")

        self.range_entry = ct.CTkEntry(self.axial_frame, placeholder_text= "Scan Range (mm)")
        self.range_entry.grid(row = 2, column = 0, padx = 10, pady = 5, sticky = "nsew")

        self.axial_label = ct.CTkLabel(self.axial_frame, text = "Axial Step Size (mm):")
        self.axial_label.grid(row = 3, column = 0, padx = 10, pady = 5, sticky = "nsw")

        self.axial_entry = ct.CTkEntry(self.axial_frame, placeholder_text = "Step Size (mm)")
        self.axial_entry.grid(row = 4, column = 0, padx = 10, pady = 5, sticky = "nsew")

        self.axial_button = ct.CTkButton(self.axial_frame, text = "Record Video", command = self.axial)
        self.axial_button.grid(row = 5, column = 0, padx = 10, pady = 5, sticky = "nsew")

        # Right side panel (middle)
        self.data_frame = ct.CTkFrame(self.tab1)
        self.data_frame.grid(row = 1, column = 2, padx = 10, pady = 10, sticky = "nsew")

        self.data_label = ct.CTkLabel(self.data_frame, text = "Data Collect", font=ct.CTkFont(size=15, weight="bold"))
        self.data_label.grid(row = 0, column = 0, columnspan = 2, padx = 10, pady = 5, sticky = "nsew")

        self.record_label = ct.CTkLabel(self.data_frame, text = "Number of Frames to Record:")
        self.record_label.grid(row = 1, column = 0, columnspan = 2,  padx = 10, pady = 5, sticky = "nsw")

        self.record_entry = ct.CTkEntry(self.data_frame, placeholder_text= "Number of Frames")
        self.record_entry.grid(row = 2, column = 0, columnspan = 2, padx = 10, pady = 5, sticky = "nsew")

        self.record_button = ct.CTkButton(self.data_frame, text = "Record Video", command = self.toggle_record_frames)
        self.record_button.grid(row = 3, column = 0, columnspan = 2, padx = 10, pady = 5, sticky = "nsew")

        self.picture_label = ct.CTkLabel(self.data_frame, text = "Capture Picture:")
        self.picture_label.grid(row = 4, column = 0, padx = 10, pady = 5, sticky = "nsw")
               
        # Create a canvas to represent the light
        self.canvas = ct.CTkCanvas(self.data_frame, width=40, height=40)
        self.canvas.grid(row = 4, column = 1, padx= 5,pady = 2, sticky = "nsew")
        
        # Create a light for pictures       
        self.light = self.canvas.create_oval(12, 12, 48, 48, fill="red")
        
        # State to track the light color (on or off)
        self.is_on = False

        self.picture = ct.CTkButton(self.data_frame, text = "Capture Picture", command=self.capture_picture)
        self.picture.grid(row = 5, column = 0, columnspan = 2, padx = 10, pady = 5, sticky = "nsew")

        # Right side panel (bottom)
        self.motor_frame = ct.CTkFrame(self.tab1)
        self.motor_frame.grid(row = 2, column = 2, rowspan = 2, padx = 10, pady = 5, sticky ="nsew")

        self.label_motor_group = ct.CTkLabel(self.motor_frame, text="Quick Motor Controls", font=ct.CTkFont(size=15, weight="bold"))
        self.label_motor_group.grid(row=0, column=0, padx=10, pady=3, sticky="nsew")
        
        self.motor_up_high = ct.CTkButton(self.motor_frame, text="+150um", command=lambda: self.button_motor("150"))
        self.motor_up_high.grid(row = 1, column = 0, pady=5, padx=10, sticky= "nsew")
        
        self.motor_up_high = ct.CTkButton(self.motor_frame, text="+100um", command=lambda: self.button_motor("100"))
        self.motor_up_high.grid(row = 2, column = 0, pady=5, padx=10, sticky= "nsew")
        
        self.motor_up_low = ct.CTkButton(self.motor_frame, text="+10um", command=lambda: self.button_motor("10"))
        self.motor_up_low.grid(row = 3, column = 0, pady=5, padx=10, sticky= "nsew")
        
        self.motor_down_low = ct.CTkButton(self.motor_frame, text="-10um", command=lambda: self.button_motor("-10"))
        self.motor_down_low.grid(row = 4, column = 0, pady=5, padx=10, sticky= "nsew")
        
        self.motor_down_high = ct.CTkButton(self.motor_frame, text="-100um", command=lambda: self.button_motor("-100"))
        self.motor_down_high.grid(row = 5, column = 0, pady=5, padx=10, sticky= "nsew")
        
        self.motor_down_high = ct.CTkButton(self.motor_frame, text="-150um", command=lambda: self.button_motor("-150"))
        self.motor_down_high.grid(row = 6, column = 0, pady=5, padx=10, sticky= "nsew")
        
        # Define a mapping between button IDs and corresponding buttons in your GUI
        self.button_mapping = {
            4: self.motor_up_high,
            3: self.motor_up_low,
            2: self.motor_down_low,
            1: self.motor_down_high,
            5: self.axial_button,
            6: self.picture
        }
    
        self.tab2.grid_rowconfigure(0, weight=1, uniform=True)
        self.tab2.grid_rowconfigure(1, weight=6, uniform=True)
        self.tab2.grid_rowconfigure(2, weight = 1, uniform = True)
        self.tab2.grid_columnconfigure(0, weight=1, uniform=True)
        self.tab2.grid_columnconfigure(1, weight=7, uniform=True) # Middle column
        self.tab2.grid_columnconfigure(2, weight=1, uniform=True) 

        # Create a frame and grid it
        self.tab2_frame = ct.CTkFrame(self.tab2)
        self.tab2_frame.grid(row=1, column=1, sticky="nsew")

        self.tab2_frame.grid_rowconfigure(0, weight=1)  
        self.tab2_frame.grid_columnconfigure(0, weight=1)

        # Create a canvas and grid it
        self.canvas_frame = ct.CTkCanvas(self.tab2_frame, cursor="cross")
        self.canvas_frame.grid(row=0, column=0, columnspan = 5, rowspan = 8, sticky="nsew")

        # Create navigation frame and grid it
        self.navigation_frame = ct.CTkFrame(self.tab2)  
        self.navigation_frame.grid(row=2, column=1, pady = 10, padx =10, sticky="nsew")

        self.navigation_frame.columnconfigure(1, weight = 5)

        # Navigation buttons
        self.prev_button = ct.CTkButton(self.navigation_frame, text="Previous Frame", command=self.prev_frame)
        self.prev_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.next_button = ct.CTkButton(self.navigation_frame, text="Next Frame", command=self.next_frame)
        self.next_button.grid(row=1, column=3, padx=10, pady=10, sticky="e")

        self.frame_counter = ct.CTkLabel(self.navigation_frame, text="Frame 0/0")
        self.frame_counter.grid(row=1, column=1, padx=10, sticky = "w")

        self.frame_slider = ct.CTkSlider(self.navigation_frame, from_=0, to=0, command=self.jump_to_frame)
        self.frame_slider.grid(row=0, column=1, padx=20, sticky="ew")

        # Load frame
        self.load_frame = ct.CTkFrame(self.tab2)
        self.load_frame.grid(row=0, column=1, pady = 10, sticky = "nsew")

        self.load_frame.grid_columnconfigure((0, 1, 2), weight = 1, uniform = True)
        self.load_frame.grid_rowconfigure(1, weight = 1, uniform= True)

        load_button = ct.CTkButton(self.load_frame, text = "Load Recent Data", command= self.upload_image)
        load_button.grid(row = 0, column = 1, padx = 10, pady = 10, sticky = "ns")

        # Menu
        self.home2_button = ct.CTkButton(self.load_frame, text="Go to Menu", command=lambda: master.show_page(MainMenu))
        self.home2_button.grid(row=0, column=0, padx = 10, pady = 10, sticky="ns")

        # Create a StringVar for the switch
        self.switch2_var = ct.StringVar(value="off")
        self.appearance2_mode_menu = ct.CTkSwitch(self.load_frame, text="Dark Mode", command=lambda: self.change_appearance_mode_event(self.switch_var.get()), variable=self.switch_var, onvalue="on", offvalue="off")
        self.appearance2_mode_menu.grid(row=0, column=2, padx=10, pady=10, sticky="ns")
        
        self.frame_adjustments = {}
        # Zoom factor
        self.zoom_factor = 1  

        # Bind actions
        self.canvas_frame.bind("<MouseWheel>", self.zoom_image)  
    
    def update_frame_counter(self):
        self.frame_counter.configure(
            text=f"Frame {self.current_frame_index + 1}/{len(self.frames)}"
        )

    def jump_to_frame(self, value):
        """Properly updates the displayed image when the slider moves."""
        self.current_frame_index = int(value)
        print(f"Slider moved to frame {self.current_frame_index}")  # Debugging line
        self.image = self.frames[self.current_frame_index]
        self.display_image()
        self.frame_slider.set(self.current_frame_index)
        self.frame_slider.update_idletasks()
        self.update_frame_counter()  # Add this line

    def prev_frame(self):
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.image = self.frames[self.current_frame_index]
            self.display_image()
            self.frame_slider.set(self.current_frame_index)
            self.frame_slider.update_idletasks()
            self.update_frame_counter()  # Add this line

    def next_frame(self):
        if self.current_frame_index < len(self.frames) - 1:
            self.current_frame_index += 1
            self.image = self.frames[self.current_frame_index]
            self.display_image()
            self.frame_slider.set(self.current_frame_index)
            self.frame_slider.update_idletasks()
            self.update_frame_counter()  # Add this line
           
    def zoom_image(self, event):
        # Adjust zoom factor based on mouse wheel movement
        if event.delta > 0:  # Zoom in
            self.zoom_factor *= 1.1
        elif event.delta < 0:  # Zoom out
            self.zoom_factor /= 1.1

        # Ensure the zoom factor stays within a reasonable range
        self.zoom_factor = max(0.1, min(self.zoom_factor, 5))

        self.display_image()  # Redisplay the image and annotations with the new zoom factor

    def upload_image(self):
        try:
            # Ensure the required variables exist before using them
            if 'video_folder' not in globals() or 'video_filename' not in globals():
                self.show_warning_popup("Error: 'video_folder' or 'video_filename' is not defined.")
                return  # Stop execution

            file_path = os.path.join(video_folder, video_filename)

            # Check if the file exists
            if not os.path.exists(file_path):
                self.show_warning_popup(f"Error: File not found at {file_path}")
                return

            # Open video file
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                self.show_warning_popup(f"Error: Cannot open video file {file_path}")
                return

            self.frames = []
            self.current_frame_index = 0
            self.zoom_factor = 1.0  # Reset zoom factor when loading new video

            # Read video frames
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
                self.frames.append(Image.fromarray(frame))

            cap.release()

            if not self.frames:
                self.show_warning_popup("Warning: No frames found in video.")
                return

            self.image = self.frames[self.current_frame_index]
            num_frames = max(len(self.frames) - 1, 1)  # Prevent division by zero
            self.frame_slider.configure(to=num_frames, from_=0)
            self.frame_slider.set(0)
            print(f"Total frames loaded: {len(self.frames)}")

            self.frame_annotations = {i: [] for i in range(len(self.frames))}  # Initialize annotations
            self.display_image()
            self.update_frame_counter()  # Add this line to update frame counter initially
            
        except Exception as e:
            self.show_warning_popup(f"An unexpected error occurred:\n{str(e)}")
    
    def display_image(self):
        if self.image:
            # Get canvas dimensions
            canvas_width = self.canvas_frame.winfo_width()
            canvas_height = self.canvas_frame.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:  # Canvas not yet properly sized
                self.canvas_frame.update_idletasks()  # Force update
                canvas_width = self.canvas_frame.winfo_width()
                canvas_height = self.canvas_frame.winfo_height()
                
                # If still not sized properly, use default values
                if canvas_width <= 1:
                    canvas_width = 800  # Default width
                if canvas_height <= 1:
                    canvas_height = 600  # Default height
            
            # Calculate the best fit for the image in the canvas
            img_width, img_height = self.image.size
            width_ratio = canvas_width / img_width
            height_ratio = canvas_height / img_height
            
            # Use the smaller ratio to ensure the entire image fits
            fit_factor = min(width_ratio, height_ratio) * 0.9  # 90% of available space
            
            # Only use fit_factor if it's smaller than the current zoom_factor on initial load
            if self.current_frame_index == 0 and self.zoom_factor == 1.0:
                self.zoom_factor = fit_factor
            
            # Apply zoom factor to the image
            width, height = self.image.size
            new_width = int(width * self.zoom_factor)
            new_height = int(height * self.zoom_factor)
            resized_image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            self.image_tk = ImageTk.PhotoImage(resized_image)
            self.canvas_frame.delete("all")  
            
            # Center the image on the canvas
            x_pos = max(0, (canvas_width - new_width) // 2)
            y_pos = max(0, (canvas_height - new_height) // 2)
            
            self.canvas_frame.create_image(x_pos, y_pos, anchor=ct.NW, image=self.image_tk)
            self.canvas_frame.config(scrollregion=self.canvas_frame.bbox(ct.ALL))
                
    def turn_on(self):
        global resX, resY, camera, converter, fps
        
        # Get the selected COM port from the dropdown
        selected_port = self.com_dropdown.get()
        
        try:
            # Attempt to connect to the first available camera
            camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
            camera.Open()

            # Enable frame rate control
            camera.AcquisitionFrameRateEnable.Value = True
            print("Camera turned on successfully.")
            fps = 30
            camera.AcquisitionFrameRate.Value = fps
            print(camera.AcquisitionFrameRate.Value)
            camera.ExposureTime.SetValue(exposure_int)

            # Setting up camera grabbing for video
            camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            resX = camera.Width.Max
            print(resX)
            resY = camera.Height.Max
            print(resY)

            converter = pylon.ImageFormatConverter()
            converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        
            self.camera_thread = threading.Thread(target=self.update_camera_feed)
            self.camera_thread.daemon = True
            self.camera_thread.start()

        except pylon.RuntimeException as e:
            self.show_warning_popup("No Cameras Connected")

        try:
            # Connect to first available Tic (Motor) Device serial number over USB
            serial_nums = tic.list_connected_device_serial_numbers()
            tic.connect_to_serial_number(serial_nums[0])
        
        except IndexError as e:
            self.show_warning_popup("Motor Not Connected")
        
        try:
            # Serial port configuration - use the selected port from the dropdown
            self.ser = serial.Serial(selected_port, 9600, timeout=1)  # Adjust as needed

            # Create a separate thread for reading serial data
            self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.serial_thread.start()
            print(f"ESP32 Remote Connected Successfully on port {selected_port}!")

        except serial.SerialException as e:
            self.show_warning_popup(f"ESP Remote Not Connected to {selected_port}")
            
    # Function to update the dropdown menu
    def refresh_ports(self):
        port_list = self.get_com_ports()
        if port_list:
            self.com_dropdown.configure(values=port_list)
            self.com_dropdown.set(port_list[0])  # Set first available port
        else:
            self.com_dropdown.configure(values=["No Ports Found"])
            self.com_dropdown.set("No Ports Found")

    # Function to get available COM ports
    def get_com_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    # Function to handle COM port selection
    def connect_to_port(choice):
        print(f"Selected Port: {choice}")  # Replace with actual connection logic

    def browse_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:  # If a folder is selected, update the entry box
            self.path.delete(0, ct.END)
            self.path.insert(0, folder_path)
            self.save_path()

    def save_path(self, event=None):
        """Save the current path using pickle."""
        folder_path = self.path.get().strip()
        if folder_path:  # Save only if the path is not empty
            with open(PERSISTENCE_FILE, "wb") as file:
                pickle.dump(folder_path, file)

    def load_saved_path(self):
        """Load the saved path using pickle if it exists."""
        if os.path.exists(PERSISTENCE_FILE):
            with open(PERSISTENCE_FILE, "rb") as file:
                saved_path = pickle.load(file)
                if saved_path:  # Load only if the file is not empty
                    self.path.insert(0, saved_path)

    def read_serial(self):
        while True:
            try:
                if self.ser.in_waiting > 0:
                    serial_data = self.ser.readline().decode().strip()
                    print("Received serial data:", serial_data)
                    self.process_serial_data(serial_data) 
            
                with camera_lock:
                    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                    grabResult.Release()
                    
            except serial.SerialException as e:
                print(f"SerialException in read_serial: {e}")
                break
                 
    # Function to process serial data received from ESP32
    def process_serial_data(self, data):
        if 'move:' in data:
            move_value = int(data.split('move: ')[1])
            print("Received move value:", move_value)
                
            if move_value in self.button_mapping:
                button = self.button_mapping[move_value]
                button.invoke()  # This will trigger the button's action
            else:
                print("Button ID not found:", move_value)

    # Bind the window's default exit
    def on_close(self):
        self.quit()
        
    # # Function for quitting program
    def quit(self):
        # Stop grabbing and close the camera
        if camera.IsGrabbing():
            camera.StopGrabbing()
            
        camera.Close()
        
        # Close the serial connection
        if self.ser.is_open:
            self.ser.close()
            
        # Terminate the serial reading thread if necessary
        if self.serial_thread.is_alive():
            try:
                self.serial_thread.join(timeout=1)
            except Exception as e:
                print(f"Exception while joining serial thread: {e}")
        
        # Destroy the tkinter window
        self.destroy()
        
        # Exit the program
        os._exit(0)
            
    #Quick Motor Controls (+100um, +10um, -10um, -100um)            
    def button_motor(self, button_text): 
        Speed = 1
        # Determine value for Speed
        um = float(button_text) #button entry
        mm = um/1000

        a1 = int((Speed) * 3200 * 10000) #speed
        b1 = int((mm) * 3200) #distance

        # Load configuration file and apply setting, change if needed
        tic.settings.load_config(self.config_path)
        tic.settings.max_speed = (a1)
        tic.settings.apply()
        

        # - Motion Command Sequence ----------------------------------
        # Zero current motor position
        tic.halt_and_set_position(0)

        # Energize Motor
        tic.energize()
        tic.exit_safe_start()

        # Move to listed positions
        d = 0

        positions = [b1]
        for p in positions:
            tic.set_target_position(p)
            while tic.variables.current_position != tic.variables.target_position:

                sleep(.1)

        # De-energize motor and get error status
        tic.enter_safe_start()
        tic.deenergize()
        #print(tic.variables.error_status)

    # Red light
    def blink(self):
        # Turn the light green (blink on)
        self.canvas.itemconfig(self.light, fill="green")
        self.canvas.update_idletasks()  # Force the canvas to update immediately
        self.after(100, self.turn_off)

    # Grey light
    def turn_off(self):
        # Turn the light back to red (blink off)
        self.canvas.itemconfig(self.light, fill="red")
        self.canvas.update_idletasks()  # Force the canvas to update immediately
        
    # Function for Axial Scan
    def axial(self):
        global exposure_int, video_filename, video_folder
        # Define video recording parameters
        user_video_name = self.name_entry.get()
    
        # Check if folder name is empty
        if not user_video_name:
            self.show_warning_popup("Folder name cannot be empty.")
            return  # Exit the function if folder name is empty
        
        save_folder = self.path.get()
        
        # Check if folder name is empty
        if not save_folder:
            self.show_warning_popup("Folder path cannot be empty. Please select where to save data.")
            return  # Exit the function if folder name is empty
                
        # Specify location of where you want to save the collected date, change if needed. Check if folder exists, add file if not
        video_folder = os.path.join(save_folder, user_video_name)
            
        if not os.path.exists(video_folder):
            os.makedirs(video_folder)
            
        def move_motor(a1, b1):
            # Load configuration file and apply setting, change if needed
            tic.settings.load_config(self.config_path)
            tic.settings.max_speed = a1
            tic.settings.apply()

            # - Motion Command Sequence ----------------------------------
            # Zero current motor position
            tic.halt_and_set_position(0)

            # Energize Motor
            tic.energize()
            tic.exit_safe_start()

            # Move to listed positions
            for p in [b1]:
                tic.set_target_position(p)
                while tic.variables.current_position != tic.variables.target_position:
                    sleep(0.1)
            
            c = int(b1/2)
            # Move to listed positions
            for p in [c]:
                tic.set_target_position(p)
                while tic.variables.current_position != tic.variables.target_position:
                    sleep(0.1)

            # De-energize motor and get error status
            tic.enter_safe_start()
            tic.deenergize()
                    
        # Check if the required entries are provided
        if self.range_entry.get() and self.axial_entry.get():
            try:
                # Extract values from entries
                a = float(self.range_entry.get())  # distance
                b = float(self.axial_entry.get())  # step size

                # Calculate number of frames and speed
                Frames = int(a / b)
                Speed = (b * fps)

                a1 = int(Speed * 3200 * 10000)  # speed
                b1 = int(a * 3200)  # distance
                
                S = 1
                S1 = int((Speed) * 3200 * 10000) #speed
                tic.settings.load_config(self.config_path)
                tic.settings.max_speed = S1
                tic.settings.apply()

                # - Motion Command Sequence ----------------------------------
                # Zero current motor position
                tic.halt_and_set_position(0)

                # Energize Motor
                tic.energize()
                tic.exit_safe_start()
                # m = -150 /1000
                # back = int(m * 3200)
                # c = back
                c = int(-b1/2)
                # Move to listed positions
                for p in [c]:
                    tic.set_target_position(p)
                    while tic.variables.current_position != tic.variables.target_position:
                        sleep(0.1)

                # De-energize motor and get error status
                tic.enter_safe_start()
                tic.deenergize()
                
                if Frames < 0:  # Adjust frames in case of negative direction
                    Frames = -Frames

                # Generate unique filename based on current time
                timestamp = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
                video_filename = f"{timestamp}_ss_{b}_exp_{exposure_int}.avi"

                # Define codec and create VideoWriter object
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                out = cv2.VideoWriter(os.path.join(video_folder, video_filename), fourcc, fps, (resX, resY))
                
                count = 0
                
                # Line below is for debugging
                # t0 = time()
                with camera_lock:  # Acquire the lock before accessing the camera
                    # Start motor movement in a separate thread
                    motor_thread = threading.Thread(target=move_motor, args=(a1, b1))
                    motor_thread.start()
                    
                    # Declare buffer to save video
                    buffer = []
                    while camera.IsGrabbing() and count < Frames:        
                        grabResult = camera.RetrieveResult(50, pylon.TimeoutHandling_ThrowException)

                        if grabResult.GrabSucceeded():
                            image = converter.Convert(grabResult)
                            img = image.GetArray()
                            
                            cv2.imshow("Live Axial Scan", cv2.resize(img, (400, 300)))  # Resize for better performance
                            
                            buffer.append(img)
                            
                            # Line below is for debugging
                            # print(f"Frame {count} captured and added to buffer")
                            count += 1

                        grabResult.Release()
                
                saving_window = self.saving("Saving Data. Please don't touch the GUI!")
                saving_window.update()
                sleep (0.5)
                
                # Function to save the buffer and close saving window
                def save_buffer_and_close():
                    for idx, img in enumerate(buffer):
                        out.write(img)
                        
                    buffer.clear()
                    out.release()
                    cv2.destroyAllWindows()
                    self.saving_window.destroy()  # Close saving window
                
                # Schedule the save_buffer_and_close function to run after 0.5 seconds
                self.after(500, save_buffer_and_close)
                
            except ValueError:
                # Show Error Message for invalid input
                self.show_warning_popup("Invalid input. Please try again!")
        else:
            # Show Error Message for missing entries
            self.show_warning_popup("Please provide all necessary inputs.")

    # Function for confirmation
    def saving(self, note):
        saving = ct.CTkToplevel()
        saving.title("Saving")
        # saving.geometry(f"{300}x{100}")
        
        saving.grab_set()
        
        ok_label = ct.CTkLabel(saving, text=note) 
        ok_label.pack(padx=10, pady=10)
        
        saving.update_idletasks()  # Ensure the window is displayed immediately
        
        # Get the dimensions of the screen and the window
        screen_width = saving.winfo_screenwidth()
        screen_height = saving.winfo_screenheight()
        window_width = saving.winfo_width()
        window_height = saving.winfo_height()

        # Calculate the position to center the window
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = (screen_height // 2) - (window_height // 2)

        # Set the window position to the center of the screen
        saving.geometry(f"{300}x{100}+{x_position}+{y_position}")
        
        # Store the reference to the window
        self.saving_window = saving

        return saving      
        
    # Function for confirmation
    def show_confirmed(self, note):
        confirm = ct.CTkToplevel()
        confirm.title("Confirmation")
        confirm.geometry(f"{300}x{100}")
        
        confirm.grab_set()
        
        ok_label = ct.CTkLabel(confirm, text=note) 
        ok_label.pack(padx=10, pady=10)
        
        ok_button = ct.CTkButton(confirm, text="OK", command=confirm.destroy)
        ok_button.pack(pady=10)
            
    # Function for warning
    def show_warning_popup(self, message):
        popup = ct.CTkToplevel()
        popup.title("Warning")
        popup.geometry(f"{300}x{100}")
        
        popup.grab_set()
        
        label = ct.CTkLabel(popup, text=message) 
        label.pack(padx=10, pady=10)
        
        button = ct.CTkButton(popup, text="OK", command=popup.destroy)
        button.pack(pady=10)
        
    # Function for taking pictures
    def capture_picture(self):
        # Get the folder name from the entry
        user_pic_name = self.name_entry.get()
    
        # Check if folder name is empty
        if not user_pic_name:
            self.show_warning_popup("Folder name cannot be empty.")
            return  # Exit the function if folder name is empty
        
        save_folder = self.path.get()
        
        # Check if folder name is empty
        if not save_folder:
            self.show_warning_popup("Folder path cannot be empty. Please select where to save data.")
            return  # Exit the function if folder name is empty
                
        # Specify location of where you want to save the collected date, change if needed. Check if folder exists, add file if not
        video_folder = os.path.join(save_folder, user_pic_name)
            
        if not os.path.exists(video_folder):
            os.makedirs(video_folder)

        # Generate a unique filename based on the current time
        timestamp = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
        picture_filename = f"{timestamp}.png"

        self.blink()

        # Capture picture and save it
        with camera_lock:  # Acquire the lock before accessing the camera
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                image = converter.Convert(grabResult)
                img = image.GetArray()

                # Apply zoom to the image
                img = cv2.resize(img, (resX, resY))

                # Save the picture in the folder
                cv2.imwrite(os.path.join(video_folder, picture_filename), img)
            grabResult.Release()

    # Function to set fps
    def fps_calculator(self):
        global fps
        default_fps = 30
        fps_value = self.fps_entry.get()

        try:
            if fps_value:
                fps = int(fps_value)
                if fps > 150:
                    self.show_warning_popup("Entered value is more than the max FPS. \n Please enter a valid number.")
                    return
                else:
                    camera.AcquisitionFrameRate.Value = fps
                    print(camera.AcquisitionFrameRate.Value)
                    self.show_confirmed("FPS successfully entered!")
            else:
                # Set a default value for fps if input is empty
                fps = default_fps
        except ValueError:
            self.show_warning_popup("Invalid FPS input. Please enter an integer.")
            return
        
        return 
    
    # Function for taking videos
    def toggle_record_frames(self):
        entry_value_frame = self.record_entry.get()
        try:
            n_frames = int(entry_value_frame)
            user_video_name = self.name_entry.get()
        
            # Check if folder name is empty
            if not user_video_name:
                self.show_warning_popup("Folder name cannot be empty.")
                return  # Exit the function if folder name is empty
            
            save_folder = self.path.get()
            
            # Check if folder name is empty
            if not save_folder:
                self.show_warning_popup("Folder path cannot be empty. Please select where to save data.")
                return  # Exit the function if folder name is empty
                    
            # Specify location of where you want to save the collected date, change if needed. Check if folder exists, add file if not
            video_folder = os.path.join(save_folder, user_video_name)
                
            if not os.path.exists(video_folder):
                os.makedirs(video_folder)

            # Generate a unique filename based on the current time
            timestamp = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
            video_filename = f"{timestamp}_exp_{exposure_int}.avi"

            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(os.path.join(video_folder, video_filename), fourcc, fps, (resX, resY))

            count = 0
            with camera_lock:  # Acquire the lock before accessing the camera
                # Declare buffer to save video
                buffer1 = []
                while camera.IsGrabbing() and count < n_frames:        
                    grabResult = camera.RetrieveResult(50, pylon.TimeoutHandling_ThrowException)

                    if grabResult.GrabSucceeded():
                        image = converter.Convert(grabResult)
                        img = image.GetArray()
                        
                        buffer1.append(img)
                        
                        # Line below is for debugging
                        # print(f"Frame {count} captured and added to buffer")
                        count += 1
                        
                        # Press 'q' to exit early from the loop
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

                    grabResult.Release()
                
            saving_window = self.saving("Saving Data. Please don't touch the GUI!")
            saving_window.update()
            sleep (0.5)
            
            # Function to save the buffer and close saving window
            def save_buffer_and_close():
                for idx, img in enumerate(buffer1):
                    out.write(img)
                    
                buffer1.clear()
                out.release()
                cv2.destroyAllWindows()
                self.saving_window.destroy()  # Close saving window
            
            # Schedule the save_buffer_and_close function to run after 0.5 seconds
            self.after(500, save_buffer_and_close)
                        
        except ValueError:
            self.show_warning_popup("Invalid input. Please enter an integer.")
            return

    # Function to resize zoom factor
    def resize(self, zoom):
        global scale
        scale = float(zoom)  # Ensure scale is a float
        self.zoom_counter.configure(text=f"{scale:.1f}x")  # Update the zoom counter label
        return scale
    
    # Function to update exposure
    def update_exposure_time(self):
        global exposure_int

        entry_value = self.exposure_entry.get()
        
        try: 
            # convert the string to an integer 
            exposure_int = int(entry_value)

            # do something with the integer value 
            camera.ExposureTime.SetValue(exposure_int)

        except ValueError: 
            # handle the case where the string value cannot be converted to an integer 
            self.show_warning_popup("Invalid input. Please enter an integer.")
            return exposure_int

    # White Balance
    def white_balance_trigger(self):
        # Select auto function ROI 2
        camera.AutoFunctionROISelector.Value = "ROI2"
        # Enable the Balance White Auto auto function
        # for the auto function ROI selected
        camera.AutoFunctionROIUseWhiteBalance.Value = True
        # Enable Balance White Auto by setting the operating mode to Continuous
        camera.BalanceWhiteAuto.Value = "Continuous"
        
    # Gain adjustments
    def change_gain(self):
        global gain
        entry_value = self.gain_entry.get()
        
        try: 
            # convert the string to an integer 
            gain = float(entry_value)

            # do something with the integer value 
            camera.GainSelector.Value = "All"
            # Set the gain to 4.2 dB
            camera.Gain.Value = gain

        except ValueError: 
            # handle the case where the string value cannot be converted to an integer 
            self.show_warning_popup("Invalid input. Please enter an integer.")
            return gain
    
    # Function for dark mode
    def change_appearance_mode_event(self, switch_var):
        if switch_var == "off":
            ct.set_appearance_mode("Light")
            self.canvas.config(bg="#f2f2f2", bd=0, highlightthickness=0)
        
        if switch_var == "on":
            ct.set_appearance_mode("Dark")
            self.canvas.config(bg="#1a1a1a", bd=0, highlightthickness=0) 

    def toggle_flip(self):
        self.flip_horizontal = not self.flip_horizontal
        
    def toggle_rotation(self):
        # Cycle through rotation angles: 0 -> 90 -> 180 -> 270 -> 0
        self.rotation_angle = (self.rotation_angle + 90) % 360
        
        # Update frame sizes if needed for 90/270 degree rotations
        if self.rotation_angle in [90, 270]:
            # Swap frame dimensions/weights for better display
            self.camera_frame.grid_configure(padx=5, pady=10)  # Adjust padding
            self.zoom_frame.grid_configure(padx=5, pady=10)
        else:
            # Return to original sizing
            self.camera_frame.grid_configure(padx=10, pady=5)
            self.zoom_frame.grid_configure(padx=10, pady=5)
    
    # Function to update the camera feed in the GUI
    def update_camera_feed(self):
        global LiveH, LiveW, zoom_height, zoom_width
        global scale
        with camera_lock:  # Acquire the lock before accessing the camera
            grabResult = camera.RetrieveResult(1000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                image = converter.Convert(grabResult)
                img = image.GetArray()
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Apply flip first
                if self.flip_horizontal:
                    img = cv2.flip(img, 1)  # 1 for horizontal flip
                
                # Apply rotation
                if self.rotation_angle == 90:
                    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                elif self.rotation_angle == 180:
                    img = cv2.rotate(img, cv2.ROTATE_180)
                elif self.rotation_angle == 270:
                    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                
                # Determine dimensions based on orientation
                divide = 6
                if self.rotation_angle in [90, 270]:
                    # Dimensions are swapped in 90/270 degrees rotation
                    LiveW = int(resY/divide)
                    LiveH = int(resX/divide)
                else:
                    LiveW = int(resX/divide)
                    LiveH = int(resY/divide)
                
                # Resize main image
                imH = cv2.resize(img, (LiveW, LiveH))
                
                img_pil = Image.fromarray(imH)
                imgtk = ct.CTkImage(light_image=img_pil, size=(LiveW, LiveH))
                
                self.feed.configure(image=imgtk)
                self.feed.img = imgtk
                
                # Calculate center and zoom area
                centerX, centerY = int(LiveH/2), int(LiveW/2)
                zoom_factor = scale  # Each step halves the previous ROI
                
                radiusX, radiusY = int((LiveH / zoom_factor) / 2), int((LiveW / zoom_factor) / 2)
                
                # Ensure crop coordinates are valid
                minX = max(0, centerX - radiusX)
                maxX = min(LiveH, centerX + radiusX)
                minY = max(0, centerY - radiusY)
                maxY = min(LiveW, centerY + radiusY)
                
                try:
                    # Crop and resize for zoom window
                    cropped = imH[minX:maxX, minY:maxY]
                    imHN = cv2.resize(cropped, (LiveW // 2, LiveH // 2))
                    
                    imgN_pil = Image.fromarray(imHN)
                    imgtkN = ct.CTkImage(light_image=imgN_pil, size=(LiveW // 2, LiveH // 2))
                    self.zoom.configure(image=imgtkN)
                    self.zoom.img = imgtkN
                    
                except Exception as e:
                    print(f"Error processing zoom: {e}")
                    self.zoom.configure(image=None, text="Zoom Error")
                
            grabResult.Release()
        self.after(50, self.update_camera_feed)   

app = App()
app.mainloop()

# Releasing the resource    
cv2.destroyAllWindows()