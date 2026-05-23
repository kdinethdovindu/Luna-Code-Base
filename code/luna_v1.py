import os
import queue
import time
import random
import numpy as np
import sounddevice as sd
from pvporcupine import create as create_porcupine
from pvrhino import Rhino
import pygame
import warnings
import RPi.GPIO as GPIO
import threading

# Suppress pygame NEON warning
warnings.filterwarnings("ignore", message="Your system is neon capable")
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


# Configuration
class Config:
    ACCESS_KEY = "UZC+Farxh3TLLZMMiRoRdK3ak9zB7dv8OIJEuvp0RzxYKKqQ8H4mYA=="
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEDIA_DIR = os.path.join(BASE_DIR, "media")
    STORIES_DIR = os.path.join(MEDIA_DIR, "stories")
    SONGS_DIR = os.path.join(MEDIA_DIR, "songs")
    EDUCATION_DIR = os.path.join(MEDIA_DIR, "education")
    FEEDBACK_DIR = os.path.join(BASE_DIR, "feedback")

    # LED pins
    RED_PIN = 7
    GREEN_PIN = 9
    BLUE_PIN = 16

    # Motor pins
    MOTOR_A_IN1 = 24
    MOTOR_A_IN2 = 23
    MOTOR_A_EN = 25
    MOTOR_B_IN3 = 17
    MOTOR_B_IN4 = 27
    MOTOR_B_EN = 22

    # Audio settings
    FEEDBACK_DELAY = 0.5  # seconds between feedback and action
    COMMAND_TIMEOUT = 3  # seconds to listen for command after wake word
    MOVEMENT_DURATION = 3  # seconds for motor movements

    # Ensure directories exist
    os.makedirs(STORIES_DIR, exist_ok=True)
    os.makedirs(SONGS_DIR, exist_ok=True)
    os.makedirs(EDUCATION_DIR, exist_ok=True)
    os.makedirs(FEEDBACK_DIR, exist_ok=True)


# Initialize pygame mixer with better buffer settings
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)


# LED Controller Class
class LEDController:
    def __init__(self):
        # Setup GPIO
        GPIO.setup(Config.RED_PIN, GPIO.OUT)
        GPIO.setup(Config.GREEN_PIN, GPIO.OUT)
        GPIO.setup(Config.BLUE_PIN, GPIO.OUT)

        # PWM setup
        self.red_pwm = GPIO.PWM(Config.RED_PIN, 100)
        self.green_pwm = GPIO.PWM(Config.GREEN_PIN, 100)
        self.blue_pwm = GPIO.PWM(Config.BLUE_PIN, 100)

        self.red_pwm.start(0)
        self.green_pwm.start(0)
        self.blue_pwm.start(0)

        self.music_playing = False
        self.music_thread = None

    def set_color(self, r, g, b):
        self.red_pwm.ChangeDutyCycle(r)
        self.green_pwm.ChangeDutyCycle(g)
        self.blue_pwm.ChangeDutyCycle(b)

    def fade_to(self, r_target, g_target, b_target, steps=50, delay=0.02):
        for i in range(steps + 1):
            r = int(r_target * i / steps)
            g = int(g_target * i / steps)
            b = int(b_target * i / steps)
            self.set_color(r, g, b)
            time.sleep(delay)

    def happy(self):
        self.stop_music()
        self.fade_to(0, 100, 0)

    def sad(self):
        self.stop_music()
        self.fade_to(0, 0, 100)

    def angry(self):
        self.stop_music()
        self.fade_to(100, 0, 0)

    def excited(self):
        self.stop_music()
        self.fade_to(100, 100, 0)

    def love(self):
        self.stop_music()
        self.fade_to(100, 0, 100)

    def normal(self):
        self.stop_music()
        self.fade_to(0, 50, 100)

    def turn_off(self):
        self.stop_music()
        self.set_color(0, 0, 0)

    def music(self):
        self.stop_music()
        self.music_playing = True
        self.music_thread = threading.Thread(target=self._music_loop)
        self.music_thread.start()

    def _music_loop(self):
        while self.music_playing:
            self.fade_to(100, 0, 0)
            if not self.music_playing: break
            self.fade_to(0, 100, 0)
            if not self.music_playing: break
            self.fade_to(0, 0, 100)
            if not self.music_playing: break
            self.fade_to(100, 100, 0)
            if not self.music_playing: break
            self.fade_to(100, 0, 100)
            if not self.music_playing: break
            self.fade_to(0, 50, 100)
            if not self.music_playing: break

    def stop_music(self):
        self.music_playing = False
        if self.music_thread:
            self.music_thread.join()
            self.music_thread = None

    def cleanup(self):
        self.stop_music()
        self.red_pwm.stop()
        self.green_pwm.stop()
        self.blue_pwm.stop()


# Motor Controller Class
class MotorController:
    def __init__(self):
        # Setup GPIO
        GPIO.setup([
            Config.MOTOR_A_IN1, Config.MOTOR_A_IN2, Config.MOTOR_A_EN,
            Config.MOTOR_B_IN3, Config.MOTOR_B_IN4, Config.MOTOR_B_EN
        ], GPIO.OUT)

        # Initial motor states
        GPIO.output(Config.MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(Config.MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(Config.MOTOR_B_IN3, GPIO.LOW)
        GPIO.output(Config.MOTOR_B_IN4, GPIO.LOW)

        # PWM setup
        self.pA = GPIO.PWM(Config.MOTOR_A_EN, 1000)
        self.pB = GPIO.PWM(Config.MOTOR_B_EN, 1000)
        self.pA.start(0)
        self.pB.start(0)

        # Timer for automatic stop
        self.timer = None

    def stop(self):
        # Cancel any ongoing timer
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        # Stop motors
        GPIO.output(Config.MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(Config.MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(Config.MOTOR_B_IN3, GPIO.LOW)
        GPIO.output(Config.MOTOR_B_IN4, GPIO.LOW)
        self.pA.ChangeDutyCycle(0)
        self.pB.ChangeDutyCycle(0)

    def forward(self):
        self.stop()  # Stop any current movement
        GPIO.output(Config.MOTOR_A_IN1, GPIO.HIGH)
        GPIO.output(Config.MOTOR_A_IN2, GPIO.LOW)
        GPIO.output(Config.MOTOR_B_IN3, GPIO.HIGH)
        GPIO.output(Config.MOTOR_B_IN4, GPIO.LOW)
        self.pA.ChangeDutyCycle(25)
        self.pB.ChangeDutyCycle(25)
        # Set a timer to stop after duration
        self.timer = threading.Timer(Config.MOVEMENT_DURATION, self.stop)
        self.timer.start()

    def backward(self):
        self.stop()
        GPIO.output(Config.MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(Config.MOTOR_A_IN2, GPIO.HIGH)
        GPIO.output(Config.MOTOR_B_IN3, GPIO.LOW)
        GPIO.output(Config.MOTOR_B_IN4, GPIO.HIGH)
        self.pA.ChangeDutyCycle(25)
        self.pB.ChangeDutyCycle(25)
        self.timer = threading.Timer(Config.MOVEMENT_DURATION, self.stop)
        self.timer.start()

    def gentle_left(self):
        self.stop()
        GPIO.output(Config.MOTOR_A_IN1, GPIO.LOW)
        GPIO.output(Config.MOTOR_A_IN2, GPIO.LOW)  # Left motors OFF
        GPIO.output(Config.MOTOR_B_IN3, GPIO.HIGH)
        GPIO.output(Config.MOTOR_B_IN4, GPIO.LOW)  # Right motors forward
        self.pA.ChangeDutyCycle(0)
        self.pB.ChangeDutyCycle(50)
        self.timer = threading.Timer(Config.MOVEMENT_DURATION, self.stop)
        self.timer.start()

    def gentle_right(self):
        self.stop()
        GPIO.output(Config.MOTOR_A_IN1, GPIO.HIGH)
        GPIO.output(Config.MOTOR_A_IN2, GPIO.LOW)  # Left motors forward
        GPIO.output(Config.MOTOR_B_IN3, GPIO.LOW)
        GPIO.output(Config.MOTOR_B_IN4, GPIO.LOW)  # Right motors OFF
        self.pA.ChangeDutyCycle(50)
        self.pB.ChangeDutyCycle(0)
        self.timer = threading.Timer(Config.MOVEMENT_DURATION, self.stop)
        self.timer.start()

    def cleanup(self):
        self.stop()
        self.pA.stop()
        self.pB.stop()


# Audio Player Class
class AudioPlayer:
    def __init__(self, led_controller):
        self.led = led_controller
        self.current_category = None  # 'story', 'song', 'education'
        self.last_index = None
        self.is_playing = False
        self.command_mode = False  # Whether we're listening for commands
        self.current_file = None
        self.playback_finished_callback = None
        self.is_media = False  # Whether current playback is media content

    def stop(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        if self.is_playing and self.is_media:
            self.led.normal()
        self.is_playing = False
        self.is_media = False
        self.current_file = None

    def play(self, filepath, wait=False, callback=None, is_media=False):
        try:
            if not os.path.exists(filepath):
                print(f"File not found: {filepath}")
                return False

            self.stop()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self.is_playing = True
            self.current_file = filepath
            self.playback_finished_callback = callback
            self.is_media = is_media

            if is_media:
                self.led.music()

            if wait:
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            return True
        except Exception as e:
            print(f"Playback error: {e}")
            return False

    def play_feedback(self, feedback_name, wait=False):
        filepath = os.path.join(Config.FEEDBACK_DIR, f"{feedback_name}.mp3")
        if os.path.exists(filepath):
            return self.play(filepath, wait=wait)
        else:
            print(f"Feedback file missing: {feedback_name}.mp3")
            return False

    def check_playback_finished(self):
        if self.is_playing and not pygame.mixer.music.get_busy():
            if self.playback_finished_callback:
                self.playback_finished_callback()
            self.is_playing = False
            if self.is_media:
                self.led.normal()
            self.is_media = False
            self.current_file = None
            return True
        return False


class CommandHandler:
    def __init__(self, audio_player, led_controller, motor_controller):
        self.audio = audio_player
        self.led = led_controller
        self.motors = motor_controller
        self.number_map = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }

    def get_feedback_name(self, intent, slots):
        """Determine the appropriate feedback file name"""
        if intent == "genaralPlay":
            media_type = slots.get("type", "")
            if media_type == "story":
                return "playing_a_story"
            elif media_type == "song":
                return "playing_a_song"
            elif media_type in ["alphabet", "numbers", "animals"]:
                return f"playing_{media_type}"

        if intent == "navigation":
            direction = slots.get("side", "").lower()
            if direction == "forward":
                return "coming_fowrd"
            elif direction == "backward":
                return "going_backward"
            elif direction == "left":
                return "turning_left"
            elif direction == "right":
                return "turning_right"

        if intent == "playStory" and "storyNum" in slots:
            num_word = slots["storyNum"].lower()
            num = self.number_map.get(num_word, 1)
            return f"playing_story_{num}"

        if intent == "playSong" and "songNum" in slots:
            num_word = slots["songNum"].lower()
            num = self.number_map.get(num_word, 1)
            return f"playing_song_{num}"

        # Default feedback names
        return {
            "comeForward": "coming_fowrd",
            "goBackward": "going_backward",
            "next": "playback_switching",
            "stop": "playback_stopped",
            "playStory": "playing_a_story",
            "playSong": "playing_a_song",
            "playAlphabet": "playing_alphabet",
            "playAnimals": "playing_animal_sounds",
            "playNumbers": "playing_numbers"
        }.get(intent, "playing_selected_content")

    def handle(self, intent, slots):
        # Skip feedback for wake word
        if intent == "heyLuna":
            self.audio.command_mode = True
            self.led.normal()
            return

        # Only process stop/next commands if playback is ongoing
        if intent in ["stop", "next"] and not self.audio.is_playing:
            print(f"Ignoring {intent} command - no playback ongoing")
            return

        # Play feedback for other commands
        if intent not in ["stop", "next"]:
            feedback_name = self.get_feedback_name(intent, slots)
            self.audio.play_feedback(feedback_name, wait=True)
            time.sleep(Config.FEEDBACK_DELAY)

        if intent == "sleep":
            if self.audio.is_playing:
                self.audio.stop()
                time.sleep(Config.FEEDBACK_DELAY)
                self.audio.play_feedback("playback_stopped", wait=True)
                time.sleep(Config.FEEDBACK_DELAY)

            self.audio.play_feedback("going_to_sleep", wait=True)
            time.sleep(Config.FEEDBACK_DELAY)

            self.audio.command_mode = False
            self.led.turn_off()
            return

        # Handle the command
        if intent == "stop":
            if self.audio.is_playing:
                self.audio.stop()
                time.sleep(Config.FEEDBACK_DELAY)
                self.audio.play_feedback("playback_stopped", wait=True)
                time.sleep(Config.FEEDBACK_DELAY)
            return

        if intent == "next":
            self._handle_next()
            return

        if intent == "playStory":
            num = self.number_map.get(slots.get("storyNum", "").lower(), None)
            self._play_story(num)

        elif intent == "playSong":
            num = self.number_map.get(slots.get("songNum", "").lower(), None)
            self._play_song(num)

        elif intent == "genaralPlay":
            if "type" in slots:
                media_type = slots["type"]
                if media_type == "story":
                    self._play_story()
                elif media_type == "song":
                    self._play_song()
                elif media_type == "alphabet":
                    self._play_education("alphabet")
                elif media_type == "numbers":
                    self._play_education("numbers")
                elif media_type == "animals":
                    self._play_education("animals")

        elif intent == "navigation":
            direction = slots.get("side", "").lower()
            if direction == "forward":
                self.motors.forward()
            elif direction == "backward":
                self.motors.backward()
            elif direction == "left":
                self.motors.gentle_left()
            elif direction == "right":
                self.motors.gentle_right()

    def _play_story(self, number=None):
        if number:
            filepath = os.path.join(Config.STORIES_DIR, f"story_{number}.mp3")
            if os.path.exists(filepath):
                self.audio.current_category = "story"
                self.audio.last_index = number
                self.audio.play(filepath, callback=self._playback_finished, is_media=True)
            else:
                print(f"Story file not found: story_{number}.mp3")
        else:
            files = [f for f in os.listdir(Config.STORIES_DIR) if f.startswith('story_')]
            if not files:
                print("No story files found")
                return
            filepath = os.path.join(Config.STORIES_DIR, random.choice(files))
            self.audio.current_category = "story"
            self.audio.last_index = int(filepath.split('_')[-1].split('.')[0])
            self.audio.play(filepath, callback=self._playback_finished, is_media=True)

    def _play_song(self, number=None):
        if number:
            filepath = os.path.join(Config.SONGS_DIR, f"song_{number}.mp3")
            if os.path.exists(filepath):
                self.audio.current_category = "song"
                self.audio.last_index = number
                self.audio.play(filepath, callback=self._playback_finished, is_media=True)
            else:
                print(f"Song file not found: song_{number}.mp3")
        else:
            files = [f for f in os.listdir(Config.SONGS_DIR) if f.startswith('song_')]
            if not files:
                print("No song files found")
                return
            filepath = os.path.join(Config.SONGS_DIR, random.choice(files))
            self.audio.current_category = "song"
            self.audio.last_index = int(filepath.split('_')[-1].split('.')[0])
            self.audio.play(filepath, callback=self._playback_finished, is_media=True)

    def _play_education(self, content_type):
        filepath = os.path.join(Config.EDUCATION_DIR, f"{content_type}.mp3")
        if os.path.exists(filepath):
            self.audio.current_category = "education"
            self.audio.play(filepath, callback=self._playback_finished, is_media=True)

    def _playback_finished(self):
        self.audio.play_feedback("playback_finished", wait=True)

    def _handle_next(self):
        if not self.audio.current_category:
            return

        # Step 1: Stop current playback
        self.audio.stop()

        # Step 2: Wait and play feedback
        time.sleep(Config.FEEDBACK_DELAY)
        self.audio.play_feedback("playback_stopped", wait=True)
        time.sleep(Config.FEEDBACK_DELAY)
        self.audio.play_feedback("playback_switching", wait=True)
        time.sleep(Config.FEEDBACK_DELAY)

        if self.audio.current_category == "story":
            files = sorted([f for f in os.listdir(Config.STORIES_DIR) if f.startswith('story_')])
            if not files:
                self.audio.play_feedback("no_file_to_switch", wait=True)
                return

            current_index = self.audio.last_index or 1
            next_index = current_index + 1

            if f"story_{next_index}.mp3" in files:
                self._play_story(next_index)
            else:
                self.audio.play_feedback("no_file_to_switch", wait=True)

        elif self.audio.current_category == "song":
            files = sorted([f for f in os.listdir(Config.SONGS_DIR) if f.startswith('song_')])
            if not files:
                self.audio.play_feedback("no_file_to_switch", wait=True)
                return

            current_index = self.audio.last_index or 1
            next_index = current_index + 1

            if f"song_{next_index}.mp3" in files:
                self._play_song(next_index)
            else:
                self.audio.play_feedback("no_file_to_switch", wait=True)


# Main Application
class LunaVoiceControl:
    def __init__(self):
        # Initialize hardware controllers
        self.led_controller = LEDController()
        self.motor_controller = MotorController()

        # Set initial LED state
        self.led_controller.normal()

        # Initialize audio and command systems
        self.audio_player = AudioPlayer(self.led_controller)
        self.command_handler = CommandHandler(
            self.audio_player,
            self.led_controller,
            self.motor_controller
        )

        # Initialize Porcupine and Rhino
        self.porcupine = create_porcupine(
            access_key=Config.ACCESS_KEY,
            keyword_paths=[os.path.join(Config.BASE_DIR, "wake-up_en_raspberry-pi_v3_0_0.ppn")]
        )

        self.rhino = Rhino(
            access_key=Config.ACCESS_KEY,
            context_path=os.path.join(Config.BASE_DIR, "robot_commands_en_raspberry-pi_v3_0_0.rhn"),
            model_path=os.path.join(Config.BASE_DIR, "lib", "raspberry-pi", "rhino_params.pv"),
            library_path=os.path.join(Config.BASE_DIR, "lib", "raspberry-pi", "arm11", "libpv_rhino.so")
        )

        self.audio_queue = queue.Queue()
        self.last_wake_time = 0

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"[AUDIO STATUS] {status}")
        self.audio_queue.put(indata.copy())

    def run(self):
        print("Say 'Hey Luna' to wake up...")

        # Play initial activation feedback
        self.audio_player.play_feedback("activated_now_listening_to_you", wait=True)

        with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.porcupine.sample_rate,
                blocksize=self.porcupine.frame_length,
                dtype='int16'
        ):
            while True:
                # Check if playback finished naturally
                self.audio_player.check_playback_finished()

                # Check if command timeout has passed
                if (self.audio_player.command_mode and
                        time.time() - self.last_wake_time > Config.COMMAND_TIMEOUT):
                    self.audio_player.command_mode = False
                    print("Command listening period ended")

                data = self.audio_queue.get()
                pcm = np.frombuffer(data, dtype=np.int16)

                # Always listen for wake word
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    print("? Wake word detected: 'Hey Luna'")
                    self.command_handler.handle("heyLuna", {})
                    self.last_wake_time = time.time()

                # Only process other commands if in command mode
                if self.audio_player.command_mode:
                    finalized = self.rhino.process(pcm)
                    if finalized:
                        inference = self.rhino.get_inference()
                        print("?? Inference:")
                        print(f"   Understood: {inference.is_understood}")

                        if inference.is_understood:
                            print(f"   Intent: {inference.intent}")
                            print(f"   Slots: {inference.slots}")
                            self.command_handler.handle(inference.intent, inference.slots)

    def cleanup(self):
        self.porcupine.delete()
        self.rhino.delete()
        pygame.quit()
        self.led_controller.cleanup()
        self.motor_controller.cleanup()
        GPIO.cleanup()


if __name__ == "__main__":
    luna = LunaVoiceControl()
    try:
        luna.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        luna.cleanup()