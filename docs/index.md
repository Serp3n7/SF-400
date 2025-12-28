# 🥑 SmartNutriScale: SF-400 IoT Mod

![MicroPython](https://img.shields.io/badge/MicroPython-1.20%2B-blue?logo=python&logoColor=white)
![Hardware](https://img.shields.io/badge/Hardware-Raspberry_Pi_Pico_W-C51A4A?logo=raspberrypi&logoColor=white)
![Status](https://img.shields.io/badge/Status-Functional-brightgreen)

Turn a cheap **SF-400 kitchen scale** into a powerful **IoT Nutrition Tracker**. 

This project replaces the original "dumb" electronics with a **Raspberry Pi Pico W**, enabling intelligent Wi-Fi connectivity, automatic calorie lookups via API, and instant data logging to **Google Sheets**.

---

## ✨ Features

* **⚖️ Precision Weighing:** Uses `hx711_pio` for stable, jitter-free readings while using Wi-Fi.
* **📶 Smart Roaming:** Automatically connects to the best available network (Home, Office, Hotspot).
* **☁️ Google Sheets Sync:** Logs every meal to the cloud automatically via Make.com.
* **📂 Local Backup:** Saves a downloadable `.csv` file directly on the Pico.
* **🔋 Battery Saver:** Auto-sleeps the OLED screen after 60 seconds of inactivity.
* **🇮🇳 Localized:** Pre-configured for IST (Indian Standard Time), but easily adjustable.

---

## 🛠️ Hardware Required

| Component | Description |
| :--- | :--- |
| **SF-400 Scale** | The donor chassis and load cell. |
| **Raspberry Pi Pico W** | The brain (Must be 'W' version for Wi-Fi). |
| **HX711 Module** | Load cell amplifier. |
| **0.96" OLED Display** | I2C (128x64 pixels). |
| **TP4056 Charger + LiPo** | (Optional) For making it rechargeable. |

---

## 🔨 Phase 1: The Surgery (Hardware Mod)

Before wiring, you must prepare the SF-400 chassis.

1.  **Open the Scale:** Remove the screws on the back and open the casing.
2.  **Remove the LCD:** Desolder or peel off the original LCD ribbon cable. It is not compatible.
3.  **Prepare the Buttons:**
    * The original buttons connect to a black "blob" chip. You must **cut the copper traces** on the PCB that lead to this blob to isolate the buttons.
    * Solder thin wires directly to the exposed copper pads of the buttons (TARE, MODE, ON/OFF).
    * Connect the *other* side of the button pads to a common Ground (GND).
4.  **Fit the OLED:** The 0.96" OLED fits perfectly in the original screen window. Secure it with hot glue.

---

## 🔌 Phase 2: Wiring Diagram



### 1. Main Components
| Component | Pin Label | Pico Pin (GP) | Function |
| :--- | :--- | :--- | :--- |
| **HX711** | DT (Data) | `GP16` | Load Cell Data |
| | SCK (Clock) | `GP17` | Load Cell Clock |
| | VCC | `3V3(OUT)` | Power (Do NOT use 5V) |
| | GND | `GND` | Ground |
| **OLED** | SDA | `GP4` | Display Data |
| | SCL | `GP5` | Display Clock |
| | VCC | `3V3` | Power |
| | GND | `GND` | Ground |

### 2. Battery (Rechargeable Mod)
* **LiPo Battery:** Connect to `B+` and `B-` on TP4056 module.
* **TP4056 Output:** Connect `OUT+` to a **Slide Switch**, then to Pico `VSYS` (Pin 39).
* **Ground:** Connect `OUT-` to Pico `GND` (Pin 38).

---

## 💻 Phase 3: Software Installation

1.  **Flash MicroPython:** Download the latest `.uf2` file for [Pico W](https://micropython.org/download/rp2-pico-w/) and drag it onto the Pico.
2.  **Install Drivers:** Save these two files to your Pico's `lib` folder (or root):
    * `hx711_pio.py` ([Download](https://github.com/robert-hh/hx711)) - *Crucial for Wi-Fi stability.*
    * `ssd1306.py` ([Download](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py))
3.  **Upload Code:** Save the provided `main.py` to the Pico.

---

## ⚙️ Phase 4: Configuration

Open `main.py` and edit the top section:

```python
# 1. Wi-Fi (Add as many as you need)
KNOWN_NETWORKS = {
    "Home_WiFi": "password123",
    "Office_WiFi": "securepass",
    "iPhone_Hotspot": "travel123"
}

# 2. Get your free key from Calorieninjas.com
CALORIE_API_KEY = "YOUR_API_KEY_HERE"

# 3. Your Make.com Webhook (See Phase 5)
WEBHOOK_URL = "[https://hook.us1.make.com/](https://hook.us1.make.com/)..."