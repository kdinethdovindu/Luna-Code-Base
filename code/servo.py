# -*- coding: utf-8 -*-
import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

# I2C and PCA9685 setup
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 60

# Constants
SERVOMIN = 150
SERVOMAX = 600

left_hand = 0
right_hand = 1
neck = 2

# --- Helper Functions ---

def map_range(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def angle_to_pulse(angle):
    return int(SERVOMIN + (angle / 180.0) * (SERVOMAX - SERVOMIN))

def set_servo_angle(channel, angle):
    pulse = angle_to_pulse(angle)
    pca.channels[channel].duty_cycle = pulse << 4

def servo_neutral():
    set_servo_angle(left_hand, 90)
    set_servo_angle(right_hand, 90)
    set_servo_angle(neck, 90)
    time.sleep(0.5)

# --- Motion Functions ---

def happy_motion():
    for _ in range(2):
        for angle in range(90, 151, 2):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, angle)
            neck_angle = map_range(angle, 90, 150, 90, 120)
            set_servo_angle(neck, neck_angle)
            time.sleep(0.005)
        for angle in range(150, 59, -2):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, angle)
            neck_angle = map_range(angle, 150, 60, 120, 70)
            set_servo_angle(neck, neck_angle)
            time.sleep(0.005)

def angry_motion():
    for _ in range(2):
        for angle in range(0, 91):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, 180 - angle)
            time.sleep(0.001)
        for angle in range(90, -1, -1):
            set_servo_angle(left_hand, angle)
            set_servo_angle(right_hand, 180 - angle)
            time.sleep(0.001)
    neck_side_to_side_angry(120, 60, 2)

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
            time.sleep(0.01)
        for angle in range(left_angle, right_angle - 1, -1):
            set_servo_angle(neck, angle)
            time.sleep(0.01)
        for angle in range(right_angle, 91):
            set_servo_angle(neck, angle)
            time.sleep(0.01)

def neck_side_to_side_sad(left_angle, right_angle, cycles):
    for _ in range(cycles):
        for angle in range(90, left_angle + 1):
            set_servo_angle(neck, angle)
            time.sleep(0.03)
