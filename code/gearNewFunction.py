import RPi.GPIO as GPIO
from time import sleep

# Motor A (left)
in1 = 24
in2 = 23
enA = 25

# Motor B (right)
in3 = 17
in4 = 27
enB = 22

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup([in1, in2, enA, in3, in4, enB], GPIO.OUT)

# Initial motor states
GPIO.output(in1, GPIO.LOW)
GPIO.output(in2, GPIO.LOW)
GPIO.output(in3, GPIO.LOW)
GPIO.output(in4, GPIO.LOW)

# PWM setup
pA = GPIO.PWM(enA, 1000)
pB = GPIO.PWM(enB, 1000)
pA.start(50)  # Set to medium speed
pB.start(50)

# Direction flag
direction = 1

# --- Movement Functions ---
def stop():
    print("Stopping")
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.LOW)

def forward():
    global direction
    print("Forward for 3 seconds")
    GPIO.output(in1, GPIO.HIGH)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.HIGH)
    GPIO.output(in4, GPIO.LOW)
    direction = 1
    sleep(3)
    stop()

def backward():
    global direction
    print("Backward for 3 seconds")
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.HIGH)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.HIGH)
    direction = 0
    sleep(3)
    stop()

def run():
    print("Running")
    if direction == 1:
        forward()
    else:
        backward()


def gentle_left():
    print("Gentle Turn Left for 0.5 seconds")
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.HIGH)
    GPIO.output(in4, GPIO.LOW)
    sleep(3)
    stop()

    
def gentle_right():
    print("Gentle Turn Right for 0.5 seconds")
    GPIO.output(in1, GPIO.HIGH)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.LOW)
    sleep(3)
    stop()

    # --- Main Loop ---
print("\nDefault: MEDIUM speed (60%), FORWARD direction.")
print("Commands: r s f b tl tr e\n")

try:
    while True:
        x = input("Enter command: ").strip().lower()

        if x == 'r':
            run()
        elif x == 's':
            stop()
        elif x == 'f':
            forward()
        elif x == 'b':
            backward()
        elif x == 'tl':
            gentle_left()
        elif x == 'tr':
            gentle_right()
        elif x == 'e':
            print("Exiting...")
            GPIO.cleanup()
            break
        else:
            print("<<< Invalid Command >>>\nTry: r s f b tl tr e")

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nInterrupted by user. GPIO cleaned up.")
