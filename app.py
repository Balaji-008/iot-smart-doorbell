from flask import Flask, render_template, Response
from gpiozero import Button, Servo
import signal
import sys
import time
import requests
import cv2
from picamera2 import Picamera2

# Setup
button = Button(17)     # Your doorbell button
servo = Servo(18)       # Your door lock servo (adjust pin if needed)
camera = Picamera2()    # Start Pi camera
camera.configure(camera.create_video_configuration())
camera.start()

app = Flask(__name__)

# --- GPIO Cleanup ---
def cleanup_gpio(signal_received, frame):
    print("\n[INFO] Cleaning up GPIO and exiting.")
    button.close()
    servo.close()
    camera.close()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup_gpio)
signal.signal(signal.SIGTERM, cleanup_gpio)

# --- Video Streaming Function ---
def generate_frames():
    while True:
        frame = camera.capture_array()
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/lock')
def lock():
    servo.min()  # Move servo to locked position
    return "Door Locked!"

@app.route('/unlock')
def unlock():
    servo.max()  # Move servo to unlocked position
    return "Door Unlocked!"

# --- Button Press Event (Doorbell Notification) ---
def doorbell_pressed():
    print("[NOTIFICATION] Doorbell Pressed!")
    send_telegram_message("🚪 Ding Dong! Someone pressed the doorbell. URL http://192.168.48.169:5000")

def send_telegram_message(message):
    bot_token = 'xxxxx'  # Redacted — replace with your Telegram Bot token
    chat_id = 'xxxxx'    # Redacted — replace with your Telegram Chat ID
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    requests.post(url, data=payload)

button.when_pressed = doorbell_pressed

# --- Main Start ---
if __name__ == '__main__':
    app.run(host='0.0.0.0')
