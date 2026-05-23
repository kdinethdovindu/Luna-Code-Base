import RPi.GPIO as GPIO

# Updated GPIO pin mapping
LED_PINS = {
    "red": 26,
    "blue": 24,
    "green": 21
}

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup all LED pins as output
for pin in LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def turn_on(color):
    off_all()  # Optional: turn off other LEDs first
    if color in LED_PINS:
        GPIO.output(LED_PINS[color], GPIO.HIGH)
        print(f"{color} LED is ON")
    else:
        print("Invalid color. Use red, blue, or green.")

def off_all():
    for pin in LED_PINS.values():
        GPIO.output(pin, GPIO.LOW)
    print("All LEDs are OFF")

try:
    print("Type 'red', 'blue', 'green' to turn ON a LED, 'off' to turn all OFF, or 'exit' to quit.")
    while True:
        command = input("Enter command: ").strip().lower()
        if command in LED_PINS:
            turn_on(command)
        elif command == "off":
            off_all()
        elif command == "exit":
            off_all()
            print("Exiting...")
            break
        else:
            print("Invalid command. Try red, blue, green, off, or exit.")

finally:
    GPIO.cleanup()

