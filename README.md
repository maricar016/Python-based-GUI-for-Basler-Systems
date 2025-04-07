# Python-based-GUI-for-Basler-Systems
This program was developed for the Translational Optical Imaging (TOI) Laboratory in the University of Arizona. This program allows the user to view live data collection from any Basler sensors. Different versions of this program also allow users to integrate a motor driven by Pololu motor drivers and an ESP32-based remote.

To start, it is highly recommended to visit the Github pages of the following libraries:
* customtkinter by TomSchimansky: https://github.com/TomSchimansky/CustomTkinter
  - customtkiner is the main UI library for this software
* pytic by Allen Institute: https://github.com/AllenInstitute/pytic
  - pytic is the Python wrapper for Pololu motors, which is the main motor driver for TOI's handheld microscopes
* pypylon by Basler: https://github.com/basler/pypylon
  - pypylon is the Python wrapper for Basler cameras

Please follow the installation instructions for these libraries in their corresponding repositories. 

## ESP32-based Remote:
The TOI lab focuses on the development of handheld microscopes. Due to the nature of biomedical imaging, slight movements affect the data quality and speed. Before the development of this remote, all controls regarding the motors in the microscopes were controlled only through the GUI within the computer, making it difficult to avoid sudden movements. 

As a solution, an ESP32-based remote was created. This remote was designed to become part of the microscope's hardware, allowing the users to control the motors from the device itself. For this project, the ESP32-s3 feather was used. However, any ESP32-based microcontroller will work as long as the GPIO pins match exactly as the schematic.

### ESP32 Remote Schematic:

![ESP32 Basler Remote Schematic](https://github.com/user-attachments/assets/1c0c8f9e-fa08-446b-89b8-8071eaa19b44)

### ESP32 Remote (Soldered):
<img src="https://github.com/user-attachments/assets/6d429a93-7bca-4ef5-90bb-edb98fb11a9b" width=30% height=30%> <img src="https://github.com/user-attachments/assets/c878097d-0d3b-412b-84f3-9a1325f4649c" width=30% height=30%>

### ESP32 Materials: 
 _Links are provided as to where it was purchased:_
  * ESP32-s3 feather: https://www.adafruit.com/product/5323
  * Buttons: https://www.adafruit.com/product/1009
  * PCB Prototype (for final version): https://a.co/d/ekKden7
  * Solder: any hardware store/ online
  * Breadboard and m-m jumper wires (to test/prototype): any Arduino kits/ prototyping kits
    
### ESP32 Remote Arduino Code
The ESP32 Arduino code can be found in the ESP32 Remote folder. Simply upload this code to the ESP32 and check if pressing the buttons print its corresponding folder. After uploading your Arduino code, check in the Arduino IDE the COM PORT number when your ESP32 is connected to your computer. You will need to change the PORT number in the Python script to match the one in the Arduino IDE. Please keep in mind that plugging your ESP32 to a different USB port will result to a different COM PORT number, which requires the user to change the Python script to accomodate this change. COM PORT number will also change when using different computers. 

## Pololu Motor Driver:
For the Pololu motor driver, the config.yml file was developed specifically for the use of handheld microscopes. You can develop your own config.yml file by following the instructions provided in the pytic github. This config.yml file was not made by the author of this repository.

## Python GUI:

![basler gui](https://github.com/user-attachments/assets/e3085127-e2fb-47d8-97e1-77774bf520ea)

## Python - ESP32 Remote Communication:

![python_remote](https://github.com/user-attachments/assets/c850ced8-de75-4393-944c-444550a80690)

## Latest GUI Version:

![Screenshot 2025-03-18 144653](https://github.com/user-attachments/assets/714ac296-a9eb-4daf-8335-1fc9e9ce0d8f)
