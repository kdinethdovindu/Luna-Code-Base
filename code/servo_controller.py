import time
import threading
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

class ServoController:
    def __init__(self):
        self.i2c = busio.I2C(SCL, SDA)
        self.pca = PCA9685(self.i2c)
        self.pca.frequency = 60

        self.SERVOMIN = 150
        self.SERVOMAX = 600

        self.left_hand = 0
        self.right_hand = 1
        self.neck = 2

    def angle_to_pulse(self, angle):
        return int(self.SERVOMIN + (angle / 180.0) * (self.SERVOMAX - self.SERVOMIN))

    def set_servo_angle(self, channel, angle):
        pulse = self.angle_to_pulse(angle)
        self.pca.channels[channel].duty_cycle = pulse << 4

    def servo_neutral(self):
        self.set_servo_angle(self.left_hand, 90)
        self.set_servo_angle(self.right_hand, 90)
        self.set_servo_angle(self.neck, 90)
        time.sleep(0.5)

    def set_emotion(self, emotion):
        if emotion == 'happy':
            threading.Thread(target=self.servo_neutral).start()
        elif emotion in ['sad', 'angry', 'love', 'excited', 'neutral']:
            threading.Thread(target=self.servo_neutral).start()

    def cleanup(self):
        self.servo_neutral()
        self.pca.deinit()
