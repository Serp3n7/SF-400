import network
import socket
import urequests
import time
import ntptime # Standard library for time sync
from machine import Pin, I2C, RTC
from hx711_pio import HX711
from ssd1306 import SSD1306_I2C

# --- CONFIGURATION ---
SSID = "YOUR_WIFI_NAME"
PASSWORD = "YOUR_WIFI_PASSWORD"
API_KEY = "YOUR_CALORIENINJAS_KEY"
CALIBRATION_FACTOR = -7050  # Your calibrated value
GMT_OFFSET = 19800 # 5.5 hours * 3600 seconds (for IST). Change to 0 for UTC.

# --- HARDWARE SETUP ---
i2c = I2C(0, sda=Pin(4), scl=Pin(5))
oled = SSD1306_I2C(128, 64, i2c)

hx = HX711(pd_sck=17, d_out=16)
hx.set_gain(128)
hx.set_time_constant(0.25)
hx.tare()

# --- WIFI & TIME SETUP ---
oled.text("Connecting...", 0, 0)
oled.show()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    time.sleep(1)

# Sync Time with Internet
try:
    ntptime.settime() # Fetches UTC time
    print("Time synced!")
except:
    print("Time sync failed")

ip = wlan.ifconfig()[0]
oled.fill(0)
oled.text(f"IP: {ip}", 0, 0)
oled.show()

# --- CSV LOGGING FUNCTION ---
def log_to_file(food, weight, calories):
    # Adjust for Timezone
    actual_time = time.time() + GMT_OFFSET
    t = time.localtime(actual_time)
    # Format: YYYY-MM-DD, HH:MM
    timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}".format(t[0], t[1], t[2], t[3], t[4])
    
    # Create CSV line: Date, Time, Food, Weight, Calories
    line = f"{timestamp},{food},{weight},{calories}\n"
    
    # Append to file
    with open("food_log.csv", "a") as f:
        f.write(line)
        
# --- NUTRITION API ---
def get_nutrition(query):
    url = "https://api.calorieninjas.com/v1/nutrition?query=" + query.replace(" ", "+")
    headers = {'X-Api-Key': API_KEY}
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

# --- HTML TEMPLATE ---
html_template = """<!DOCTYPE html>
<html>
<head>
 <meta name="viewport" content="width=device-width, initial-scale=1">
 <style>
  body { font-family: sans-serif; text-align: center; padding: 20px; }
  .btn { background-color: #4CAF50; color: white; padding: 15px 32px; text-decoration: none; display: inline-block; font-size: 16px; margin: 10px; border-radius: 8px;}
  .dl-btn { background-color: #008CBA; }
  input[type=text] { padding: 10px; font-size: 16px; width: 80%; }
 </style>
</head>
<body>
  <h1>🥑 Smart Scale</h1>
  <h2>%s g</h2>
  <form action="/calculate" method="get">
    <input type="text" name="food" placeholder="e.g. Apple">
    <br><br>
    <input type="submit" value="Log Calories" class="btn">
  </form>
  
  <p>%s</p>
  
  <hr>
  <a href="/download.csv" class="btn dl-btn">📥 Download Excel File</a>
</body>
</html>
"""

# --- SERVER LOOP ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

last_msg = "Ready to weigh"

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        
        # 1. Get Weight
        raw = hx.read_average(3)
        weight = max(0, int(raw / CALIBRATION_FACTOR))
        
        # 2. Update OLED
        oled.fill(0)
        oled.text(f"{weight}g", 0, 0)
        oled.text(last_msg[:16], 0, 20) # Limit text length
        oled.show()

        # 3. ROUTE: Download CSV
        if "GET /download.csv" in request:
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/csv\n')
            conn.send('Content-Disposition: attachment; filename="food_log.csv"\n\n')
            
            # Send Header if file is new-ish, otherwise just dump file
            try:
                with open("food_log.csv", "r") as f:
                    conn.send(f.read())
            except OSError:
                conn.send("Date,Food,Weight(g),Calories\nNo data yet.")
                
        # 4. ROUTE: Calculate & Log
        elif "GET /calculate" in request:
            try:
                food_part = request.split("food=")[1].split(" ")[0]
                food_name = food_part.replace("+", " ")
                
                cals, name = get_nutrition(f"{weight}g {food_name}")
                
                if name != "Unknown":
                    total_cals = cals # API returns total for that weight
                    log_to_file(name, weight, total_cals)
                    last_msg = f"Saved: {total_cals}kcal"
                else:
                    last_msg = "Food not found"
            except:
                last_msg = "Error"
            
            response = html_template % (weight, last_msg)
            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n')
            conn.send(response)

        # 5. ROUTE: Home Page
        else:
            response = html_template % (weight, last_msg)
            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n')
            conn.send(response)

        conn.close()
        
    except Exception as e:
        print("Error:", e)