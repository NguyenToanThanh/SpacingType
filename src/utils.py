import pygame
import json
from io import BytesIO
from pathlib import Path
from .settings import IMAGE_DIR, SOUND_DIR, PROGRESS_FILE
from PIL import Image
from pathlib import Path
# ============================================================
# HÀM XỬ LÝ JSON AN TOÀN
# ============================================================
def safe_json_load(path: Path, default):
    try:
        if Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def safe_json_save(path: Path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# HÀM LOAD HÌNH ẢNH (CÓ CHỐNG LỖI)
# ============================================================
def load_image(name, size=None):
    """
    Nạp hình ảnh từ thư mục IMAGE_DIR. Tự động scale nếu có size.
    """
    path = IMAGE_DIR / name
    try:
        if path.suffix.lower() == ".png":
            # Đảm bảo PNG không chứa ICC/exif để tránh cảnh báo
            with Image.open(path) as im:
                im = im.convert("RGBA")
                im.info.pop("icc_profile", None)
                im.info.pop("exif", None)
                buf = BytesIO()
                im.save(buf, format="PNG", optimize=True)
                buf.seek(0)
                surf = pygame.image.load(buf, name)
        else:
            surf = pygame.image.load(str(path))

        if size:
            surf = pygame.transform.smoothscale(surf, size)
        return surf.convert_alpha()
    except Exception as e:
        print(f"[❌ load_image] Không thể tải '{name}': {e}")
        raise


# ============================================================
# HÀM LOAD ÂM THANH (TỰ KHỞI TẠO MIXER)
# ============================================================
def load_sound(filename):
    """Load âm thanh từ thư mục SOUND_DIR"""
    sound_path = SOUND_DIR / filename
    
    # Debug: In ra đường dẫn
    print(f"[DEBUG] 🔍 Đang load sound: {sound_path}")
    
    if not sound_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {sound_path}")
    
    try:
        sound = pygame.mixer.Sound(str(sound_path))
        print(f"[DEBUG] ✅ Sound loaded thành công: {filename}")
        return sound
    except pygame.error as e:
        print(f"[ERROR] ❌ Lỗi load sound '{filename}': {e}")
        return None
    # Khởi tạo mixer nếu chưa có
    if pygame.mixer.get_init() is None:
        try:
            pygame.mixer.init()
            print("[✅ Mixer đã khởi tạo]")
        except Exception as e:
            print(f"[⚠️ Không thể khởi tạo mixer]: {e}")
            return None

    try:
        sound = pygame.mixer.Sound(str(path))
        print(f"[🎵 Đã nạp âm thanh]: {path.name}")
        return sound
    except Exception as e:
        print(f"[⚠️ Lỗi khi nạp âm thanh '{path.name}']: {e}")
        return None


# ============================================================
# FONT (FREETYPE)
# ============================================================
def load_font(path_like, size: int):
    import pygame.freetype as ft
    if not ft.get_init():
        ft.init()

    font_path = None
    try:
        if path_like:
            p = Path(path_like)
            if p.is_file() and p.stat().st_size > 0:
                font_path = str(p)
    except Exception as e:
        print(f"[load_font] path check error: {e}")

    try:
        return ft.Font(font_path, size)
    except Exception as e:
        print(f"[load_font] open '{font_path}' failed: {e} -> fallback default")
        return ft.Font(None, size)


# ============================================================
# HÀM TÍNH SỐ SAO THEO MẠNG
# ============================================================
def stars_from_lives(lives: int) -> int:
    if lives >= 3:
        return 3
    elif lives == 2:
        return 2
    elif lives == 1:
        return 1
    return 0


# ============================================================
# LOAD / SAVE TIẾN TRÌNH NGƯỜI CHƠI
# ============================================================
def load_progress() -> dict:
    try:
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                unlocked = int(data.get("unlocked_level", 1))
                stars = data.get("stars", [0] * 10)
                if not isinstance(stars, list) or len(stars) != 10:
                    stars = [0] * 10
                stars = [max(0, min(3, int(x))) for x in stars]
                return {
                    "unlocked_level": max(1, min(10, unlocked)),
                    "stars": stars,
                }
    except Exception as e:
        print("[progress] load error:", e)
    return {"unlocked_level": 1, "stars": [0] * 10}


def save_progress(unlocked_level: int, stars: list[int]) -> None:
    try:
        PROGRESS_FILE.parent.mkdir(exist_ok=True)
        unlocked_level = max(1, min(10, int(unlocked_level)))
        if not isinstance(stars, list) or len(stars) != 10:
            stars = [0] * 10
        stars = [max(0, min(3, int(x))) for x in stars]
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({"unlocked_level": unlocked_level, "stars": stars}, f)
    except Exception as e:
        print("[progress] save error:", e)


# ============================================================
# LIỆT KÊ DANH SÁCH BACKGROUND
# ============================================================
def list_background_files() -> list[str]:
    """Liệt kê tất cả background files (images và videos)"""
    image_exts = {".jpg", ".jpeg", ".png"}
    video_exts = {".mp4", ".avi", ".mov", ".mkv"}
    bg_dir = IMAGE_DIR / "backgrounds"
    files = []
    try:
        for p in bg_dir.iterdir():
            if p.is_file() and (p.suffix.lower() in image_exts or p.suffix.lower() in video_exts):
                files.append(str(p.relative_to(IMAGE_DIR)).replace("\\", "/"))
    except FileNotFoundError:
        pass
    return sorted(files)


def is_video_file(filename: str) -> bool:
    """Kiểm tra xem file có phải video không"""
    video_exts = {".mp4", ".avi", ".mov", ".mkv"}
    return Path(filename).suffix.lower() in video_exts


# ============================================================
# ÁNH XẠ BACKGROUND VỚI MUSIC
# ============================================================
def get_music_for_background(background_name: str) -> str:
    """
    Trả về tên file nhạc tương ứng với background.
    Ví dụ: background1.jpg -> music1.mp3
    """
    # Mapping giữa background và music
    bg_music_map = {
        "backgrounds/background1.jpg": "music1.mp3",
        "backgrounds/background2.png": "music2.mp3",
        "backgrounds/background3.jpg": "music3.mp3",
        "backgrounds/background4.jpg": "music4.mp3",
        "backgrounds/background5.jpg": "music5.mp3",
        "backgrounds/background6.jpg": "music6.mp3",
    }
    
    # Trả về music tương ứng, hoặc mặc định music1.mp3
    return bg_music_map.get(background_name, "music1.mp3")


def get_music_path(filename: str) -> str:
    """Trả về đường dẫn đầy đủ tới file nhạc"""
    return str(SOUND_DIR / filename)
