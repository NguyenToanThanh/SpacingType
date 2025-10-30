# ============================================================
# settings.py - Cấu hình toàn bộ game (constants, paths, settings)
# ============================================================

import sys
from pathlib import Path

# ============================================================
# PHÁT HIỆN CHẠY .EXE HAY SCRIPT PYTHON
# ============================================================
# Khi build thành .exe bằng PyInstaller, assets sẽ nằm trong thư mục tạm _MEIPASS
# Khi chạy script Python bình thường, assets nằm trong thư mục project
if getattr(sys, 'frozen', False):
    # Đang chạy file .exe - assets được giải nén vào _MEIPASS
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Đang chạy script Python - assets nằm trong thư mục project
    # __file__ = đường dẫn file này (settings.py)
    # .parent = thư mục src/
    # .parent.parent = thư mục gốc project
    BASE_DIR = Path(__file__).parent.parent

# ============================================================
# CÀI ĐẶT MÀN HÌNH
# ============================================================
WIDTH, HEIGHT = 800, 600  # Kích thước cửa sổ game (pixel)
FPS = 120  # Frames Per Second - Số khung hình mỗi giây (càng cao càng mượt)
VSYNC = True  # Vertical Sync - Đồng bộ khung hình với màn hình (chống giật lag)

# ============================================================
# ĐỊNH NGHĨA MÀU SẮC (RGB format)
# ============================================================
WHITE = (255, 255, 255)  # Màu trắng - dùng cho text, đạn
RED   = (255,   0,   0)  # Màu đỏ - dùng cho enemy, cảnh báo

# ============================================================
# CÀI ĐẶT TÀU VŨ TRỤ (PLAYER)
# ============================================================
SHIP_WIDTH  = 60  # Chiều rộng tàu (pixel)
SHIP_HEIGHT = 40  # Chiều cao tàu (pixel)
SHIP_Y = HEIGHT - SHIP_HEIGHT - 10  # Vị trí Y của tàu (gần đáy màn hình) 

# ============================================================
# CÀI ĐẶT ENEMY (KẺ ĐỊCH)
# ============================================================
SPAWN_DELAYMS = 2500  # Khoảng cách thời gian spawn enemy mới (milliseconds)

# ============================================================
# DANH SÁCH TỪ TRONG GAME
# ============================================================
# Các từ được phân loại theo độ dài:
# - Từ ngắn (3-4 ký tự): Rơi nhanh, dễ gõ
# - Từ trung bình (5-7 ký tự): Rơi vừa phải
# - Từ dài (8-10 ký tự): Rơi chậm
# - Từ rất dài (11-15 ký tự): Rơi rất chậm, khó gõ
WORDS = [
    # Từ ngắn (3-4 ký tự) - Rơi nhanh
    "cat", "dog", "car", "sun", "run",
    "book", "moon", "star", "tree", "fish",
    
    # Từ trung bình (5-7 ký tự) - Rơi vừa
    "apple", "water", "phone", "river", "chair",
    "music", "school", "planet", "coffee", "robot",
    "light", "cloud", "train", "game", "bird",
    "ocean", "garden", "forest", "dragon", "castle",
    
    # Từ dài (8-10 ký tự) - Rơi chậm
    "computer", "keyboard", "mountain", "universe", "elephant",
    "butterfly", "adventure", "beautiful", "chocolate", "wonderful",
    "important", "different", "hospital", "scientist", "government",
    
    # Từ rất dài (11-15 ký tự) - Rơi rất chậm
    "programming", "environment", "communication", "understanding", "extraordinary",
    "revolutionary", "entertainment", "international", "championship", "transformation",
    "sophisticated", "congratulations", "determination", "independence", "technological"
]

# ============================================================
# ĐƯỜNG DẪN TỚI CÁC THỨ MỤC ASSETS
# ============================================================
# Tự động phát hiện đường dẫn dựa trên BASE_DIR (script hay .exe)
ASSET_DIR = BASE_DIR / "assets"  # Thư mục gốc chứa tất cả assets
IMAGE_DIR = ASSET_DIR / "images"  # Thư mục chứa hình ảnh (background, spaceship, etc.)
SOUND_DIR = ASSET_DIR / "sounds"  # Thư mục chứa âm thanh và nhạc nền

# ============================================================
# ĐƯỜNG DẪN TỚI FONT CHỮ
# ============================================================
FONT_DIR = ASSET_DIR / "fonts"  # Thư mục chứa font
FONT_REGULAR = FONT_DIR / "Roboto-Regular.ttf"  # Font chữ thường
FONT_BOLD    = FONT_DIR / "Roboto-Bold.ttf"     # Font chữ đậm

# ============================================================
# THỨ MỤC LƯU DỮ LIỆU GAME (SAVE DATA)
# ============================================================
# Save data (leaderboard, progress) không được lưu trong _MEIPASS
# vì _MEIPASS là thư mục TẠM, bị xóa sau khi tắt game
# → Lưu vào thư mục user hiện tại để dữ liệu tồn tại lâu dài

if getattr(sys, 'frozen', False):
    # ===== CHẠY .EXE =====
    # Lưu save data vào thư mục hiện tại (nơi .exe đang chạy)
    SAVE_DIR = Path.cwd() / "save"
    SAVE_DIR.mkdir(exist_ok=True, parents=True)  # Tạo thư mục nếu chưa có
    
    # LẦN CHẠY ĐẦU TIÊN: Copy dữ liệu mẫu từ bundle vào thư mục user
    bundled_save = BASE_DIR / "save"  # Dữ liệu mẫu được đóng gói trong .exe
    if bundled_save.exists():
        import shutil
        
        # Copy leaderboard.json nếu user chưa có
        if (bundled_save / "leaderboard.json").exists() and not (SAVE_DIR / "leaderboard.json").exists():
            try:
                shutil.copy2(bundled_save / "leaderboard.json", SAVE_DIR / "leaderboard.json")
                print("[✓] Copied leaderboard.json from bundle")
            except Exception as e:
                print(f"[✗] Warning: Could not copy leaderboard.json: {e}")
        
        # Copy progress.json nếu user chưa có
        if (bundled_save / "progress.json").exists() and not (SAVE_DIR / "progress.json").exists():
            try:
                shutil.copy2(bundled_save / "progress.json", SAVE_DIR / "progress.json")
                print("[✓] Copied progress.json from bundle")
            except Exception as e:
                print(f"[✗] Warning: Could not copy progress.json: {e}")
else:
    # ===== CHẠY SCRIPT PYTHON =====
    # Lưu save data vào thư mục project (thư mục gốc)
    SAVE_DIR = BASE_DIR / "save"
    SAVE_DIR.mkdir(exist_ok=True, parents=True)  # Tạo thư mục nếu chưa có

# Đường dẫn đến file lưu tiến trình challenge mode
PROGRESS_FILE = SAVE_DIR / "progress.json"

# ============================================================
# CÀI ĐẶT CHALLENGE MODE (10 LEVELS)
# ============================================================
# Mỗi level có tốc độ rơi tăng dần (càng cao càng khó)
# Index 0 = Level 1, Index 9 = Level 10
CHALLENGE_LEVELS = [
    0.5,  # Level 1 
    0.8,  # Level 2
    1.5,  # Level 3
    1.7,  # Level 4
    1.9,  # Level 5 
    2.3,  # Level 6
    2.7,  # Level 7
    3.0,  # Level 8
    3.5,  # Level 9
    4.0   # Level 10
]

STAR_IMAGE_NAME = "star.png"  # Tên file icon sao (dùng trong level select)

# ============================================================
# ĐỊNH NGHĨA CÁC TRẠNG THÁI GAME (GAME STATES)
# ============================================================
# Game chuyển đổi giữa các state này
STATE_MENU = "menu"              # Màn hình menu chính
STATE_CLASSIC = "classic"        # Chế độ chơi tự do
STATE_CHALLENGE = "challenge"    # Chế độ thử thách 10 levels
STATE_LEADERBOARD = "leaderboard"  # Bảng xếp hạng
STATE_LEVEL_CLEAR = "level_clear"  # Màn hình hoàn thành level
