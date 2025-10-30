# ============================================================
# SPACE TYPING GAME - MAIN MENU
# ============================================================
# File: menu.py
# Mô tả: Giao diện menu chính với buttons và hiệu ứng
# Chức năng chính:
#   - Button class với hover effects, shadow, scale animation
#   - MainMenu class điều khiển giao diện menu chính
#   - Gradient background với overlay
#   - Callbacks để chuyển state (Classic, Challenge, Leaderboard, Exit)
#   - Xử lý input (mouse hover, click, ESC key)
# ============================================================

import pygame
import pygame.freetype as ft
from .utils import load_font
from .settings import WIDTH, HEIGHT, WHITE, FONT_BOLD

# ==============================
# 🎨 BUTTON CLASS
# ==============================
class Button:
    """
    Nút bấm với hiệu ứng hover, shadow và scale animation.
    
    Attributes:
        text (str): Text hiển thị trên nút
        rect (pygame.Rect): Vùng nút (để detect collision)
        on_click (callable): Callback khi click
        hover (bool): Đang hover hay không
        scale_factor (float): Tỷ lệ phóng to khi hover (1.0 = normal, 1.05 = hover)
    
    Hiệu ứng:
        - Shadow: Bóng đổ phía sau nút
        - Hover color: Đổi màu khi hover
        - Border: Viền sáng khi hover
        - Scale: Phóng to nhẹ 5% khi hover
    """
    def __init__(self, text, center, on_click, w=280, h=70):
        """
        Khởi tạo Button.
        
        Args:
            text (str): Text hiển thị
            center (tuple): Toạ độ trung tâm (x, y)
            on_click (callable): Hàm callback khi click
            w (int): Chiều rộng nút (default: 280)
            h (int): Chiều cao nút (default: 70)
        """
        self.text = text
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = center
        self.on_click = on_click
        self.hover = False
        self.font = load_font(FONT_BOLD, 32)

        # 🎨 Màu sắc & hiệu ứng
        self.base_color = (40, 40, 60)       # Màu nền bình thường
        self.hover_color = (80, 80, 120)     # Màu nền khi hover
        self.border_color = (120, 120, 200)  # Màu viền khi hover
        self.shadow_offset = 5               # Khoảng cách shadow
        self.scale_factor = 1.0              # Hiệu ứng phóng nhẹ khi hover

    def draw(self, surf):
        """
        Vẽ nút lên surface.
        
        Args:
            surf (pygame.Surface): Surface để vẽ
            
        Vẽ theo thứ tự:
            1. Shadow (phía sau, offset 5px)
            2. Background (màu thay đổi khi hover)
            3. Border (chỉ khi hover)
            4. Text (căn giữa)
        """
        # Scale nhẹ khi hover
        current_w = int(self.rect.width * self.scale_factor)
        current_h = int(self.rect.height * self.scale_factor)
        scaled_rect = pygame.Rect(0, 0, current_w, current_h)
        scaled_rect.center = self.rect.center

        # Vẽ shadow nhẹ phía sau
        shadow_rect = scaled_rect.move(self.shadow_offset, self.shadow_offset)
        pygame.draw.rect(surf, (10, 10, 20), shadow_rect, border_radius=16)

        # Vẽ nền nút
        bg_color = self.hover_color if self.hover else self.base_color
        pygame.draw.rect(surf, bg_color, scaled_rect, border_radius=16)

        # Vẽ viền khi hover
        if self.hover:
            pygame.draw.rect(surf, self.border_color, scaled_rect, 3, border_radius=16)

        # Render chữ (căn giữa)
        text_surf, _ = self.font.render(self.text, WHITE)
        surf.blit(text_surf, text_surf.get_rect(center=scaled_rect.center))

    def handle(self, event):
        """
        Xử lý input events cho nút.
        
        Args:
            event (pygame.Event): Event cần xử lý
            
        Events:
            - MOUSEMOTION: Update hover state và scale_factor
            - MOUSEBUTTONDOWN (left click): Gọi callback nếu click vào nút
        """
        if event.type == pygame.MOUSEMOTION:
            hovering = self.rect.collidepoint(event.pos)
            if hovering and not self.hover:
                self.scale_factor = 1.05  # Phóng nhẹ khi mới hover
            elif not hovering and self.hover:
                self.scale_factor = 1.0   # Trở về bình thường khi rời khỏi
            self.hover = hovering

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()  # Gọi callback

# ==============================
# 🌌 MAIN MENU CLASS
# ==============================
    def __init__(self, text, center, on_click, w=280, h=70):
        self.text = text
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = center
        self.on_click = on_click
        self.hover = False
        self.font = load_font(FONT_BOLD, 32)

        # 🎨 màu & hiệu ứng
        self.base_color = (40, 40, 60)
        self.hover_color = (80, 80, 120)
        self.border_color = (120, 120, 200)
        self.shadow_offset = 5
        self.scale_factor = 1.0  # hiệu ứng phóng nhẹ khi hover

    def draw(self, surf):
        # Scale nhẹ khi hover
        current_w = int(self.rect.width * self.scale_factor)
        current_h = int(self.rect.height * self.scale_factor)
        scaled_rect = pygame.Rect(0, 0, current_w, current_h)
        scaled_rect.center = self.rect.center

        # Vẽ shadow nhẹ phía sau
        shadow_rect = scaled_rect.move(self.shadow_offset, self.shadow_offset)
        pygame.draw.rect(surf, (10, 10, 20), shadow_rect, border_radius=16)

        # Vẽ nền nút
        bg_color = self.hover_color if self.hover else self.base_color
        pygame.draw.rect(surf, bg_color, scaled_rect, border_radius=16)

        # Vẽ viền khi hover
        if self.hover:
            pygame.draw.rect(surf, self.border_color, scaled_rect, 3, border_radius=16)

        # Render chữ
        text_surf, _ = self.font.render(self.text, WHITE)
        surf.blit(text_surf, text_surf.get_rect(center=scaled_rect.center))

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            hovering = self.rect.collidepoint(event.pos)
            if hovering and not self.hover:
                self.scale_factor = 1.05  # phóng nhẹ khi mới hover
            elif not hovering and self.hover:
                self.scale_factor = 1.0
            self.hover = hovering

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

# ==============================
# 🌌 MAIN MENU CLASS
# ==============================
class MainMenu:
    """
    Giao diện menu chính của game.
    
    Attributes:
        buttons (list): Danh sách 3 nút chính (Classic, Challenge, Leaderboard)
        exit_button (Button): Nút Exit ở góc trái dưới
        should_quit (bool): Flag để báo hiệu thoát game
        background (Surface): Background image (optional)
    
    Input:
        - Mouse: Hover và click vào buttons
        - ESC: Thoát game (set should_quit = True)
    
    Layout:
        - Title: "SPACE TYPING" (center, top)
        - Subtitle: "Master your speed & accuracy"
        - 3 buttons chính: Classic, Challenge, Leaderboard (center)
        - Exit button: Góc trái dưới
    """
    def __init__(self, on_classic, on_challenge, on_leaderboard, background=None):
        """
        Khởi tạo MainMenu.
        
        Args:
            on_classic (callable): Callback khi chọn Classic
            on_challenge (callable): Callback khi chọn Challenge
            on_leaderboard (callable): Callback khi chọn Leaderboard
            background (Surface, optional): Background image
        """
        self.on_classic = on_classic
        self.on_challenge = on_challenge
        self.on_leaderboard = on_leaderboard
        self.title_font = load_font(FONT_BOLD, 64)
        self.subtitle_font = load_font(FONT_BOLD, 22)
        self.should_quit = False  # Flag để báo hiệu thoát game

        cx = WIDTH // 2
        cy = HEIGHT // 2

        # 3 nút chính
        self.buttons = [
            Button("Classic",     (cx, cy - 50), self.on_classic),
            Button("Challenge",   (cx, cy + 40), self.on_challenge),
            Button("Leaderboard", (cx, cy + 130), self.on_leaderboard),
        ]
        
        # Nút Exit ở góc trái dưới
        self.exit_button = Button("Exit", (100, HEIGHT - 50), self.on_exit, w=150, h=50)
        
        self.background = background
    
    def on_exit(self):
        """Callback khi nhấn nút Exit - set flag should_quit = True."""
        self.should_quit = True

    def _draw_gradient_background(self, surf):
        """
        Vẽ gradient background từ tối (top) đến sáng (bottom).
        
        Args:
            surf (pygame.Surface): Surface để vẽ
            
        Colors:
            - Top: (10, 10, 25) - Xanh đen tối
            - Bottom: (35, 35, 65) - Xanh đen sáng hơn
        """
        top_color = (10, 10, 25)
        bottom_color = (35, 35, 65)
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

    def draw(self, surf):
        """
        Vẽ toàn bộ menu lên surface.
        
        Args:
            surf (pygame.Surface): Surface để vẽ
            
        Thứ tự vẽ:
            1. Gradient background
            2. Background image (nếu có) với overlay tối 100 alpha
            3. Title "SPACE TYPING" với glow effect
            4. Subtitle "Master your speed & accuracy"
            5. 3 buttons chính
            6. Exit button
        """
        # Gradient nền
        self._draw_gradient_background(surf)

        # Nếu có background → phủ mờ (overlay alpha 100)
        if self.background:
            bg = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
            surf.blit(bg, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))  # Đen mờ 100 alpha
            surf.blit(overlay, (0, 0))

        # Tiêu đề với glow effect
        title_surf, _ = self.title_font.render("SPACE TYPING", WHITE)
        glow = pygame.Surface(title_surf.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(glow, (120, 120, 255, 60), glow.get_rect(), border_radius=20)
        surf.blit(glow, title_surf.get_rect(center=(WIDTH // 2, 140)))
        surf.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 140)))

        # Subtitle
        sub_surf, _ = self.subtitle_font.render("Master your speed & accuracy", (180, 180, 200))
        surf.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, 190)))

        # Vẽ các nút
        for b in self.buttons:
            b.draw(surf)
        
        # Vẽ nút Exit
        self.exit_button.draw(surf)

    def handle(self, event):
        """
        Xử lý input events cho menu chính.
        
        Args:
            event (pygame.Event): Event cần xử lý
            
        Events:
            - Mouse events: Chuyển cho buttons xử lý
            
        Note: 
            ESC không được dùng để thoát từ menu chính (để tránh xung đột với ESC từ 
            các màn hình con). Người dùng phải dùng nút Exit hoặc nút X của cửa sổ.
        """
        # Xử lý các nút menu
        for b in self.buttons:
            b.handle(event)
        
        # Xử lý nút Exit
        self.exit_button.handle(event)