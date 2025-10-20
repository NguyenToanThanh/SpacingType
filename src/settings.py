import sys
import os
from pathlib import Path

# Hỗ trợ PyInstaller: lấy đường dẫn đúng cho assets
def get_base_path():
    """Trả về base path cho assets, hỗ trợ cả dev và exe"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys._MEIPASS)
    else:
        # Running in development
        return Path(__file__).parent.parent

BASE_PATH = get_base_path()

# Màn hình
WIDTH, HEIGHT = 800, 600
FPS = 120  # Tăng lên 120 FPS cho chuyển động mượt mà hơn
VSYNC = True  # Bật VSync để tránh screen tearing

# Màu
WHITE = (255, 255, 255)
RED   = (255,   0,   0)

# Tàu
SHIP_WIDTH  = 60
SHIP_HEIGHT = 40
SHIP_Y = HEIGHT - SHIP_HEIGHT - 10 

# Enemy & spawn
ENEMY_SPEED   = 0.6  # Rất chậm để game dễ chơi
SPAWN_DELAYMS = 2500  

# WORDS
WORDS = [
    "apple", "explant", "car", "water", "cat",
    "book", "phone", "river", "planet", "chair",
    "music", "school", "light", "game", "bird",
    "train", "coffee", "robot", "cloud", "tree"
]

# Đường dẫn asset tương đối
ASSET_DIR = BASE_PATH / "assets"
IMAGE_DIR = ASSET_DIR / "images"
SOUND_DIR = ASSET_DIR / "sounds"

# Font
FONT_DIR = ASSET_DIR / "fonts"
FONT_REGULAR = FONT_DIR / "Roboto-Regular.ttf"
FONT_BOLD    = FONT_DIR / "Roboto-Bold.ttf"

# Save directory - luôn lưu ở nơi exe chạy, không trong _MEIPASS
if getattr(sys, 'frozen', False):
    # Khi chạy từ exe, lưu ở cùng thư mục với exe
    SAVE_DIR = Path(sys.executable).parent / "save"
else:
    # Khi dev, lưu ở thư mục project
    SAVE_DIR = BASE_PATH / "save"

SAVE_DIR.mkdir(exist_ok=True)
PROGRESS_FILE = SAVE_DIR / "progress.json"

# Challenge
CHALLENGE_LEVELS = [1.2, 1.5, 1.8, 2.2, 2.6, 3.0, 3.5, 4.0, 4.6, 5.2]  # tốc độ rơi
STAR_IMAGE_NAME = "star.png"

# States
STATE_MENU = "menu"
STATE_CLASSIC = "classic"
STATE_CHALLENGE = "challenge"
STATE_LEADERBOARD = "leaderboard"
STATE_LEVEL_CLEAR = "level_clear"
