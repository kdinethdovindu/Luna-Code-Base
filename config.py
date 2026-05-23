import os

class Config:
    # Base directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Media and feedback paths
    MEDIA_DIR = os.path.join(BASE_DIR, "media")
    STORIES_DIR = os.path.join(MEDIA_DIR, "stories")
    SONGS_DIR = os.path.join(MEDIA_DIR, "songs")
    EDUCATION_DIR = os.path.join(MEDIA_DIR, "education")
    FEEDBACK_DIR = os.path.join(BASE_DIR, "feedback")
    IMAGE_DIR = os.path.join(BASE_DIR, "images")
    ANIMAL_IMAGE_DIR = os.path.join(IMAGE_DIR, "animals")

    # Audio configuration
    DEFAULT_VOLUME = 0.6            # 0.0 to 1.0
    VOLUME_STEP = 0.1

    # Delays and durations
    FEEDBACK_DELAY = 0.5
    COMMAND_LISTEN_DURATION = 3
    TOUCH_COOLDOWN = 5
    MOTOR_RUN_DURATION = 3

    # API Keys
    GOOGLE_API_KEY = "AIzaSyDZ-qp3bV0WS5BywXjL84pYVqyH5TlbZiI"
    PICOVOICE_ACCESS_KEY = "HaA1GFy3+aa2hMf4z9tIJCV1WTZnUwyhchdcoJ38UXjDUXBaz03dzw=="   # << ADD this here

    # Porcupine + Rhino engine paths
    WAKE_WORD_PATH = os.path.join(BASE_DIR, "hey-luna_en_raspberry-pi_v3_0_0.ppn")
    RHINO_CONTEXT_PATH = os.path.join(BASE_DIR, "robot_commands_en_raspberry-pi_v3_0_0.rhn")
    RHINO_MODEL_PATH = os.path.join(BASE_DIR, "lib", "raspberry-pi", "rhino_params.pv")
    RHINO_LIB_PATH = os.path.join(BASE_DIR, "lib", "raspberry-pi", "arm11", "libpv_rhino.so")
