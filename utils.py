# ============================================================
# utils.py - Các hàm tiện ích dùng chung trong game
# ============================================================
# File này chứa các hàm helper để:
# - Load hình ảnh, âm thanh, font
# - Xử lý JSON (save/load)
# - Quản lý tiến trình game
# - Liệt kê background files

import pygame  # Thư viện game engine
import json    # Xử lý file JSON (save data)
from io import BytesIO  # Đọc/ghi dữ liệu trong bộ nhớ
from pathlib import Path  # Xử lý đường dẫn file/folder
from .settings import IMAGE_DIR, SOUND_DIR, PROGRESS_FILE  # Import paths từ settings
from PIL import Image  # Thư viện xử lý ảnh (Pillow)

# ============================================================
# HÀM XỬ LÝ JSON AN TOÀN
# ============================================================

def safe_json_load(path: Path, default):
    """
    Load file JSON một cách an toàn.
    
    Args:
        path: Đường dẫn đến file JSON
        default: Giá trị mặc định trả về nếu load thất bại
        
    Returns:
        Dữ liệu từ JSON hoặc giá trị default nếu lỗi
    """
    try:
        if Path(path).exists():  # Kiểm tra file có tồn tại không
            with open(path, "r", encoding="utf-8") as f:  # Mở file với UTF-8
                return json.load(f)  # Parse JSON thành dict/list
    except Exception:
        pass  # Bỏ qua mọi lỗi (file corrupt, permission denied, etc.)
    return default  # Trả về giá trị mặc định


def safe_json_save(path: Path, data):
    """
    Lưu dữ liệu vào file JSON một cách an toàn.
    Tự động tạo thư mục cha nếu chưa tồn tại.
    
    Args:
        path: Đường dẫn file cần lưu
        data: Dữ liệu (dict/list) cần lưu
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)  # Tạo thư mục cha (mkdir -p)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)  # Lưu JSON có format đẹp


# ============================================================
# HÀM LOAD HÌNH ẢNH (HỖ TRỢ PNG, JPG)
# ============================================================

def load_image(name, size=None):
    """
    Load hình ảnh từ thư mục IMAGE_DIR và tự động xử lý.
    
    Args:
        name: Tên file ảnh (vd: "spaceship.png")
        size: Tuple (width, height) để resize. None = giữ nguyên kích thước
        
    Returns:
        pygame.Surface đã convert_alpha() (tối ưu cho vẽ)
        
    Raises:
        Exception nếu không load được ảnh
    """
    path = IMAGE_DIR / name  # Ghép đường dẫn: IMAGE_DIR + name
    
    try:
        if path.suffix.lower() == ".png":
            # ===== XỬ LÝ ĐỘC BIỆT CHO PNG =====
            # PNG có thể chứa ICC profile/EXIF metadata → gây warning
            # → Xóa metadata và re-save trong memory
            
            with Image.open(path) as im:  # Mở ảnh bằng Pillow
                im = im.convert("RGBA")  # Chuyển sang RGBA (có alpha channel)
                im.info.pop("icc_profile", None)  # Xóa ICC color profile
                im.info.pop("exif", None)         # Xóa EXIF metadata
                
                # Lưu lại PNG "sạch" vào memory buffer
                buf = BytesIO()
                im.save(buf, format="PNG", optimize=True)
                buf.seek(0)  # Về đầu buffer để đọc
                
                # Load vào pygame từ buffer
                surf = pygame.image.load(buf, name)
        else:
            # ===== XỬ LÝ THƯỜNG CHO JPG, GIF, ETC. =====
            surf = pygame.image.load(str(path))

        # Resize nếu có yêu cầu
        if size:
            surf = pygame.transform.smoothscale(surf, size)  # Scale mượt mà
        
        return surf.convert_alpha()  # Convert để vẽ nhanh hơn
        
    except Exception as e:
        print(f"[❌ load_image] Không thể tải '{name}': {e}")
        raise  # Throw lỗi ra ngoài để caller xử lý


# ============================================================
# HÀM LOAD ÂM THANH (TỰ ĐỘNG KHỞI TẠO MIXER)
# ============================================================

def load_sound(filename):
    """
    Load file âm thanh từ thư mục SOUND_DIR.
    Tự động khởi tạo pygame.mixer nếu chưa có.
    Hỗ trợ cả script Python và .exe (dùng SOUND_DIR từ settings).
    
    Args:
        filename: Tên file âm thanh (vd: "ban.wav", "music1.mp3")
        
    Returns:
        pygame.mixer.Sound object hoặc None nếu lỗi
    """
    # ===== KHỞI TẠO MIXER (NẾU CHƯA CÓ) =====
    if pygame.mixer.get_init() is None:  # Kiểm tra mixer đã init chưa
        try:
            pygame.mixer.init()  # Khởi tạo audio system
            print("[✅ Mixer đã khởi tạo]")
        except Exception as e:
            print(f"[⚠️ Không thể khởi tạo mixer]: {e}")
            return None  # Không có audio → trả về None

    # ===== TÌM FILE ÂM THANH =====
    # SOUND_DIR tự động là đường dẫn đúng (script hay .exe)
    sound_path = SOUND_DIR / filename
    
    print(f"[🔍 Load sound]: {sound_path}")
    
    # Kiểm tra file có tồn tại không
    if not sound_path.exists():
        print(f"[❌ File không tồn tại]: {sound_path}")
        return None
    
    # ===== LOAD ÂM THANH =====
    try:
        sound = pygame.mixer.Sound(str(sound_path))  # Load file vào Sound object
        print(f"[✅ Sound loaded]: {filename}")
        return sound
    except Exception as e:
        print(f"[❌ Lỗi load sound '{filename}']: {e}")
        return None  # Trả về None nếu lỗi (game vẫn chạy được, chỉ không có âm thanh)


# ============================================================
# HÀM LOAD FONT CHỮ (FREETYPE)
# ============================================================

def load_font(path_like, size: int):
    """
    Load font chữ từ file TTF/OTF hoặc dùng font mặc định.
    Sử dụng pygame.freetype (hỗ trợ Unicode tốt hơn pygame.font).
    
    Args:
        path_like: Đường dẫn đến file font (Path object hoặc str). None = font mặc định
        size: Kích thước font (pixel)
        
    Returns:
        pygame.freetype.Font object
    """
    import pygame.freetype as ft
    
    # Khởi tạo FreeType module nếu chưa có
    if not ft.get_init():
        ft.init()

    font_path = None  # Mặc định dùng system font
    
    # ===== KIỂM TRA ĐƯỜNG DẪN FONT =====
    try:
        if path_like:
            p = Path(path_like)
            # Kiểm tra file có tồn tại và không rỗng
            if p.is_file() and p.stat().st_size > 0:
                font_path = str(p)  # Dùng font này
    except Exception as e:
        print(f"[load_font] path check error: {e}")

    # ===== LOAD FONT =====
    try:
        return ft.Font(font_path, size)  # Load font với size
    except Exception as e:
        print(f"[load_font] open '{font_path}' failed: {e} -> fallback default")
        return ft.Font(None, size)  # Fallback sang font mặc định của hệ thống


# ============================================================
# HÀM TÍNH SỐ SAO (STARS) DỰA TRÊN SỐ MẠNG CÒN LẠI
# ============================================================

def stars_from_lives(lives: int) -> int:
    """
    Chuyển đổi số mạng còn lại thành số sao (★).
    Dùng trong Challenge mode khi hoàn thành level.
    
    Args:
        lives: Số mạng còn lại (0-3)
        
    Returns:
        Số sao (0-3):
        - 3 mạng → 3 sao ★★★ (hoàn hảo)
        - 2 mạng → 2 sao ★★☆
        - 1 mạng → 1 sao ★☆☆
        - 0 mạng → 0 sao ☆☆☆ (thua)
    """
    if lives >= 3:
        return 3
    elif lives == 2:
        return 2
    elif lives == 1:
        return 1
    return 0  # 0 mạng = 0 sao


# ============================================================
# LOAD / SAVE TIẾN TRÌNH NGƯỜI CHƠI (CHALLENGE MODE)
# ============================================================

def load_progress() -> dict:
    """
    Load tiến trình Challenge mode từ file progress.json.
    
    Returns:
        Dict với 2 key:
        - "unlocked_level": Level cao nhất đã mở (1-10)
        - "stars": List 10 số sao cho mỗi level [0-3, 0-3, ...]
        
    Nếu file không tồn tại hoặc lỗi, trả về progress mặc định:
        {"unlocked_level": 1, "stars": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}
    """
    try:
        if PROGRESS_FILE.exists():  # Kiểm tra file có tồn tại không
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)  # Parse JSON
                
                # Lấy unlocked_level (giới hạn 1-10)
                unlocked = int(data.get("unlocked_level", 1))
                
                # Lấy stars list (phải có đúng 10 phần tử)
                stars = data.get("stars", [0] * 10)
                if not isinstance(stars, list) or len(stars) != 10:
                    stars = [0] * 10  # Reset nếu không đúng format
                
                # Giới hạn mỗi giá trị sao trong khoảng 0-3
                stars = [max(0, min(3, int(x))) for x in stars]
                
                return {
                    "unlocked_level": max(1, min(10, unlocked)),  # Clamp 1-10
                    "stars": stars,
                }
    except Exception as e:
        print("[progress] load error:", e)
    
    # Trả về progress mặc định nếu lỗi
    return {"unlocked_level": 1, "stars": [0] * 10}


def save_progress(unlocked_level: int, stars: list[int]) -> None:
    """
    Lưu tiến trình Challenge mode vào file progress.json.
    
    Args:
        unlocked_level: Level cao nhất đã unlock (1-10)
        stars: List 10 số sao [0-3] cho từng level
        
    Note:
        - Tự động tạo thư mục save/ nếu chưa có
        - Tự động validate và clamp giá trị hợp lệ
    """
    try:
        # Tạo thư mục save nếu chưa có
        PROGRESS_FILE.parent.mkdir(exist_ok=True)
        
        # Validate và clamp unlocked_level (1-10)
        unlocked_level = max(1, min(10, int(unlocked_level)))
        
        # Validate stars list
        if not isinstance(stars, list) or len(stars) != 10:
            stars = [0] * 10  # Reset nếu không hợp lệ
        
        # Clamp mỗi giá trị sao (0-3)
        stars = [max(0, min(3, int(x))) for x in stars]
        
        # Lưu vào file JSON
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({"unlocked_level": unlocked_level, "stars": stars}, f)
            
    except Exception as e:
        print("[progress] save error:", e)


# ============================================================
# LIỆT KÊ VÀ KIỂM TRA BACKGROUND FILES
# ============================================================

def list_background_files() -> list[str]:
    """
    Liệt kê tất cả file background (ảnh + video) trong thư mục backgrounds/.
    
    Returns:
        List tên file (relative path):
        ["backgrounds/bg1.jpg", "backgrounds/bg2.mp4", ...]
        
    Hỗ trợ:
        - Images: .jpg, .jpeg, .png
        - Videos: .mp4, .avi, .mov, .mkv
    """
    # Định nghĩa các extension được hỗ trợ
    image_exts = {".jpg", ".jpeg", ".png"}
    video_exts = {".mp4", ".avi", ".mov", ".mkv"}
    
    bg_dir = IMAGE_DIR / "backgrounds"  # Thư mục chứa backgrounds
    files = []
    
    try:
        # Duyệt qua tất cả file trong thư mục
        for p in bg_dir.iterdir():
            # Chỉ lấy file (không lấy folder)
            if p.is_file():
                ext = p.suffix.lower()  # Lấy extension (.jpg, .mp4, ...)
                
                # Kiểm tra có phải ảnh hoặc video không
                if ext in image_exts or ext in video_exts:
                    # Chuyển sang relative path (tương đối IMAGE_DIR)
                    # vd: "backgrounds/bg1.jpg"
                    rel_path = str(p.relative_to(IMAGE_DIR)).replace("\\", "/")
                    files.append(rel_path)
                    
    except FileNotFoundError:
        pass  # Thư mục không tồn tại → trả về list rỗng
    
    return sorted(files)  # Sắp xếp theo tên


def is_video_file(filename: str) -> bool:
    """
    Kiểm tra xem file có phải video không (dựa trên extension).
    
    Args:
        filename: Tên file (vd: "backgrounds/video1.mp4")
        
    Returns:
        True nếu là video, False nếu là ảnh
    """
    video_exts = {".mp4", ".avi", ".mov", ".mkv"}
    return Path(filename).suffix.lower() in video_exts


# ============================================================
# ÁNH XẠ BACKGROUND → MUSIC (BACKGROUND MUSIC MATCHING)
# ============================================================

def get_music_for_background(background_name: str) -> str:
    """
    Trả về tên file nhạc phù hợp với background đang chọn.
    Mỗi background có 1 bài nhạc riêng để tạo không khí phù hợp.
    
    Args:
        background_name: Tên background file
                        vd: "backgrounds/background1.jpg"
        
    Returns:
        Tên file nhạc tương ứng
        vd: "music1.mp3"
        
    Note:
        - Nếu background không có trong map → trả về "music1.mp3" (default)
        - Có thể mở rộng map này để thêm backgrounds mới
    """
    # Dictionary ánh xạ: background → music
    bg_music_map = {
        "backgrounds/background1.jpg": "music1.mp3",
        "backgrounds/background2.png": "music2.mp3",
        "backgrounds/background3.jpg": "music3.mp3",
        "backgrounds/background4.jpg": "music4.mp3",
        "backgrounds/background5.jpg": "music5.mp3",
        "backgrounds/background6.jpg": "music6.mp3",
    }
    
    # Lookup: Tìm music tương ứng hoặc dùng music1.mp3 làm default
    return bg_music_map.get(background_name, "music1.mp3")


# ============================================================
# CHỤP MÀN HÌNH (SCREENSHOT)
# ============================================================

def take_screenshot(surface: pygame.Surface) -> str:
    """
    Chụp màn hình game và lưu vào file PNG.
    
    Args:
        surface: pygame.Surface cần chụp (thường là screen)
        
    Returns:
        Đường dẫn file đã lưu hoặc None nếu lỗi
    """
    from datetime import datetime
    
    try:
        # Tạo thư mục screenshots nếu chưa có
        screenshot_dir = Path.cwd() / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        
        # Tạo tên file với timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = screenshot_dir / filename
        
        # Lưu surface thành PNG
        pygame.image.save(surface, str(filepath))
        
        print(f"[📸 Screenshot saved]: {filepath}")
        return str(filepath)
        
    except Exception as e:
        print(f"[❌ Screenshot failed]: {e}")
        return None
