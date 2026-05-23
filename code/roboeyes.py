import time
import random
import math
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont, ImageOps
from adafruit_rgb_display import ili9341

# Display dimensions for landscape mode
WIDTH = 320
HEIGHT = 240

# Setup pins and SPI for ILI9341 display
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D6)
reset_pin = digitalio.DigitalInOut(board.D13)
spi = board.SPI()

# Create display in landscape mode (rotation = 0)
disp = ili9341.ILI9341(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    width=WIDTH,
    height=HEIGHT,
    rotation=180
)

# Mood color definitions
MOOD_COLORS = {
    "happy": (0, 223, 255),
    "sad": (34, 34, 178),
    "angry": (255, 69, 0),
    "love": (147, 20, 255),
    "neutral": (240, 255, 230),
    "excited": (0, 255, 255)
}

class RoboEyes:
    def __init__(self, display):
        self.disp = display
        self.width = WIDTH
        self.height = HEIGHT
        self.image = Image.new("RGB", (self.width, self.height), "black")
        self.draw_obj = ImageDraw.Draw(self.image)

        self.eye_w = 110
        self.eye_h = 110
        self.eye_spacing = 30
        self.eye_radius = 18

        total_eye_width = 2 * self.eye_w + self.eye_spacing
        start_x = (self.width - total_eye_width) // 2
        y_pos = (self.height - self.eye_h) // 2
        self.left_eye_pos = (start_x, y_pos)
        self.right_eye_pos = (start_x + self.eye_w + self.eye_spacing, y_pos)

        self.mood = "neutral"
        self.blinking = False
        self.auto_blink = False

        self.blink_direction = 0
        self.blink_progress = 0.0
        self.blink_speed = 0.005
        self.blink_hold_time = 0.03
        self.blink_hold_timer = 0

        self.last_blink = time.monotonic()
        self.next_blink_time = time.monotonic() + random.uniform(8, 16)

        self.frame_interval = 0.05
        self.last_frame = 0

        self.vertical_offset = 0
        self.scale_factor = 1.0
        self.animation_phase = 0.0

        self.eye_x_offset = 0
        self.eye_y_offset = 0
        self.next_neutral_shift_time = time.monotonic() + random.uniform(2, 5)
        self.neutral_shift_duration = 0.5
        self.neutral_shift_start_time = 0

    def set_mood(self, mood):
        self.mood = mood

    def blink(self):
        if not self.blinking:
            self.blinking = True
            self.blink_direction = 1
            self.blink_progress = 0.0
            self.blink_speed = random.uniform(0.003, 0.008)

    def toggle_auto_blink(self):
        self.auto_blink = not self.auto_blink

    def mood_color(self):
        return MOOD_COLORS.get(self.mood, (0, 0, 255))

    def draw(self):
        self.image.paste((0, 0, 0), [0, 0, self.width, self.height])
        self._draw_eye(self.draw_obj, self.left_eye_pos, True)
        self._draw_eye(self.draw_obj, self.right_eye_pos, False)
        self.disp.image(self.image)

    def _draw_heart(self, draw, cx, cy, size, fill_color):
        scale = 0.05
        points = []
        for t in range(0, 360, 5):
            angle = math.radians(t)
            x = size * 16 * (math.sin(angle) ** 3)
            y = -size * (13 * math.cos(angle) - 5 * math.cos(2 * angle) -
                         2 * math.cos(3 * angle) - math.cos(4 * angle))
            points.append((cx + int(x * scale), cy + int(y * scale)))
        draw.polygon(points, fill=fill_color)

    def _draw_star(self, draw, cx, cy, size, fill_color):
        points = []
        for i in range(5):
            angle_outer = math.radians(i * 72 - 90)
            angle_inner = math.radians(i * 72 + 36 - 90)
            points.append((cx + size * math.cos(angle_outer),
                           cy + size * math.sin(angle_outer)))
            points.append((cx + size * 0.5 * math.cos(angle_inner),
                           cy + size * 0.5 * math.sin(angle_inner)))
        draw.polygon(points, fill=fill_color)

    def _draw_eye(self, draw, pos, is_left):
        x, y = pos
        y += self.vertical_offset

        scale = self.scale_factor
        eye_w = int(self.eye_w * scale)
        eye_h = int(self.eye_h * scale)
        eye_x = x + (self.eye_w - eye_w) // 2
        eye_y = y + (self.eye_h - eye_h) // 2

        b, g, r = self.mood_color()
        color = (r, g, b)

        offset_x = self.eye_x_offset if self.mood == "neutral" else 0
        offset_y = self.eye_y_offset if self.mood == "neutral" else 0

        cx = eye_x + eye_w // 2 + offset_x
        cy = eye_y + eye_h // 2 + offset_y
        size = min(eye_w, eye_h) // 2

        if self.mood not in ("love", "excited"):
            draw.rounded_rectangle(
                (eye_x, eye_y, eye_x + eye_w, eye_y + eye_h),
                radius=self.eye_radius,
                fill=color
            )

        if self.blinking:
            max_lid_height = eye_h // 2
            lid_height = int(max_lid_height * self.blink_progress)
            slit_height = 4
            if lid_height * 2 > eye_h - slit_height:
                lid_height = (eye_h - slit_height) // 2
            draw.rectangle((eye_x, eye_y, eye_x + eye_w, eye_y + lid_height), fill="black")
            draw.rectangle((eye_x, eye_y + eye_h - lid_height, eye_x + eye_w, eye_y + eye_h), fill="black")
            return

        if self.mood == "love":
            self._draw_heart(draw, cx, cy, size + 10, (193, 182, 255))
        elif self.mood == "excited":
            self._draw_star(draw, cx, cy, size, (0, 255, 255))
        elif self.mood == "sad":
            self._draw_sad_eye(draw, eye_x, eye_y, is_left)
        elif self.mood == "angry":
            self._draw_angry_eye(draw, eye_x, eye_y, is_left)
        elif self.mood == "happy":
            self._draw_happy_eye(draw, eye_x, eye_y)

    def _draw_sad_eye(self, draw, x, y, is_left):
        if is_left:
            draw.polygon([(x, y), (x + self.eye_w, y), (x, y + self.eye_h // 2)], fill="black")
        else:
            draw.polygon([(x, y), (x + self.eye_w, y), (x + self.eye_w, y + self.eye_h // 2)], fill="black")

    def _draw_angry_eye(self, draw, x, y, is_left):
        if is_left:
            draw.polygon([(x, y), (x + self.eye_w, y), (x + self.eye_w, y + self.eye_h // 2)], fill="black")
        else:
            draw.polygon([(x, y), (x + self.eye_w, y), (x, y + self.eye_h // 2)], fill="black")

    def _draw_happy_eye(self, draw, x, y):
        eyelid_height = self.eye_h // 2
        draw.rounded_rectangle(
            (x - 1, y + self.eye_h - eyelid_height,
             x + self.eye_w + 1, y + self.eye_h + eyelid_height),
            radius=self.eye_radius,
            fill="black"
        )

    def update(self):
        now = time.monotonic()
        dt = now - self.last_frame
        self.last_frame = now

        self.animation_phase += dt

        if self.mood == "happy":
            self.vertical_offset = int(math.sin(self.animation_phase * 3) * 5)
            self.scale_factor = 1.0
        elif self.mood == "sad":
            amplitude = 3
            base_offset = 8
            self.vertical_offset = base_offset + int(amplitude * math.sin(self.animation_phase * 1.5))
            self.scale_factor = 1.0
        elif self.mood in ("angry", "love", "excited"):
            self.vertical_offset = 0
            self.scale_factor = 1.0 + 0.05 * math.sin(self.animation_phase * 4)
        else:
            self.vertical_offset = 0
            self.scale_factor = 1.0
            if now >= self.next_neutral_shift_time:
                self.eye_x_offset = random.randint(-5, 5)
                self.eye_y_offset = random.randint(-3, 3)
                self.neutral_shift_start_time = now
                self.next_neutral_shift_time = now + random.uniform(2, 5)
            elif now - self.neutral_shift_start_time >= self.neutral_shift_duration:
                self.eye_x_offset = 0
                self.eye_y_offset = 0

        if self.auto_blink and not self.blinking and now >= self.next_blink_time:
            self.blink()

        if self.blinking:
            self.blink_progress += self.blink_direction * dt / self.blink_speed
            self.blink_progress = max(0.0, min(1.0, self.blink_progress))

            if self.blink_progress >= 1.0:
                self.blink_progress = 1.0
                if self.blink_hold_timer == 0:
                    self.blink_hold_timer = now + self.blink_hold_time
                elif now >= self.blink_hold_timer:
                    self.blink_direction = -1
                    self.blink_hold_timer = 0
            elif self.blink_progress <= 0.0 and self.blink_direction == -1:
                self.blinking = False
                self.blink_direction = 0
                self.next_blink_time = now + random.uniform(1, 8)

        self.draw()

    def display_number(self, num):
        image = Image.new("RGB", (self.width, self.height), "black")
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 160)
        except OSError:
            font = ImageFont.load_default()
        text = str(num)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (self.width - w) // 2
        y = (self.height - h) // 2 - 30
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        self.disp.image(image)

    def numbers(self, delay=1):
        for num in range(1, 11):
            self.display_number(num)
            time.sleep(delay)

    def countdown_numbers(self, delay=1):
        for num in range(10, 0, -1):
            self.display_number(num)
            time.sleep(delay)

    def display_letter(self, letter):
        image = Image.new("RGB", (self.width, self.height), "black")
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 160)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), letter, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (self.width - w) // 2
        y = (self.height - h) // 2 - 30
        draw.text((x, y), letter, font=font, fill=(255, 255, 255))
        self.disp.image(image)

    def alphabet(self, delay=1):
        for char_code in range(ord('A'), ord('Z') + 1):
            self.display_letter(chr(char_code))
            time.sleep(delay)

    def display_animal(self, name, delay=1):
        try:
            img_path = f"images/animals/{name}.png"
            image = Image.open(img_path).convert("RGB")
            image = ImageOps.fit(image, (239, 239), method=Image.LANCZOS)
            background = Image.new("RGB", (self.width, self.height), "black")
            x = (self.width - 239) // 2
            y = (self.height - 239) // 2
            background.paste(image, (x, y))
            self.disp.image(background)
            time.sleep(delay)
        except Exception as e:
            print(f"Error loading/displaying animal '{name}': {e}")

    def animals(self, delay=2):
        animals = [
            "dog", "cat", "cow", "bird", "pig", "horse", "wolf", "snake",
            "frog", "whale", "owl", "sheep", "chicken", "bee", "monkey", "lion"
        ]
        for animal in animals:
            self.display_animal(animal, delay)
def main():
    eyes = RoboEyes(disp)
    # print("RoboEyes Ready!")
    eyes.alphabet()
    #eyes.numbers()
    eyes.toggle_auto_blink()
    eyes.set_mood("angry")

    try:
        while True:
            start = time.monotonic()
            eyes.update()
            elapsed = time.monotonic() - start
            sleep_time = max(0, eyes.frame_interval - elapsed)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        disp.image(Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0)))
        print("Program stopped.")

if __name__ == "__main__":
    main()
