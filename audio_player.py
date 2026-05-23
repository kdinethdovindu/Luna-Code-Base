import os
import time
import pygame
from config import Config


class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        pygame.mixer.music.set_volume(Config.DEFAULT_VOLUME)

        self.is_playing = False
        self.current_category = None  # story / song / education
        self.last_index = None        # story/song number (1–10)
        self.current_file = None
        self.last_play_mode = None    # "specific" or "random"
        self.callback = None          # Function to call when playback ends

    def play(self, filepath, category=None, index=None, mode="specific", callback=None):
        """Plays an audio file and tracks its state."""
        if not os.path.exists(filepath):
            print(f"[AudioPlayer] File not found: {filepath}")
            return False

        self.stop()

        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self.is_playing = True
            self.current_category = category
            self.last_index = index
            self.current_file = filepath
            self.last_play_mode = mode
            self.callback = callback
            return True
        except Exception as e:
            print(f"[AudioPlayer] Playback error: {e}")
            return False

    def play_feedback(self, name, wait=False):
        """Play feedback from feedback folder by name (without .mp3)."""
        path = os.path.join(Config.FEEDBACK_DIR, f"{name}.mp3")
        if os.path.exists(path):
            self.play(path)
            if wait:
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
        else:
            print(f"[AudioPlayer] Missing feedback: {name}.mp3")

    def stop(self):
        """Stops any currently playing audio."""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.is_playing = False
        self.current_file = None
        self.callback = None

    def check_finished(self):
        """Check if playback ended naturally and run callback."""
        if self.is_playing and not pygame.mixer.music.get_busy():
            self.is_playing = False
            if self.callback:
                self.callback()
            self.callback = None
            return True
        return False

    def set_volume(self, volume):
        """Set volume between 0.0 and 1.0"""
        volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(volume)

    def increase_volume(self):
        current = pygame.mixer.music.get_volume()
        self.set_volume(current + Config.VOLUME_STEP)

    def decrease_volume(self):
        current = pygame.mixer.music.get_volume()
        self.set_volume(current - Config.VOLUME_STEP)
