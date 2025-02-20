"""
@ Date Created: Mon September 25, 2023
@ Author: Maria Carmella Ocaya
    - Last Update: Tue November 26, 2024

@ Copyrights (C) :
    For Pypylon by Basler:
        Copyright (C) 2017-2023 Basler AG
    For Customtkinter:
        Copyright (c) 2023 Tom Schimansky

@ Disclaimer: 
    Check below for the licenses of the libraries above. Redistribution and use of software must meet the conditions of said licenses. Permission is granted, free of charge, to anyone obtaining a copy of the Python script below with no restrictions as long as credit is given to the author. 
    However, author is not responsible for any unmet requirements of the licenses that are associated with the libraries used in this script. 

    Pypylon: https://github.com/basler/pypylon/blob/master/LICENSE
    Customtkinter: https://github.com/TomSchimansky/CustomTkinter/blob/master/LICENSE
    
"""
from tkinter import Label
from tkinter import *
import customtkinter as ct #Tkinter-based library
import cv2
import os
import threading
from datetime import datetime
from pypylon import pylon
from PIL import Image, ImageTk
from pathlib import Path
from time import sleep
from time import time

print(Path.cwd())

# Connecting to the first available camera
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
# camera.Open()

# Initialize the lock
camera_lock = threading.Lock()

# Setting up camera grabbing for video
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

# Global variables for resolution 4:3 (4024 * 3036)
resX = 4024
resY = 3036

# Enable FPS Acquisition, Set Max Frame Rate
camera.AcquisitionFrameRateEnable.Value = True
fps = 30
camera.AcquisitionFrameRate.Value = fps

# Set scale variable for zooming 
scale = 50

# Set deafult exposure value
exposure_int = 1000
camera.ExposureTime.SetValue(exposure_int)

# Directory of the current Python script
current_directory = os.path.dirname(__file__)

name = "Collected Data"

# Create the main user folder in the current directory
user_folder_path = os.path.join(current_directory, name)
os.makedirs(user_folder_path, exist_ok=True)

# Create subfolders inside the user folder
subfolders = ["Recorded Frames", "Picture Frame"]
for subfolder in subfolders:
    os.makedirs(os.path.join(user_folder_path, subfolder), exist_ok=True)


# tkinter 
ct.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ct.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ct.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Basler Sensor")
        self.geometry(f"{1000}x{1000}")

        # Configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # Sidebar frame for the widgets
        self.sidebar_frame = ct.CTkFrame(self)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(15, weight=1)

        self.logo_label = ct.CTkLabel(self.sidebar_frame, text="Basler Sensor", font=ct.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # StringVar for the switch
        self.switch_var = ct.StringVar(value="off")

        # Switch widget (Dark Mode)
        self.appearance_mode_menu = ct.CTkSwitch(self.sidebar_frame, text="Dark Mode",
                                                 command=lambda: self.change_appearance_mode_event(self.switch_var.get()),
                                                 variable=self.switch_var, onvalue="on", offvalue="off")
        self.appearance_mode_menu.grid(row=18, column=0, padx=20, pady=(10, 10), sticky = S)

        # Text box for naming file entry
        self.name_label = ct.CTkLabel(self.sidebar_frame, text="Folder Name:")
        self.name_label.grid(row = 2, column = 0)
        self.name_entry = ct.CTkEntry(self.sidebar_frame)
        self.name_entry.grid(row = 3, column = 0)

        # Text box for time exposure entry
        self.exposure_label = ct.CTkLabel(self.sidebar_frame, text="Exposure Time(us), (Default = 1000 us):")
        self.exposure_label.grid(row = 4, column = 0, sticky = N)
        self.exposure_entry = ct.CTkEntry(self.sidebar_frame)
        self.exposure_entry.grid(row = 5, column = 0, sticky = N)

        # Button for time exposure confirmation   
        self.exposure_entry_button = ct.CTkButton(self.sidebar_frame, text="Enter", command=self.update_exposure_time)
        self.exposure_entry_button.grid(row = 7, column = 0, pady = 10, sticky = N)

        # Text box for fps entry
        self.fps_label = ct.CTkLabel(self.sidebar_frame, text="FPS (Default = 30, Max = 150):")
        self.fps_label.grid(row = 8, column = 0, sticky = N)
        self.fps_entry = ct.CTkEntry(self.sidebar_frame)
        self.fps_entry.grid(row = 9, column = 0, sticky = N)

        # Buttons for fps confirmation
        self.fps_entry_button = ct.CTkButton(self.sidebar_frame, text="Enter", command=self.fps_calculator)
        self.fps_entry_button.grid(row = 10, column = 0, pady = 10, sticky = N)
               
        # Text box for setting the number of frames to capture
        self.frame_count_label = ct.CTkLabel(self.sidebar_frame, text="Number of Frames to Record:")
        self.frame_count_label.grid(row = 11, column = 0)
        self.frame_count_entry = ct.CTkEntry(self.sidebar_frame)
        self.frame_count_entry.grid(row = 12, column = 0)

        # Button for capturing frames confirmation
        self.record_frames_button = ct.CTkButton(self.sidebar_frame, text="Start Recording Frames", command=self.toggle_record_frames)
        self.record_frames_button.grid(row = 13, column = 0,pady = 10)
        
        # Button for capturing pictures
        self.capture_picture_label = ct.CTkLabel(self.sidebar_frame, text="Capture Picture:")
        self.capture_picture_label.grid(row = 14, column = 0)
        self.capture_picture_button = ct.CTkButton(self.sidebar_frame, text="Capture Picture", command=self.capture_picture)
        self.capture_picture_button.grid(row = 15, column = 0, pady = 10, sticky = N)
        
        # Create a canvas to represent the light (used to confirm picture is taken)
        self.canvas = ct.CTkCanvas(self, width=80, height=80)
        self.canvas.place(x = 380, y = 27)
        
        # Create a light for picture taking confirmation     
        self.light = self.canvas.create_oval(16, 16, 64, 64, fill="red")
        
        # State to track the light color (captured = green or idle = red)
        self.is_on = False
        
        # Slider for zooming in and out
        self.zoom_label = ct.CTkLabel(self.sidebar_frame, text="Zoom:")
        self.zoom_label.grid(row = 16, column = 0)
        self.zoom_scale = ct.CTkSlider(self.sidebar_frame, from_= 50, to=1, command=self.resize)
        self.zoom_scale.set(50)  # Set the initial value
        self.zoom_scale.grid(row = 17, column = 0, padx=10)
    
        # Label widget for displaying the camera feed
        self.label = Label(self, width=1006, height=759)
        #self.label = Label(self, width=4024, height=3036)
        self.label.grid(row=0, column=1, rowspan = 3)
      
        # Separate window for zoom        
        self.camera_feed_label = Label (self, width = 503, height= 380, highlightthickness=2)
        self.camera_feed_label.place(x = 380, y = 1000)
        
        # Bind the custom close handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
        # Camera fram rate
        camera.AcquisitionFrameRate.Value = fps

        # Call camera feed
        self.update_camera_feed()
        
    # Bind the window's default exit
    def on_close(self):
        self.quit()
        
    # # Function for quitting program
    def quit(self):
        # Stop grabbing and close the camera
        if camera.IsGrabbing():
            camera.StopGrabbing()
            
        camera.Close()
    
        # Destroy the tkinter window
        self.destroy()
        
        # Exit the program
        os._exit(0)
            
    # Red to green light
    def blink(self):
        # Turn the light green (blink on)
        self.canvas.itemconfig(self.light, fill="green")
        self.canvas.update_idletasks()  # Force the canvas to update immediately
        self.after(100, self.turn_off)

    # Green to Red light
    def turn_off(self):
        # Turn the light back to red (blink off)
        self.canvas.itemconfig(self.light, fill="red")
        self.canvas.update_idletasks()  # Force the canvas to update immediately
          
    # Function for confirmation
    def saving(self, note):
        saving = ct.CTkToplevel()
        saving.title("Saving")
        
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
        folder_name = self.name_entry.get()
        
        # Check if folder name is empty
        if not folder_name:
            self.show_warning_popup("Folder name cannot be empty.")
            return  # Exit the function if folder name is empty

        def find_folder_path(folder):
            for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):  # Starting from GUI directory
                if folder in dirs:
                    return os.path.join(root, folder)  # Use 'folder' instead of 'name'

        folder_name_to_find = "Picture Frame" 
        folder_path = find_folder_path(folder_name_to_find)

        if folder_path is None:
            self.show_warning_popup(f"Folder '{folder_name_to_find}' not found.")
            return  # Exit if the folder isn't found

        # Generate the full path to save the picture
        save_path = os.path.join(folder_path, folder_name)
        if not os.path.exists(save_path):
            os.makedirs(save_path)  # Create the folder if it doesn't exist

        # Generate a unique filename based on the current time
        timestamp = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
        picture_filename = f"{timestamp}.png"
        picture_full_path = os.path.join(save_path, picture_filename)


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
                cv2.imwrite(os.path.join(folder_path, picture_filename), img)
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
                else:
                    camera.AcquisitionFrameRate.Value = fps
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
        entry_value_frame = self.frame_count_entry.get()
        try:
            n_frames = int(entry_value_frame)
            user_video_name = self.name_entry.get()
            
            # Check if folder name is empty
            if not user_video_name:
                self.show_warning_popup("Folder name cannot be empty.")
                return  # Exit the function if folder name is empty

            def find_folder_path(folder_name):
                for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
                    if folder_name in dirs:
                        return os.path.join(root, folder_name)
                return None

            folder_path = find_folder_path("Recorded Frames")
            if folder_path is None:
                self.show_warning_popup("Folder 'Recorded Frames' not found.")
                return

            save_path = os.path.join(folder_path, user_video_name)
            os.makedirs(save_path, exist_ok=True)

            timestamp = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
            video_filename = f"{timestamp}_exp_{exposure_int}.avi"
            video_full_path = os.path.join(save_path, video_filename)

            fourcc = cv2.VideoWriter_fourcc(*'MJPG')  
            out = None  
            count = 0
            buffer1 = []

            # Frame acquisition
            def capture_frames():
                nonlocal count, out  # Use 'out' within the local function
                try:
                    with camera_lock:
                        # t1 = time()
                        while camera.IsGrabbing() and count < n_frames:
                            grabResult = camera.RetrieveResult(50, pylon.TimeoutHandling_ThrowException)
                            if grabResult.GrabSucceeded():
                                image = converter.Convert(grabResult)
                                img = image.GetArray()

                                # Initialize 'out' with frame dimensions on the first frame
                                if count == 0:
                                    height, width = img.shape[:2]
                                    out = cv2.VideoWriter(video_full_path, fourcc, fps, (width, height))

                                buffer1.append(img)
                                count += 1

                                if cv2.waitKey(1) & 0xFF == ord('q'):  # Early exit
                                    break
                            grabResult.Release()
                        # t2 = time()
                        # timer = t2 - t1
                        # print(timer)

                except Exception as e:
                    self.show_warning_popup(f"Camera error: {str(e)}")

            threading.Thread(target=capture_frames, daemon=True).start()

                
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

    # Function to resize
    def resize(self, zoom):
        global scale
        scale = int(zoom)
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

    # Function for dark mode
    def change_appearance_mode_event(self, switch_var):
        if switch_var == "off":
            ct.set_appearance_mode("Light")
            self.canvas.config(bg="#f2f2f2", bd=0, highlightthickness=0)
        
        if switch_var == "on":
            ct.set_appearance_mode("Dark")
            self.canvas.config(bg="#1a1a1a", bd=0, highlightthickness=0) 

    # Function to update the camera feed in the GUI
    def update_camera_feed(self):
        global scale
        with camera_lock:  # Acquire the lock before accessing the camera
            grabResult = camera.RetrieveResult(1000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                image = converter.Convert(grabResult)
                img = image.GetArray()
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                imH = cv2.resize(img, (1006, 759))

                img_pil = Image.fromarray(imH)
                imgtk = ImageTk.PhotoImage(image=img_pil)

                self.label.configure(image=imgtk)
                self.label.img = imgtk

                # scale = 6
                
                #prepare the crop
                centerX,centerY=int(759/2),int(1006/2)
                radiusX,radiusY= int(scale*759/100),int(scale*1006/100)

                minX,maxX=centerX-radiusX,centerX+radiusX
                minY,maxY=centerY-radiusY,centerY+radiusY

                # Zoom in window
                cropped = imH[minX:maxX, minY:maxY]
                imHN = cv2.resize(cropped, (1006, 759)) 

                imgN_pil = Image.fromarray(imHN)
                imgtkN = ImageTk.PhotoImage(image=imgN_pil)
                self.camera_feed_label.configure(image=imgtkN)
                self.camera_feed_label.img = imgtkN

            grabResult.Release()
        self.after(50, self.update_camera_feed)
        
app = App()
app.mainloop()

# Releasing the resource    
cv2.destroyAllWindows()