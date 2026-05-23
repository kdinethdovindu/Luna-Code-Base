import RPi.GPIO as GPIO
import time

# Use physical pin numbering
GPIO.setmode(GPIO.BOARD)

# Define motor control pins
ENA = 22
IN1 = 18
IN2 = 16
IN3 = 11
IN4 = 13
ENB = 15

# Setup pins
motor_pins = [ENA, IN1, IN2, IN3, IN4, ENB]
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

# Set up PWM for ENA and ENB
pwmA = GPIO.PWM(ENA, 1000)  # 1kHz
pwmB = GPIO.PWM(ENB, 1000)

# Start PWM with 100% duty cycle
pwmA.start(100)
pwmB.start(100)

try:
    print("Motors forward")
    # Motor A forward
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    # Motor B forward
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    time.sleep(2)

    print("Motors reverse")
    # Motor A reverse
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    # Motor B reverse
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    time.sleep(2)

    print("Motors stop")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)

finally:
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()
