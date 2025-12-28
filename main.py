import network
import socket
import urequests
import time
import ntptime
from machine import Pin, I2C, RTC
from lib.hx711_pio import HX711
from lib.ssd1306 import SSD1306_I2C

# ==========================================
# ⚙️ USER CONFIGURATION
# ==========================================

# 1. Wi-Fi Networks (Add as many as you want)
KNOWN_NETWORKS = {
    "Your_Home_WiFi": "Your_Password",
    "Your_Office_WiFi": "Office_Password",
    "iPhone_Hotspot": "hotspot123"
}

# 2. API Keys
# Get free key from: https://calorieninjas.com/
CALORIE_API_KEY = "YOUR_CALORIENINJAS_KEY_HERE"

# 3. Cloud Integration (Google Sheets)
# Create a webhook at make.com (see README)
WEBHOOK_URL = "https://hook.us1.make.com/YOUR_WEBHOOK_ID_HERE"

# 4. Calibration
# Set to 1 first to find your factor, then update.
CALIBRATION_FACTOR = -7050 

# 5. Settings
GMT_OFFSET = 19800      # 19800 = IST (+5.30). 0 = UTC.
SCREEN_TIMEOUT = 60     # Seconds before screen turns off to save battery

# ==========================================
# 🛠️ HARDWARE SETUP
# ==========================================

# OLED Display (I2C)
i2c = I2C(0, sda=Pin(4), scl=Pin(5))
oled = SSD1306_I2C(128, 64, i2c)

# Load Cell (HX711 PIO)
# DT=GP16, SCK=GP17
hx = HX711(d_out=16, pd_sck=17)
hx.set_gain(128)
hx.set_time_constant(0.25)

# Global Variables
rtc = RTC()
last_activity_time = time.time()
screen_active = True

# ==========================================
# 🌐 NETWORK & TIME FUNCTIONS
# ==========================================

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    oled.fill(0)
    oled.text("Scanning WiFi...", 0, 0)
    oled.show()
    
    # Scan for available networks
    try:
        scan_results = wlan.scan()
        visible_ssids = [s[0].decode('utf-8') for s in scan_results]
    except:
        visible_ssids = []

    # Try to find a match
    for ssid, password in KNOWN_NETWORKS.items():
        if ssid in visible_ssids:
            oled.fill(0)
            oled.text(f"Joining {ssid}...", 0, 0)
            oled.show()
            
            wlan.connect(ssid, password)
            
            # Wait for connection
            max_wait = 15
            while max_wait > 0:
                if wlan.status() == 3: # Connected
                    print(f"Connected to {ssid}")
                    return wlan
                max_wait -= 1
                time.sleep(1)
                
    oled.fill(0)
    oled.text("No WiFi Found!", 0, 0)
    oled.show()
    return None

def sync_time():
    try:
        ntptime.settime()
        print("Time synced via NTP")
    except:
        print("Time sync failed")

def get_timestamp():
    # Returns formatted string: "YYYY-MM-DD HH:MM"
    now = time.time() + GMT_OFFSET
    t = time.localtime(now)
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4])

# ==========================================
# 💾 LOGGING FUNCTIONS
# ==========================================

def get_nutrition(query):
    # Fetch calories from API
    url = "https://api.calorieninjas.com/v1/nutrition?query=" + query.replace(" ", "+")
    headers = {'X-Api-Key': CALORIE_API_KEY}
    try:
        response = urequests.get(url, headers=headers)
        data = response.json()
        response.close()
        if 'items' in data and len(data['items']) > 0:
            item = data['items'][0]
            return item['calories'], item['name']
        return 0, "Unknown"
    except:
        return 0, "Error"

def log_data(food, weight, calories):
    timestamp = get_timestamp()
    
    # 1. Save to Local CSV
    try:
        with open("food_log.csv", "a") as f:
            f.write(f"{timestamp},{food},{weight},{calories}\n")
        print("Saved to CSV")
    except:
        print("CSV Error")

    # 2. Send to Google Sheets (Make.com)
    if "hook.us1.make.com" in WEBHOOK_URL:
        print("Sending to Cloud...")
        safe_food = food.replace(" ", "%20")
        safe_time = timestamp.replace(" ", "%20")
        url = f"{WEBHOOK_URL}?date={safe_time}&food={safe_food}&weight={weight}&calories={calories}"
        try:
            urequests.get(url).close()
            print("Cloud Upload Success")
        except:
            print("Cloud Upload Failed")

# ==========================================
# 🖥️ WEB INTERFACE
# ==========================================

html_template = """<!DOCTYPE html>
<html>
<head>
 <meta name="viewport" content="width=device-width, initial-scale=1">
 <title>Smart Scale</title>
 <style>
  body { font-family: -apple-system, sans-serif; text-align: center; padding: 20px; background: #f4f4f9; }
  .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
  h1 { color: #333; }
  .weight { font-size: 40px; color: #2ecc71; font-weight: bold; }
  input[type=text] { padding: 12px; width: 70%; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }
  .btn { background-color: #2ecc71; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 10px; width: 100%; }
  .dl-btn { background-color: #3498db; margin-top: 20px; }
  .log { color: #555; margin-top: 15px; font-size: 14px; }
 </style>
</head>
<body>
 <div class="card">
  <h1>🥑 Smart Scale</h1>
  <div class="weight">%s g</div>
  
  <form action="/calculate" method="get">
    <input type="text" name="food" placeholder="What are you eating?">
    <button type="submit" class="btn">Log Calories</button>
  </form>
  
  <div class="log">%s</div>
  
  <a href="/download.csv"><button class="btn dl-btn">📥 Download Excel</button></a>
 </div>
</body>
</html>
"""

# ==========================================
# 🚀 MAIN LOOP
# ==========================================

# 1. Setup
hx.tare()
wlan = connect_wifi()
if wlan:
    sync_time()
    ip_address = wlan.ifconfig()[0]
else:
    ip_address = "Offline"

# 2. Start Web Server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)
s.settimeout(0.1) # Non-blocking to allow weighing to happen

last_msg = "Ready"

while True:
    try:
        # --- A. WEIGHING LOGIC ---
        raw = hx.read_average(3)
        weight = max(0, int(raw / CALIBRATION_FACTOR))
        
        # --- B. SCREEN SAVER LOGIC ---
        # If weight changes > 2g, wake up screen
        if abs(weight - (hx.read_average(3)/CALIBRATION_FACTOR)) > 2: 
             last_activity_time = time.time()
             
        if time.time() - last_activity_time > SCREEN_TIMEOUT:
            if screen_active:
                oled.poweroff()
                screen_active = False
        else:
            if not screen_active:
                oled.poweron()
                screen_active = True
            
            # Update Screen
            oled.fill(0)
            oled.text(f"{weight}g", 10, 10)
            oled.text(f"IP: {ip_address}", 0, 50)
            oled.show()

        # --- C. WEB SERVER LOGIC ---
        try:
            conn, addr = s.accept() # Check for connection
            request = conn.recv(1024).decode()
            
            # Reset sleep timer on web activity
            last_activity_time = time.time() 

            # Route: Download CSV
            if "GET /download.csv" in request:
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/csv\nContent-Disposition: attachment; filename="food_log.csv"\n\n')
                try:
                    with open("food_log.csv", "r") as f:
                        conn.send(f.read())
                except:
                    conn.send("Date,Food,Weight,Calories\n")
            
            # Route: Calculate
            elif "GET /calculate" in request:
                try:
                    food_part = request.split("food=")[1].split(" ")[0]
                    food_name = food_part.replace("+", " ")
                    
                    cals, name = get_nutrition(f"{weight}g {food_name}")
                    
                    if name != "Unknown":
                        log_data(name, weight, cals)
                        last_msg = f"Logged: {name} ({cals} kcal)"
                    else:
                        last_msg = "❌ Food not found"
                except:
                    last_msg = "❌ Input Error"
                
                response = html_template % (weight, last_msg)
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n')
                conn.send(response)

            # Route: Home
            else:
                response = html_template % (weight, last_msg)
                conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n')
                conn.send(response)
            
            conn.close()
            
        except OSError:
            pass # No web request received, continue loop

    except Exception as e:
        print("Error in loop:", e)