import RPi.GPIO as GPIO
import time
import threading

# =========================
# GPIO pin assignments
# =========================
RED_PIN = 7     # GPIO 7 → Red LED pin
GREEN_PIN = 9   # GPIO 9 → Green LED pin
BLUE_PIN = 16    # GPIO 8 → Blue LED pin  (updated from GPIO 6)

# =========================
# GPIO setup
# =========================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

# =========================
# PWM setup (100 Hz)
# =========================
red_pwm = GPIO.PWM(RED_PIN, 100)
green_pwm = GPIO.PWM(GREEN_PIN, 100)
blue_pwm = GPIO.PWM(BLUE_PIN, 100)

red_pwm.start(0)
green_pwm.start(0)
blue_pwm.start(0)

# =========================
# Global control for music loop
# =========================
music_playing = False
music_thread = None

# =========================
# Set color instantly (0–100)
# =========================
def set_color(r, g, b):
    """Set LED brightness instantly (0=off, 100=full)."""
    red_pwm.ChangeDutyCycle(r)
    green_pwm.ChangeDutyCycle(g)
    blue_pwm.ChangeDutyCycle(b)

# =========================
# Smooth fade to target color
# =========================
def fade_to(r_target, g_target, b_target, steps=50, delay=0.02):
    """Smoothly fade from current color to target color."""
    for i in range(steps + 1):
        r = int(r_target * i / steps)
        g = int(g_target * i / steps)
        b = int(b_target * i / steps)
        set_color(r, g, b)
        time.sleep(delay)

# =========================
# Emotion functions
# =========================
def happy():
    fade_to(0, 100, 0)       # Green

def sad():
    fade_to(0, 0, 100)       # Blue

def angry():
    fade_to(100, 0, 0)       # Red

def excited():
    fade_to(100, 100, 0)     # Yellow

def love():
    fade_to(100, 0, 100)     # Pink / Magenta

def normal():
    fade_to(0, 50, 100)      # Light Blue

def turn_off():
    set_color(0, 0, 0)       # All off

# =========================
# Music mode (loop colors)
# =========================
def music():
    """Start looping color transitions until stop_music() is called."""
    global music_playing, music_thread
    music_playing = True

    def music_loop():
        while music_playing:
            fade_to(100, 0, 0)   # Red
            time.sleep(0.3)
            fade_to(0, 100, 0)   # Green
            time.sleep(0.3)
            fade_to(0, 0, 100)   # Blue
            time.sleep(0.3)
            fade_to(100, 100, 0) # Yellow
            time.sleep(0.3)
            fade_to(100, 0, 100) # Pink
            time.sleep(0.3)
            fade_to(0, 50, 100)  # Light Blue
            time.sleep(0.3)

    music_thread = threading.Thread(target=music_loop)
    music_thread.start()

def stop_music():
    """Stop looping color transitions."""
    global music_playing, music_thread
    music_playing = False
    if music_thread:
        music_thread.join()
        music_thread = None
    turn_off()

# =========================
# Cleanup GPIO
# =========================
def cleanup():
    stop_music()
    red_pwm.stop()
    green_pwm.stop()
    blue_pwm.stop()
    GPIO.cleanup()

# =========================
# Test sequence
# =========================
if __name__ == "__main__":
    try:
        happy()
        time.sleep(1)
        sad()
        time.sleep(1)
        angry()
        time.sleep(1)
        excited()
        time.sleep(1)
        love()
        time.sleep(1)
        normal()
        time.sleep(1)
        music()
        time.sleep(5)
        stop_music()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
