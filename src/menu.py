import pygame
import pygame.freetype as ft
from .utils import load_font
from .settings import WIDTH, HEIGHT, WHITE, FONT_BOLD

# ==============================
# 🎨 BUTTON CLASS
# ==============================
class Button:
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
    def __init__(self, on_classic, on_challenge, on_leaderboard, background=None):
        self.on_classic = on_classic
        self.on_challenge = on_challenge
        self.on_leaderboard = on_leaderboard
        self.title_font = load_font(FONT_BOLD, 64)
        self.subtitle_font = load_font(FONT_BOLD, 22)

        cx = WIDTH // 2
        cy = HEIGHT // 2

        self.buttons = [
            Button("Classic",     (cx, cy - 50), self.on_classic),
            Button("Challenge",   (cx, cy + 40), self.on_challenge),
            Button("Leaderboard", (cx, cy + 130), self.on_leaderboard),
        ]
        self.background = background

    def _draw_gradient_background(self, surf):
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
        # Gradient nền
        self._draw_gradient_background(surf)

        # Nếu có background → phủ mờ
        if self.background:
            bg = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
            surf.blit(bg, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surf.blit(overlay, (0, 0))

        # Tiêu đề
        title_surf, _ = self.title_font.render("SPACE TYPING", WHITE)
        glow = pygame.Surface(title_surf.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(glow, (120, 120, 255, 60), glow.get_rect(), border_radius=20)
        surf.blit(glow, title_surf.get_rect(center=(WIDTH // 2, 140)))
        surf.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 140)))

        # Subtitle
        sub_surf, _ = self.subtitle_font.render("Master your speed & accuracy", (180, 180, 200))
        surf.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, 190)))

        # Vẽ nút
        for b in self.buttons:
            b.draw(surf)

    def handle(self, event):
        for b in self.buttons:
            b.handle(event)