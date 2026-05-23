import time
import threading

class EmotionTimeline:
    def __init__(self, story_id):
        self.story_id = story_id
        self.current_emotion = "neutral"
        self.running = False
        self.thread = None

        # Example hardcoded timeline (seconds: emotion)
        self.timelines = {
            1: [(0, "neutral"), (5, "happy"), (10, "sad"), (15, "neutral")],
            2: [(0, "neutral"), (3, "angry"), (8, "love"), (12, "neutral")]
        }

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_timeline, daemon=True)
        self.thread.start()

    def _run_timeline(self):
        start_time = time.time()
        timeline = self.timelines.get(self.story_id, [])
        idx = 0

        while self.running and idx < len(timeline):
            timestamp, emotion = timeline[idx]
            if time.time() - start_time >= timestamp:
                self.current_emotion = emotion
                idx += 1
            time.sleep(0.1)

    def get_current_emotion(self):
        return self.current_emotion

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
