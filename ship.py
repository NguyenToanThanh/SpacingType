# ============================================================
# ship.py — Xử lý hiển thị tàu vũ trụ (Spaceship)
# ============================================================

import pygame, math
from .utils import load_image      # Hàm tiện ích để tải hình ảnh
from .settings import WIDTH, SHIP_Y  # Lấy kích thước màn hình & vị trí Y của tàu


# Biến toàn cục lưu ảnh tàu — giúp chỉ load 1 lần duy nhất
_ship_img = None


# ------------------------------------------------------------
# Hàm khởi tạo ảnh tàu (_init_ship)
# ------------------------------------------------------------
def _init_ship():
    """
    Hàm này dùng để tải hình ảnh tàu vũ trụ và chuẩn bị cho việc vẽ.
    - Nếu ảnh tàu chưa được tải (biến _ship_img là None), nó sẽ tải từ file 'spaceship.png'
    - Kích thước ảnh được resize về (80, 80)
    - Nếu ảnh không có alpha (trong suốt), thì phần nền (pixel [0,0]) sẽ được đặt làm colorkey
      => giúp bỏ nền khi vẽ lên màn hình.
    """
    global _ship_img
    if _ship_img is None:  # Chỉ tải 1 lần duy nhất
        img = load_image("spaceship.png", (80, 80))  # Tải ảnh và resize
        if img.get_alpha() is None:                  # Nếu ảnh không có kênh alpha (trong suốt)
            bg_color = img.get_at((0, 0))[:3]        # Lấy màu nền từ góc trên trái
            img.set_colorkey(bg_color)               # Đặt màu nền thành trong suốt
        _ship_img = img                              # Lưu ảnh vào biến toàn cục


# ------------------------------------------------------------
# Hàm vẽ tàu bình thường (không xoay)
# ------------------------------------------------------------
def draw_ship(surface: pygame.Surface, offset=(0, 0)):
    """
    Vẽ tàu vũ trụ ở vị trí mặc định (giữa màn hình).
    - surface: đối tượng pygame.Surface (màn hình đích để vẽ lên)
    - offset: cho phép dịch chuyển tàu (dùng trong hiệu ứng rung màn hình)
    """
    _init_ship()  # Đảm bảo ảnh tàu đã được tải
    rect = _ship_img.get_rect(
        center=(WIDTH // 2 + offset[0], SHIP_Y + offset[1])  # Căn giữa theo chiều ngang
    )
    surface.blit(_ship_img, rect)  # Vẽ ảnh tàu lên màn hình


# ------------------------------------------------------------
# Hàm vẽ tàu xoay theo góc (dùng khi ngắm kẻ địch)
# ------------------------------------------------------------
def draw_rotated_ship(surface: pygame.Surface, angle_rad: float, offset=(0, 0)):
    """
    Vẽ tàu vũ trụ với góc xoay nhất định (angle_rad — tính bằng radian).
    - Dùng trong trường hợp tàu tự động xoay nòng súng hướng về enemy bị lock.
    - offset dùng cho hiệu ứng rung hoặc dịch chuyển nhẹ.
    """

    _init_ship()  # Đảm bảo ảnh tàu đã được tải
    # Chuyển góc từ radian sang độ, đồng thời trừ 90 độ để điều chỉnh hướng mũi tàu cho đúng
    deg = -math.degrees(angle_rad) - 90  

    # Xoay ảnh theo góc đã tính
    rotated = pygame.transform.rotate(_ship_img, deg)

    # Lấy vị trí trung tâm mới sau khi xoay
    rect = rotated.get_rect(
        center=(WIDTH // 2 + offset[0], SHIP_Y + offset[1])
    )

    # Vẽ ảnh xoay lên màn hình
    surface.blit(rotated, rect)
