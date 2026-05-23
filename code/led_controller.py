import RPi.GPIO as GPIO
import time
import threading

class LEDController:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Example pins, change as per your wiring
        self.RED_PIN = 4
        self.GREEN_PIN = 5
        self.BLUE_PIN = 6

        GPIO.setup(self.RED_PIN, GPIO.OUT)
        GPIO.setup(self.GREEN_PIN, GPIO.OUT)
        GPIO.setup(self.BLUE_PIN, GPIO.OUT)

        self.red = GPIO.PWM(self.RED_PIN, 100)
        self.green = GPIO.PWM(self.GREEN_PIN, 100)
        self.blue = GPIO.PWM(self.BLUE_PIN, 100)

        self.red.start(0)
        self.green.start(0)
        self.blue.start(0)

    def _set_color(self, r, g, b):
        self.red.ChangeDutyCycle(100 - r)
        self.green.ChangeDutyCycle(100 - g)
        self.blue.ChangeDutyCycle(100 - b)

    def set_emotion(self, emotion):
        if emotion == "neutral":
            self._set_color(0, 0, 100)
        elif emotion == "happy":
            self._set_color(0, 100, 0)
        elif emotion == "sad":
            self._set_color(0, 0, 100)
        elif emotion == "angry":
            self._set_color(100, 0, 0)
        elif emotion == "love":
            self._set_color(100, 0, 100)
        elif emotion == "surprise":
            self._set_color(100, 100, 0)

    def music(self):
        threading.Thread(target=self._color_cycle, daemon=True).start()

    def _color_cycle(self):
        while True:
            for r, g, b in [(100, 0, 0), (0, 100, 0), (0, 0, 100)]:
                self._set_color(r, g, b)
                time.sleep(0.3)

    def stop_music(self):
        self.set_emotion("neutral")

    def turn_off(self):
        self._set_color(0, 0, 0)

    def cleanup(self):
        self.turn_off()
        GPIO.cleanup([self.RED_PIN, self.GREEN_PIN, self.BLUE_PIN])
