import os
import time
import threading
from emotion_timeline import EmotionTimeline

class StoryPlayer:
    def __init__(self, audio_player, led_controller, display_controller, servo_controller):
        """
        audio_player: Object with .play(filepath) and .stop()
        led_controller: LEDController instance
        display_controller: RoboEyes instance
        servo_controller: ServoController instance
        """
        self.audio_player = audio_player
        self.led = led_controller
        self.display = display_controller
        self.servo = servo_controller

        self.timeline = None
        self.is_playing = False
        self.update_thread = None

    def play(self, story_id):
        """Start playing a story and emotion timeline."""
        if self.is_playing:
            self.stop()

        filepath = os.path.join("media", "stories", f"story_{story_id}.mp3")
        if not os.path.exists(filepath):
            print(f"❌ Story file not found: {filepath}")
            return

        self.timeline = EmotionTimeline(story_id)
        self.timeline.start()
        self.is_playing = True

        self.update_thread = threading.Thread(target=self._update_components, daemon=True)
        self.update_thread.start()

        print(f"▶ Playing story {story_id}")
        self.audio_player.play(filepath)

    def _update_components(self):
        last_emotion = None
        while self.is_playing:
            emotion = self.timeline.get_current_emotion()
            if emotion and emotion != last_emotion:
                print(f"🎭 Emotion changed to: {emotion}")
                self.led.set_emotion(emotion)
                self.display.set_mood(emotion)
                self.servo.set_emotion(emotion)
                last_emotion = emotion
            time.sleep(0.1)

    def stop(self):
        """Stop story playback and reset."""
        if not self.is_playing:
            return

        print("⏹ Stopping story playback")
        self.is_playing = False
        self.audio_player.stop()

        self.led.set_emotion("neutral")
        self.display.set_mood("neutral")
        self.servo.set_emotion("neutral")

        if self.update_thread:
            self.update_thread.join(timeout=0.5)
            self.update_thread = None
