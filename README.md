# 🥑 SmartNutriScale: SF-400 IoT Mod

![MicroPython](https://img.shields.io/badge/MicroPython-1.20%2B-blue?logo=python&logoColor=white)
![Hardware](https://img.shields.io/badge/Hardware-Raspberry_Pi_Pico_W-C51A4A?logo=raspberrypi&logoColor=white)
![Status](https://img.shields.io/badge/Status-Functional-brightgreen)

Turn a cheap **SF-400 kitchen scale** into a powerful **IoT Nutrition Tracker**. 

This project replaces the original "dumb" electronics with a **Raspberry Pi Pico W**, enabling Wi-Fi connectivity, automatic calorie lookups via API, and data logging to Excel.

---

## ✨ Features

* **⚖️ High Precision Weighing:** Uses the scale's original strain gauge load cell with an HX711 amplifier.
* **📶 Web Interface:** Host a local web server on the Pico to view weight on your phone.
* **🍎 Smart Calorie Lookup:** Type the food name (e.g., "Banana") on your phone, and the scale fetches calorie data automatically using the **CalorieNinjas API**.
* **📊 Data Logging:** Automatically saves every meal (Time, Food, Weight, Calories) to a `.csv` file on the device.
* **📥 Excel Export:** Download your nutrition log directly from the web interface with one click.
* **📟 OLED Display:** Shows real-time weight, IP address, and status messages.

---

## 🛠️ Hardware Required

| Component | Description |
| :--- | :--- |
| **SF-400 Scale** | Standard cheap kitchen scale (Case + Load Cell used). |
| **Raspberry Pi Pico W** | The brain. Must be the "W" version for Wi-Fi. |
| **HX711 Module** | Amplifier for the load cell. |
| **0.96" OLED** | I2C Display (SSD1306 driver). |
| **Wires & Soldering Iron** | For connecting components. |

---

## 🔌 Wiring Diagram

**Pin Mapping (Pico W)**

| Component | Pin Label | Pico Pin (GP) |
| :--- | :--- | :--- |
| **HX711** | DT (Data) | `GP16` |
| | SCK (Clock) | `GP17` |
| | VCC | `3V3(OUT)` |
| | GND | `GND` |
| **OLED** | SDA | `GP4` |
| | SCL | `GP5` |
| | VCC | `3V3` |
| | GND | `GND` |

> **⚠️ Note:** The HX711 is very sensitive to noise. Keep wires short and avoid crossing the Wi-Fi antenna area of the Pico if possible.

---

## 💻 Software Installation

### 1. Flash MicroPython
Download the latest [MicroPython firmware for Pico W](https://micropython.org/download/rp2-pico-w/) and install it.

### 2. Install Libraries
Upload the following files to the `lib/` folder (or root) of your Pico:
* `ssd1306.py` - [Official Driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py)
* `hx711_pio.py` - **Crucial:** Use the PIO version to prevent reading glitches during Wi-Fi activity.

### 3. Configuration
Open `main.py` and edit the configuration section:

```python
# --- CONFIGURATION ---
SSID = "YOUR_WIFI_NAME"        # Your Wi-Fi Name
PASSWORD = "YOUR_WIFI_PASS"    # Your Wi-Fi Password
API_KEY = "YOUR_API_KEY"       # Get free key from calorieninjas.com
CALIBRATION_FACTOR = -7050     # See Calibration section below
GMT_OFFSET = 19800             # Adjust for your timezone (19800 = IST)