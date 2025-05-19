# Techin515-Wand

# Magic Wand Project

This project implements a gesture-recognition magic wand using an ESP32, MPU6050 sensor, and Edge Impulse model.

## Features

- Real-time gesture capture
- Trained with Edge Impulse
- On-device inference via ESP32
- 3D-printed pyramid enclosure

## Setup Instructions

### 1. Install Dependencies

Make sure you have the following installed:
- Arduino IDE or PlatformIO
- Python 3.8+
- Required Python packages:
```bash
pip install pyserial

### 2. Upload Arduino Sketch
Go to src/sketches/gesture_capture.ino
Upload the code to your ESP32 using Arduino IDE.

### 3. Run Python Script to Collect Data
Navigate to src/python-scripts and run:

python process_gesture_data.py --gesture A --person yourname
Use 'o' to start capture. Data will be saved as .csv.

### 4. Edge Impulse Training
Upload data to Edge Impulse
Select Spectral Features + Classification Block
Train, test, and deploy model

### 5. Model Deployment
Download C++ deployment from Edge Impulse
Integrate it into your Arduino project (see magic_wand_inference.ino)


