import pygame
from .utils import load_font, load_image
from .settings import WIDTH, HEIGHT, FONT_BOLD, SOUND_DIR
from src.game import Game

def start_classic_mode():
    pygame.mixer.music.stop()
    pygame.mixer.music.load(str(SOUND_DIR / "classic_bgm.mp3"))
    pygame.mixer.music.play(-1)
    Game(mode="classic").run()

def start_challenge_mode():
    pygame.mixer.music.stop()
    pygame.mixer.music.load(str(SOUND_DIR / "challenge_bgm.mp3"))
    pygame.mixer.music.play(-1)
    Game(mode="challenge").run()
BTN_W, BTN_H = 90, 70
GAP = 20

class LevelSelect:
    def __init__(self, unlocked_level: int, stars: list[int]):
        self.unlocked = max(1, min(10, int(unlocked_level)))
        self.stars = (stars[:] + [0]*10)[:10]  # luôn đủ 10 phần tử
        self.title_font = load_font(FONT_BOLD, 52)
        self.num_font = load_font(FONT_BOLD, 36)

        # Tải icon sao & khóa
        try:
            self.star_img = load_image("star.png", (22, 22))
        except:
            self.star_img = None

        try:
            self.lock_img = load_image("lock.png", (26, 26))
        except:
            self.lock_img = None

        self.buttons = []
        self._layout()
        self.hover_level = None

    def _layout(self):
        cols, rows = 5, 2
        total_w = cols * BTN_W + (cols - 1) * GAP
        total_h = rows * BTN_H + (rows - 1) * GAP
        self.start_x = (WIDTH - total_w) // 2
        self.start_y = (HEIGHT - total_h) // 2
        self.buttons.clear()

        level = 1
        for r in range(rows):
            for c in range(cols):
                x = self.start_x + c * (BTN_W + GAP)
                y = self.start_y + r * (BTN_H + GAP)
                rect = pygame.Rect(x, y, BTN_W, BTN_H)
                locked = level > self.unlocked
                self.buttons.append((rect, level, locked))
                level += 1

    def _draw_background(self, surf):
        # Gradient nền
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
        if event.type == pygame.MOUSEMOTION:
            self.hover_level = None
            mx, my = event.pos
            for rect, level, locked in self.buttons:
                if not locked and rect.collidepoint(mx, my):
                    self.hover_level = level
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for rect, level, locked in self.buttons:
                if not locked and rect.collidepoint(mx, my):
                    return level
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return -1  # Trả về -1 để báo hiệu muốn thoát về menu
        
        return None

    def draw(self, surf):
        self._draw_background(surf)
        title_surf, _ = self.title_font.render("CHỌN LEVEL", (255, 255, 255))
        surf.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, 100)))
        
        # Hướng dẫn ESC
        hint_font = load_font(FONT_BOLD, 22)
        hint_surf, _ = hint_font.render("Press ESC to return to menu", (180, 180, 180))
        surf.blit(hint_surf, hint_surf.get_rect(center=(WIDTH//2, HEIGHT - 40)))

        for rect, level, locked in self.buttons:
            is_hover = (level == self.hover_level)

            # Shadow đa lớp cho nút
            shadow_rect = rect.move(4, 4)
            pygame.draw.rect(surf, (10, 10, 20), shadow_rect, border_radius=16)
            pygame.draw.rect(surf, (20, 20, 30), shadow_rect.inflate(6, 6), border_radius=16)

            # Màu nút
            if locked:
                bg = (60, 60, 60)
            else:
                bg = (90, 120, 200) if not is_hover else (130, 160, 240)

            draw_rect = rect.copy()
            if is_hover:
                draw_rect.inflate_ip(10, 10)

                # hiệu ứng glow
                glow_surf = pygame.Surface((draw_rect.width+20, draw_rect.height+20), pygame.SRCALPHA)
                pygame.draw.ellipse(glow_surf, (150, 180, 255, 80), glow_surf.get_rect())
                surf.blit(glow_surf, glow_surf.get_rect(center=draw_rect.center))

            pygame.draw.rect(surf, bg, draw_rect, border_radius=16)
            if not locked:
                pygame.draw.rect(surf, (180, 200, 255), draw_rect, 2, border_radius=16)

            # Số level hoặc ổ khóa
            if locked and self.lock_img:
                surf.blit(self.lock_img, self.lock_img.get_rect(center=draw_rect.center))
            else:
                num_surf, _ = self.num_font.render(str(level), (255, 255, 255))
                surf.blit(num_surf, num_surf.get_rect(center=(draw_rect.centerx, draw_rect.centery - 8)))

            # Sao ⭐
            if not locked and self.star_img:
                n = max(0, min(3, int(self.stars[level - 1])))
                if n > 0:
                    total_w = n * self.star_img.get_width() + (n - 1) * 6
                    start_x = draw_rect.centerx - total_w // 2
                    y = draw_rect.bottom - self.star_img.get_height() - 6
                    for i in range(n):
                        surf.blit(self.star_img, (start_x + i * (self.star_img.get_width() + 6), y))
                        