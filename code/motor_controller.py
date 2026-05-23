import RPi.GPIO as GPIO

class MotorController:
    def __init__(self, config):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.config = config

        GPIO.setup(config.MOTOR_A_IN1, GPIO.OUT)
        GPIO.setup(config.MOTOR_A_IN2, GPIO.OUT)
        GPIO.setup(config.MOTOR_A_EN, GPIO.OUT)
        GPIO.setup(config.MOTOR_B_IN3, GPIO.OUT)
        GPIO.setup(config.MOTOR_B_IN4, GPIO.OUT)
        GPIO.setup(config.MOTOR_B_EN, GPIO.OUT)

        self.pA = GPIO.PWM(config.MOTOR_A_EN, 1000)
        self.pB = GPIO.PWM(config.MOTOR_B_EN, 1000)
        self.pA.start(0)
        self.pB.start(0)

    def forward(self, speed=40):
        self.stop()
        GPIO.output(self.config.MOTOR_A_IN1, GPIO.HIGH)
        GPIO.output(self.config.MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(self.config.MOTOR_B_IN3, GPIO.HIGH)
        GPIO.output(self.config.MOTOR_B_IN4, GPIO.LOW)
        self.pA.ChangeDutyCycle(speed)
        self.pB.ChangeDutyCycle(speed)

    def backward(self, speed=40):
        self.stop()
        GPIO.output(self.config.MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(self.config.MOTOR_A_IN2, GPIO.HIGH)
        GPIO.output(self.config.MOTOR_B_IN3, GPIO.LOW)
        GPIO.output(self.config.MOTOR_B_IN4, GPIO.HIGH)
        self.pA.ChangeDutyCycle(speed)
        self.pB.ChangeDutyCycle(speed)

    def left(self, speed=40):
        self.stop()
        GPIO.output(self.config.MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(self.config.MOTOR_A_IN2, GPIO.HIGH)
        GPIO.output(self.config.MOTOR_B_IN3, GPIO.HIGH)
        GPIO.output(self.config.MOTOR_B_IN4, GPIO.LOW)
        self.pA.ChangeDutyCycle(speed)
        self.pB.ChangeDutyCycle(speed)

    def right(self, speed=40):
        self.stop()
        GPIO.output(self.config.MOTOR_A_IN1, GPIO.HIGH)
        GPIO.output(self.config.MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(self.config.MOTOR_B_IN3, GPIO.LOW)
        GPIO.output(self.config.MOTOR_B_IN4, GPIO.HIGH)
        self.pA.ChangeDutyCycle(speed)
        self.pB.ChangeDutyCycle(speed)

    def stop(self):
        GPIO.output(self.config.MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(self.config.MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(self.config.MOTOR_B_IN3, GPIO.LOW)
        GPIO.output(self.config.MOTOR_B_IN4, GPIO.LOW)
        self.pA.ChangeDutyCycle(0)
        self.pB.ChangeDutyCycle(0)

    def cleanup(self):
        self.stop()
        self.pA.stop()
        self.pB.stop()
        GPIO.cleanup()
