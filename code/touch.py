import RPi.GPIO as GPIO
import time

TOUCH_PIN = 4  # GPIO 4

GPIO.setmode(GPIO.BCM)
GPIO.setup(TOUCH_PIN, GPIO.IN)

print("Waiting for touch...")

try:
    while True:
        if GPIO.input(TOUCH_PIN) == GPIO.HIGH:
            print("Touch detected!")
            # Wait until touch is released to avoid repeated prints
            while GPIO.input(TOUCH_PIN) == GPIO.HIGH:
                time.sleep(0.01)
        time.sleep(0.01)  # Small delay to reduce CPU usage
except KeyboardInterrupt:
    print("Exiting...")

