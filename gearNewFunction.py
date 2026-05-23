import RPi.GPIO as GPIO
import time
from config import Config

class MotorController:
    def __init__(self):
        # Motor A
        self.in1 = 24
        self.in2 = 23
        self.enA = 25

        # Motor B
        self.in3 = 17
        self.in4 = 27
        self.enB = 22

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([self.in1, self.in2, self.enA, self.in3, self.in4, self.enB], GPIO.OUT)

        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.LOW)

        self.pA = GPIO.PWM(self.enA, 1000)
        self.pB = GPIO.PWM(self.enB, 1000)

        self.pA.start(80)  # Medium speed
        self.pB.start(80)

    def stop(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.LOW)

    def forward(self):
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.HIGH)
        GPIO.output(self.in4, GPIO.LOW)
        time.sleep(Config.MOTOR_RUN_DURATION)
        self.stop()

    def backward(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.HIGH)
        time.sleep(Config.MOTOR_RUN_DURATION)
        self.stop()

    def turn_left(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.HIGH)
        GPIO.output(self.in4, GPIO.LOW)
        time.sleep(Config.MOTOR_RUN_DURATION)
        self.stop()

    def turn_right(self):
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.LOW)
        time.sleep(Config.MOTOR_RUN_DURATION)
        self.stop()
