# ============================================================
# FILE: level_select.py
# MÔ TẢ: Màn hình chọn level cho Challenge Mode với grid 5x2 (10 levels)
#        Hiển thị lock icon cho levels chưa mở và stars cho levels đã hoàn thành
# ============================================================

import pygame
from .utils import load_font, load_image
from .settings import WIDTH, HEIGHT, FONT_BOLD, SOUND_DIR
from src.game import Game

# ============================================================
# LEGACY FUNCTIONS - Không còn sử dụng
# ============================================================
def start_classic_mode():
    """[DEPRECATED] Hiện tại main.py xử lý việc start game modes."""
    pygame.mixer.music.stop()
    pygame.mixer.music.load(str(SOUND_DIR / "music3.mp3"))
    pygame.mixer.music.play(-1)
    Game(mode="classic").run()

def start_challenge_mode():
    """[DEPRECATED] Hiện tại main.py xử lý việc start game modes."""
    pygame.mixer.music.stop()
    pygame.mixer.music.load(str(SOUND_DIR / "music5.mp3"))
    pygame.mixer.music.play(-1)
    Game(mode="challenge").run()

# ============================================================
# CONSTANTS - Kích thước buttons và spacing
# ============================================================
BTN_W, BTN_H = 90, 70  # Kích thước mỗi button level
GAP = 20               # Khoảng cách giữa các buttons

# ============================================================
# LEVEL SELECT CLASS - Grid UI cho chọn Challenge levels
# ============================================================
class LevelSelect:
    """
    Màn hình chọn level với grid 5x2 (10 levels total).
    
    Features:
    - Lock/Unlock progression: Chỉ hiển thị levels đã unlock
    - Stars display: Hiển thị 0-3 sao cho mỗi level đã hoàn thành
    - Hover effect: Phóng to và glow khi hover chuột
    - ESC to exit: Nhấn ESC để quay về menu
    
    Attributes:
        unlocked (int): Level cao nhất đã unlock (1-10)
        stars (list[int]): Danh sách 10 số, mỗi số = số sao của level đó (0-3)
        title_font (pygame.Font): Font cho tiêu đề
        num_font (pygame.Font): Font cho số level
        star_img (pygame.Surface): Icon ngôi sao
        lock_img (pygame.Surface): Icon ổ khóa
        buttons (list): Danh sách (rect, level, locked) cho mỗi button
        hover_level (int): Level đang được hover (None nếu không hover)
    """
    
    def __init__(self, unlocked_level: int, stars: list[int]):
        """
        Khởi tạo màn hình chọn level.
        
        Args:
            unlocked_level (int): Level cao nhất đã mở (1-10)
            stars (list[int]): Danh sách số sao cho mỗi level (0-3 mỗi level)
        """
        # Chuẩn hóa unlocked level (1-10)
        self.unlocked = max(1, min(10, int(unlocked_level)))
        
        # Đảm bảo stars luôn có đủ 10 phần tử
        self.stars = (stars[:] + [0]*10)[:10]
        
        # Fonts
        self.title_font = load_font(FONT_BOLD, 52)
        self.num_font = load_font(FONT_BOLD, 36)

        # Load icons (fallback: None nếu không load được)
        try:
            self.star_img = load_image("star.png", (22, 22))
        except:
            self.star_img = None

        try:
            self.lock_img = load_image("lock.png", (26, 26))
        except:
            self.lock_img = None

        self.buttons = []
        self._layout()  # Tạo layout grid 5x2
        self.hover_level = None

    def _layout(self):
        """
        Tạo layout grid 5x2 cho 10 levels.
        
        Layout:
        [1] [2] [3] [4] [5]
        [6] [7] [8] [9] [10]
        
        Mỗi button có thông tin: (rect, level_number, is_locked)
        """
        cols, rows = 5, 2
        
        # Tính tổng kích thước grid
        total_w = cols * BTN_W + (cols - 1) * GAP
        total_h = rows * BTN_H + (rows - 1) * GAP
        
        # Vị trí bắt đầu (center screen)
        self.start_x = (WIDTH - total_w) // 2
        self.start_y = (HEIGHT - total_h) // 2
        
        self.buttons.clear()
        level = 1
        for r in range(rows):
            for c in range(cols):
                # Tính vị trí button
                x = self.start_x + c * (BTN_W + GAP)
                y = self.start_y + r * (BTN_H + GAP)
                rect = pygame.Rect(x, y, BTN_W, BTN_H)
                
                # Level locked nếu > unlocked
                locked = level > self.unlocked
                
                self.buttons.append((rect, level, locked))
                level += 1

    def _draw_background(self, surf):
        """
        Vẽ gradient background cho màn hình level select.
        
        Args:
            surf (pygame.Surface): Surface để vẽ
        """
        # Gradient nền từ trên xuống dưới
        top_color = (15, 15, 40)
        bottom_color = (30, 40, 80)
        gradient = pygame.Surface((1, HEIGHT))
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            c = [
                int(top_color[i] + (bottom_color[i] - top_color[i]) * ratio)
                for i in range(3)
            ]
            gradient.set_at((0, y), c)
        gradient = pygame.transform.scale(gradient, (WIDTH, HEIGHT))
        surf.blit(gradient, (0, 0))

        # Ánh sáng trung tâm nhẹ
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow, (120, 120, 255, 50), (WIDTH // 2, HEIGHT // 2), 300)
        surf.blit(glow, (0, 0))

    def handle(self, event):
        """
        Xử lý input events cho level select.
        
        Controls:
        - Mouse hover: Hiệu ứng phóng to button
        - Left click: Chọn level (nếu không locked)
        - ESC: Quay về menu (return -1)
        
        Args:
            event (pygame.Event): Event cần xử lý
            
        Returns:
            int: Level number (1-10) nếu chọn, -1 nếu ESC, None nếu không action
        """
        if event.type == pygame.MOUSEMOTION:
            # Update hover state
            self.hover_level = None
            mx, my = event.pos
            for rect, level, locked in self.buttons:
                if not locked and rect.collidepoint(mx, my):
                    self.hover_level = level
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click chọn level
            mx, my = event.pos
            for rect, level, locked in self.buttons:
                if not locked and rect.collidepoint(mx, my):
                    return level  # Trả về level đã chọn
        
        elif event.type == pygame.KEYDOWN:
            # ESC: Quay về menu
            if event.key == pygame.K_ESCAPE:
                return -1
        
        return None

    def draw(self, surf):
        """
        Vẽ màn hình level select với grid 5x2.
        
        Components:
        - Background gradient
        - Title "SELECT LEVEL"
        - Grid 10 buttons (5x2)
        - Lock icons cho levels chưa mở
        - Stars (0-3) cho levels đã hoàn thành
        - Hint text "Press ESC to return to menu"
        
        Args:
            surf (pygame.Surface): Surface để vẽ
        """
        # Vẽ background
        self._draw_background(surf)
        
        # Vẽ tiêu đề
        title_surf, _ = self.title_font.render("SELECT LEVEL", (255, 255, 255))
        surf.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, 100)))

        # Vẽ hint text ở dưới cùng
        hint_font = load_font(FONT_BOLD, 24)
        hint_surf, _ = hint_font.render("Press ESC to return to menu", (200, 200, 200))
        surf.blit(hint_surf, hint_surf.get_rect(center=(WIDTH//2, HEIGHT - 50)))

        # Vẽ từng button level
        for rect, level, locked in self.buttons:
            is_hover = (level == self.hover_level)

            # Shadow đa lớp cho depth effect
            shadow_rect = rect.move(4, 4)
            pygame.draw.rect(surf, (10, 10, 20), shadow_rect, border_radius=16)
            pygame.draw.rect(surf, (20, 20, 30), shadow_rect.inflate(6, 6), border_radius=16)

            # Màu button (xám nếu locked, xanh nếu unlocked)
            if locked:
                bg = (60, 60, 60)
            else:
                bg = (90, 120, 200) if not is_hover else (130, 160, 240)

            # Hiệu ứng scale khi hover
            draw_rect = rect.copy()
            if is_hover:
                draw_rect.inflate_ip(10, 10)

                # Glow effect khi hover
                glow_surf = pygame.Surface((draw_rect.width+20, draw_rect.height+20), pygame.SRCALPHA)
                pygame.draw.ellipse(glow_surf, (150, 180, 255, 80), glow_surf.get_rect())
                surf.blit(glow_surf, glow_surf.get_rect(center=draw_rect.center))

            # Vẽ button background
            pygame.draw.rect(surf, bg, draw_rect, border_radius=16)
            if not locked:
                # Viền sáng cho unlocked buttons
                pygame.draw.rect(surf, (180, 200, 255), draw_rect, 2, border_radius=16)

            # Vẽ nội dung button: Lock icon hoặc số level
            if locked and self.lock_img:
                surf.blit(self.lock_img, self.lock_img.get_rect(center=draw_rect.center))
            else:
                num_surf, _ = self.num_font.render(str(level), (255, 255, 255))
                surf.blit(num_surf, num_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery - 8)))

            # Vẽ stars ở dưới button (nếu level đã hoàn thành)
            if not locked and self.star_img:
                n = max(0, min(3, int(self.stars[level - 1])))  # 0-3 sao
                if n > 0:
                    # Tính vị trí center cho n sao
                    total_w = n * self.star_img.get_width() + (n - 1) * 6
                    start_x = draw_rect.centerx - total_w // 2
                    y = draw_rect.bottom - self.star_img.get_height() - 6
                    
                    # Vẽ từng sao
                    for i in range(n):
                        surf.blit(self.star_img, (start_x + i * (self.star_img.get_width() + 6), y))
                        