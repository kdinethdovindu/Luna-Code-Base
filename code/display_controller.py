import time
import threading
from PIL import Image, ImageDraw
import adafruit_rgb_display.st7789 as st7789
import digitalio
import board
import busio


class RoboEyes:
    def __init__(self):
        try:
            # Setup SPI display
            self.spi = board.SPI()
            self.cs_pin = digitalio.DigitalInOut(board.CE0)
            self.dc_pin = digitalio.DigitalInOut(board.D25)
            self.reset_pin = digitalio.DigitalInOut(board.D24)

            self.display = st7789.ST7789(
                self.spi,
                cs=self.cs_pin,
                dc=self.dc_pin,
                rst=self.reset_pin,
                baudrate=64000000,
                width=240,
                height=240,
                x_offset=0,
                y_offset=0
            )

            self.width = self.display.width
            self.height = self.display.height
            self.image = Image.new("RGB", (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)
            self.current_mood = "neutral"
            self.lock = threading.Lock()
        except Exception as e:
            print(f"[Display] Init failed: {e}")

    def set_mood(self, mood):
        with self.lock:
            self.current_mood = mood

    def update(self):
        try:
            with self.lock:
                self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
                if self.current_mood == "neutral":
                    self.draw.text((80, 110), "o o", fill=(0, 0, 255))
                elif self.current_mood == "love":
                    self.draw.text((70, 110), "<3 <3", fill=(255, 0, 0))
                elif self.current_mood == "happy":
                    self.draw.text((80, 110), "^ ^", fill=(255, 255, 0))
                elif self.current_mood == "sad":
                    self.draw.text((80, 110), "u u", fill=(0, 0, 255))
                elif self.current_mood == "angry":
                    self.draw.text((80, 110), "> <", fill=(255, 0, 0))
                elif self.current_mood == "surprise":
                    self.draw.text((80, 110), "O O", fill=(255, 255, 255))

            self.display.image(self.image)
        except Exception as e:
            print(f"[Display] Update failed: {e}")

    def cleanup(self):
        try:
            self.set_mood("neutral")
        except:
            pass
