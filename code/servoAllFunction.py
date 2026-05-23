# -*- coding: utf-8 -*-
import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

# Setup I2C and PCA9685
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 60

# Servo configuration
SERVOMIN = 150   # Pulse for 0 degrees
SERVOMAX = 600   # Pulse for 180 degrees

# Servo channels
left_hand = 0
right_hand = 1
neck = 2

# --- Helper Functions ---

# Map function (like Arduino's map())
def map_range(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# Convert angle (0º180) to PWM pulse
def angle_to_pulse(angle):
    return int(SERVOMIN + (angle / 180.0) * (SERVOMAX - SERVOMIN))

# Set servo angle for a specific channel
def set_servo_angle(channel, angle):
    pulse = angle_to_pulse(angle)
    pca.channels[channel].duty_cycle = pulse << 4  # Convert to 16-bit

# Move servos to neutral (90 degrees)
def servo_neutral():
    set_servo_angle(left_hand, 90)
    set_servo_angle(right_hand, 90)
    set_servo_angle(neck, 90)
    time.sleep(0.5)

# --- Motion Functions (No Neutral Call Inside) ---

def happy_motion():
    for _ in range(3):
        for angle in range(90, 151, 2):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, angle)
            neck_angle = map_range(angle, 90, 150, 90, 120)
            set_servo_angle(neck, neck_angle)
            time.sleep(0.005)

        time.sleep(0.2)

        for angle in range(150, 59, -2):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, angle)
            neck_angle = map_range(angle, 150, 60, 120, 70)
            set_servo_angle(neck, neck_angle)
            time.sleep(0.005)

        time.sleep(0.2)

def angry_motion():
    for _ in range(3):
        for angle in range(0, 91):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, 180 - angle)
            time.sleep(0.001)
        for angle in range(90, -1, -1):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, 180 - angle)
            time.sleep(0.001)

    neck_side_to_side_angry(120, 60, 3)

def hands_and_neck_sad_motion(down_angle, neck_angle, cycles):
    for _ in range(cycles):
        for angle in range(90, down_angle + 1):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, angle)
            neck_map = map_range(angle, 90, down_angle, 90, neck_angle)
            set_servo_angle(neck, neck_map)
            time.sleep(0.015)

        for angle in range(down_angle, 89, -1):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, angle)
            neck_map = map_range(angle, down_angle, 90, neck_angle, 90)
            set_servo_angle(neck, neck_map)
            time.sleep(0.015)

def neck_side_to_side_angry(left_angle, right_angle, cycles):
    for _ in range(cycles):
        for angle in range(90, left_angle + 1):
            set_servo_angle(neck, angle)
            time.sleep(0.01)  # Add delay here
        for angle in range(left_angle, right_angle - 1, -1):
            set_servo_angle(neck, angle)
            time.sleep(0.01)  # Add delay here
        for angle in range(right_angle, 91):
            set_servo_angle(neck, angle)
            time.sleep(0.01)  # Add delay here

def neck_side_to_side_sad(left_angle, right_angle, cycles):
    for _ in range(cycles):
        for angle in range(90, left_angle + 1):
            set_servo_angle(neck, angle)
            time.sleep(0.03)
        for angle in range(left_angle, right_angle - 1, -1):
            set_servo_angle(neck, angle)
            time.sleep(0.03)
        for angle in range(right_angle, 91):
            set_servo_angle(neck, angle)
            time.sleep(0.03)

# --- Additional Movement Function (for walking) ---




def wave_both_hands(cycles=7):
    """
    Waves both hands simultaneously and returns to neutral position after.
    """
    print("Performing: Wave Both Hands")

    for _ in range(cycles):
        # Raise both hands smoothly
        for angle in range(90, 151, 1):  # 90 to 150 (more lift, smoother)
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, angle)
            time.sleep(0.015)  # slower movement

        # Lower both hands smoothly
        for angle in range(150, 89, -1):  # 150 to 90
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, angle)
            time.sleep(0.015)







# --- Emotion Functions (With Neutral Return) ---

def perform_happy():
    print("Performing: Happy")
    happy_motion()
    servo_neutral()

def perform_angry():
    print("Performing: Angry")
    angry_motion()
    servo_neutral()

def perform_sad():
    print("Performing: Sad")
    hands_and_neck_sad_motion(120, 100, 3)
    time.sleep(0.2)
    neck_side_to_side_sad(110, 70, 1)
    servo_neutral()

# --- Main Loop ---

try:
    while True:
        perform_happy()
        time.sleep(2)

        perform_angry()
        time.sleep(2)

        perform_sad()
        time.sleep(2)

        wave_both_hands(2)
        time.sleep(2)

except KeyboardInterrupt:
    print("Interrupted. Returning to neutral and exiting.")
    servo_neutral()
    pca.deinit()
