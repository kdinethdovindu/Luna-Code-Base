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
from scipy.signal import resample


# Suppress pygame NEON warning
warnings.filterwarnings("ignore", message="Your system is neon capable")

# Initialize pygame mixer with better buffer settings
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)


# Configuration
class Config:
    ACCESS_KEY = "UZC+Farxh3TLLZMMiRoRdK3ak9zB7dv8OIJEuvp0RzxYKKqQ8H4mYA=="
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEDIA_DIR = os.path.join(BASE_DIR, "media")
    STORIES_DIR = os.path.join(MEDIA_DIR, "stories")
    SONGS_DIR = os.path.join(MEDIA_DIR, "songs")
    EDUCATION_DIR = os.path.join(MEDIA_DIR, "education")
    FEEDBACK_DIR = os.path.join(BASE_DIR, "feedback")

    # Ensure directories exist
    os.makedirs(STORIES_DIR, exist_ok=True)
    os.makedirs(SONGS_DIR, exist_ok=True)
    os.makedirs(EDUCATION_DIR, exist_ok=True)
    os.makedirs(FEEDBACK_DIR, exist_ok=True)

    # Audio settings
    FEEDBACK_DELAY = 0.5  # seconds between feedback and action
    COMMAND_TIMEOUT = 5  # seconds to listen for command after wake word


# Audio Player Class
class AudioPlayer:
    def __init__(self):
        self.current_category = None  # 'story', 'song', 'education'
        self.last_index = None
        self.is_playing = False
        self.command_mode = False  # Whether we're listening for commands
        self.current_file = None
        self.playback_finished_callback = None

    def stop(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.is_playing = False
        self.current_file = None

    def play(self, filepath, wait=False, callback=None):
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
            self.current_file = None
            return True
        return False



class CommandHandler:
    def __init__(self, audio_player):
        self.audio = audio_player
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

        elif intent in ["comeForward", "goBackward"]:
            print(f"Movement command: {intent}")
            # Add robot movement logic here


    def _play_story(self, number=None):
        if number:
            filepath = os.path.join(Config.STORIES_DIR, f"story_{number}.mp3")
            if os.path.exists(filepath):
                self.audio.current_category = "story"
                self.audio.last_index = number
                self.audio.play(filepath, callback=self._playback_finished)
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
            self.audio.play(filepath, callback=self._playback_finished)

    def _play_song(self, number=None):
        if number:
            filepath = os.path.join(Config.SONGS_DIR, f"song_{number}.mp3")
            if os.path.exists(filepath):
                self.audio.current_category = "song"
                self.audio.last_index = number
                self.audio.play(filepath, callback=self._playback_finished)
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
            self.audio.play(filepath, callback=self._playback_finished)

    def _play_education(self, content_type):
        filepath = os.path.join(Config.EDUCATION_DIR, f"{content_type}.mp3")
        if os.path.exists(filepath):
            self.audio.current_category = "education"
            self.audio.play(filepath, callback=self._playback_finished)

    def _playback_finished(self):
        self.audio.play_feedback("playback_finished", wait=True)

    def _handle_next(self):
        if not self.audio.current_category:
            return

        # Step 1: Stop current playback
        self.audio.stop()

        # Step 2: Wait 0.5s and play 'playback_stopped' feedback
        time.sleep(Config.FEEDBACK_DELAY)
        self.audio.play_feedback("playback_stopped", wait=True)

        # Step 3: Wait another 0.5s and play 'playback_switching' feedback
        time.sleep(Config.FEEDBACK_DELAY)
        self.audio.play_feedback("playback_switching", wait=True)

        # Step 4: Wait another 0.5s and play next file
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
        self.audio_player = AudioPlayer()
        self.command_handler = CommandHandler(self.audio_player)
        self.input_sample_rate = 44100
        self.target_sample_rate = 16000
        self.raw_audio_buffer = np.array([], dtype=np.int16)

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

    def _get_input_device_index(self):
        for i, dev in enumerate(sd.query_devices()):
            if "USB" in dev['name'] and dev['max_input_channels'] > 0:
                print(f"Using USB mic: {dev['name']}")
                return i
        raise RuntimeError("USB microphone not found")

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"[AUDIO STATUS] {status}")

        # Append new input data (44100 Hz) to raw_audio_buffer
        self.raw_audio_buffer = np.concatenate((self.raw_audio_buffer, indata[:, 0]))

        # Calculate how many input samples correspond to 512 samples at 16kHz
        # input_samples_needed = 512 * (44100 / 16000) = 512 * 2.75625 ≈ 1412 samples
        input_samples_needed = int(512 * (self.input_sample_rate / self.target_sample_rate))

        while len(self.raw_audio_buffer) >= input_samples_needed:
            # Take a chunk of input_samples_needed from raw buffer
            input_chunk = self.raw_audio_buffer[:input_samples_needed]

            # Resample chunk down to 512 samples at 16kHz
            resampled_chunk = resample(input_chunk, 512).astype(np.int16)

            # Put resampled chunk into queue for processing
            self.audio_queue.put(resampled_chunk)

            # Remove used samples from raw buffer
            self.raw_audio_buffer = self.raw_audio_buffer[input_samples_needed:]

    def run(self):
        print("Say 'Hey Luna' to wake up...")

        # Play initial activation feedback only once
        self.audio_player.play_feedback("activated_now_listening_to_you", wait=True)

        with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.input_sample_rate,
                blocksize=512,
                dtype='int16',
                device=self._get_input_device_index()
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
                    # Don't play feedback for wake word

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


if __name__ == "__main__":
    luna = LunaVoiceControl()
    try:
        luna.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        luna.cleanup()