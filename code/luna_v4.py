import os
import time
import threading
import random
import queue
import numpy as np
import pygame
import RPi.GPIO as GPIO
import sounddevice as sd
from scipy.signal import resample
from pvporcupine import create as create_porcupine
from pvrhino import Rhino

from led_controller import LEDController
from display_controller import RoboEyes
from servo_controller import ServoController
from story_player import StoryPlayer
from emotion_timeline import EmotionTimeline
from motor_controller import MotorController
from emotion_detector import detect_emotion


# === AUDIO DEVICE DETECTION ===
devices = sd.query_devices()

print("\n=== 🎧 AUDIO DEVICE CHECK ===")
for i, dev in enumerate(devices):
    print(f"{i}: {dev['name']} (inputs: {dev['max_input_channels']}, outputs: {dev['max_output_channels']})")
print("=============================\n")

# --- Pick first input-capable device ---
input_device_index = None
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        input_device_index = i
        break

if input_device_index is None:
    raise RuntimeError("❌ No working input microphone found")
else:
    print(f"✅ Using microphone: {devices[input_device_index]['name']}")

# --- Pick first output-capable device ---
output_device_hw = None
output_device_name = None
for i, dev in enumerate(devices):
    if dev['max_output_channels'] > 0:
        output_device_hw = f"hw:{i},0"
        output_device_name = dev['name']
        break

if output_device_hw is None:
    raise RuntimeError("❌ No working output speaker found")
else:
    print(f"🔊 Using speaker: {output_device_name} ({output_device_hw})")

# --- Force pygame to use chosen output ---
os.environ["SDL_AUDIODRIVER"] = "alsa"
os.environ["AUDIODEV"] = output_device_hw

# Store for LunaVoiceControl
AUDIO_INPUT_DEVICE_INDEX = input_device_index


class Config:
    ACCESS_KEY = "UZC+Farxh3TLLZMMiRoRdK3ak9zB7dv8OIJEuvp0RzxYKKqQ8H4mYA=="
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEDIA_DIR = os.path.join(BASE_DIR, "media")
    STORIES_DIR = os.path.join(MEDIA_DIR, "stories")
    SONGS_DIR = os.path.join(MEDIA_DIR, "songs")
    EDUCATION_DIR = os.path.join(MEDIA_DIR, "education")
    FEEDBACK_DIR = os.path.join(BASE_DIR, "feedback")

    MOTOR_A_IN1 = 24
    MOTOR_A_IN2 = 23
    MOTOR_A_EN = 25
    MOTOR_B_IN3 = 17
    MOTOR_B_IN4 = 27
    MOTOR_B_EN = 22

    TOUCH_PIN = 7  # BCM numbering

    MOVEMENT_DURATION = 3
    COMMAND_TIMEOUT = 5

    WAKE_WORD_PATH = os.path.join(BASE_DIR, "wake-up_en_raspberry-pi_v3_0_0.ppn")
    RHINO_CONTEXT_PATH = os.path.join(BASE_DIR, "robot_commands_en_raspberry-pi_v3_0_0.rhn")
    RHINO_MODEL_PATH = os.path.join(BASE_DIR, "lib", "raspberry-pi", "rhino_params.pv")
    RHINO_LIBRARY_PATH = os.path.join(BASE_DIR, "lib", "raspberry-pi", "arm11", "libpv_rhino.so")

    os.makedirs(STORIES_DIR, exist_ok=True)
    os.makedirs(SONGS_DIR, exist_ok=True)
    os.makedirs(EDUCATION_DIR, exist_ok=True)
    os.makedirs(FEEDBACK_DIR, exist_ok=True)


class AudioPlayer:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.led_controller = None
        self.lock = threading.Lock()

    def play(self, filepath, is_song=False):
        with self.lock:
            if not os.path.exists(filepath):
                print(f"❌ File not found: {filepath}")
                return
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            if is_song and self.led_controller:
                self.led_controller.music()

    def stop(self):
        with self.lock:
            pygame.mixer.music.stop()
            if self.led_controller:
                self.led_controller.stop_music()

    def play_feedback(self, name):
        path = os.path.join(Config.FEEDBACK_DIR, f"{name}.mp3")
        self.play(path, is_song=False)


class LunaVoiceControl:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.led_controller = LEDController()
        self.display_controller = RoboEyes()
        self.servo_controller = ServoController()
        self.motor_controller = MotorController(Config)
        self.audio_player = AudioPlayer()
        self.audio_player.led_controller = self.led_controller
        self.story_player = StoryPlayer(self.audio_player, self.led_controller, self.display_controller, self.servo_controller)

        self.sleep_mode = False

        self.set_initial_mode()
        self._setup_touch_sensor()

        self.porcupine = create_porcupine(access_key=Config.ACCESS_KEY, keyword_paths=[Config.WAKE_WORD_PATH])
        self.rhino = Rhino(access_key=Config.ACCESS_KEY,
                           context_path=Config.RHINO_CONTEXT_PATH,
                           model_path=Config.RHINO_MODEL_PATH,
                           library_path=Config.RHINO_LIBRARY_PATH)

        self.audio_queue = queue.Queue()
        self.raw_audio_buffer = np.array([], dtype=np.int16)
        self.input_sample_rate = 44100
        self.target_sample_rate = 16000

        threading.Thread(target=self._display_update_loop, daemon=True).start()

    def set_initial_mode(self):
        print("🔵 Initial mode: Neutral")
        self.led_controller.set_emotion("neutral")
        self.display_controller.set_mood("neutral")
        self.servo_controller.set_emotion("neutral")

    def set_sleep_mode(self):
        print("💤 Sleep mode")
        self.led_controller.turn_off()
        self.display_controller.cleanup()
        self.sleep_mode = True

    def _setup_touch_sensor(self):
        GPIO.setup(Config.TOUCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        threading.Thread(target=self._touch_sensor_loop, daemon=True).start()

    def _touch_sensor_loop(self):
        last_touch = 0
        debounce = 0.5
        while True:
            if GPIO.input(Config.TOUCH_PIN) == GPIO.HIGH:
                now = time.time()
                if now - last_touch > debounce:
                    last_touch = now
                    print("🤚 Touch detected")
                    self.display_controller.set_mood("love")
                    self.servo_controller.set_emotion("happy")
                    self.audio_player.play_feedback("petting")
            time.sleep(0.05)

    def _display_update_loop(self):
        while True:
            self.display_controller.update()
            time.sleep(0.05)

    def _get_input_device_index(self):
        return AUDIO_INPUT_DEVICE_INDEX

    def audio_callback(self, indata, frames, time_info, status):
        self.raw_audio_buffer = np.concatenate((self.raw_audio_buffer, indata[:, 0]))
        input_samples_needed = int(512 * (self.input_sample_rate / self.target_sample_rate))
        while len(self.raw_audio_buffer) >= input_samples_needed:
            chunk = self.raw_audio_buffer[:input_samples_needed]
            resampled = resample(chunk, 512).astype(np.int16)
            self.audio_queue.put(resampled)
            self.raw_audio_buffer = self.raw_audio_buffer[input_samples_needed:]

    def handle_intent(self, intent, slots):
        if intent == "sleep":
            self.story_player.stop()
            self.audio_player.stop()
            self.set_sleep_mode()
            return

        if intent == "navigation":
            side = slots.get("side", "").lower()
            if side == "forward":
                self.motor_controller.forward()
            elif side == "backward":
                self.motor_controller.backward()
            elif side == "left":
                self.motor_controller.left()
            elif side == "right":
                self.motor_controller.right()
            threading.Timer(Config.MOVEMENT_DURATION, self.motor_controller.stop).start()
            return

        if intent == "checkEmotion":
            threading.Thread(target=self.detect_emotion_and_act, daemon=True).start()
            return

    def detect_emotion_and_act(self):
        emotion = detect_emotion()
        if emotion is None:
            self.audio_player.play_feedback("no_face")
            return

        print(f"🎭 Emotion detected: {emotion}")

        mapping = {
            "joy": ("joy", self._play_random_story),
            "sorrow": ("sorrow", self._play_random_song),
            "anger": ("anger", lambda: self.audio_player.play(os.path.join(Config.SONGS_DIR, "rude.mp3"))),
            "surprise": ("surprise", None)
        }

        fb, action = mapping.get(emotion, (None, None))
        if fb:
            self.audio_player.play_feedback(fb)
        if action:
            time.sleep(1.5)
            action()

    def _play_random_story(self):
        files = [f for f in os.listdir(Config.STORIES_DIR) if f.endswith(".mp3")]
        if files:
            choice = random.choice(files)
            self.audio_player.play(os.path.join(Config.STORIES_DIR, choice))

    def _play_random_song(self):
        files = [f for f in os.listdir(Config.SONGS_DIR) if f.endswith(".mp3")]
        if files:
            choice = random.choice(files)
            self.audio_player.play(os.path.join(Config.SONGS_DIR, choice), is_song=True)

    def run(self):
        print("Say 'Hey Luna' to wake me up...")
        with sd.InputStream(callback=self.audio_callback, channels=1, samplerate=self.input_sample_rate,
                            blocksize=512, dtype='int16', device=self._get_input_device_index()):
            while True:
                data = self.audio_queue.get()
                pcm = np.frombuffer(data, dtype=np.int16)
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    if self.sleep_mode:
                        self.set_initial_mode()
                        self.sleep_mode = False
                    continue
                if not self.sleep_mode:
                    finalized = self.rhino.process(pcm)
                    if finalized:
                        inference = self.rhino.get_inference()
                        if inference.is_understood:
                            self.handle_intent(inference.intent, dict(inference.slots))

    def cleanup(self):
        try:
            self.story_player.stop()
            self.audio_player.stop()
            self.motor_controller.cleanup()
            self.led_controller.cleanup()
            self.servo_controller.cleanup()
            self.display_controller.cleanup()
            self.porcupine.delete()
            self.rhino.delete()
            pygame.quit()
            GPIO.cleanup()
        except Exception as e:
            print(f"Cleanup error: {e}")


if __name__ == "__main__":
    luna = LunaVoiceControl()
    try:
        luna.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        luna.cleanup()
