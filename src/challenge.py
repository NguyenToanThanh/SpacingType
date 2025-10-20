# src/challenge.py
import pygame
from .settings import CHALLENGE_LEVELS, WIDTH, HEIGHT, WHITE, STAR_IMAGE_NAME, FPS, FONT_BOLD, SOUND_DIR
from .utils import load_image, stars_from_lives, load_font
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
class Challenge:
    def __init__(self, screen, background):
        self.screen = screen
        self.background = background
        try:
            self.star_img = load_image(STAR_IMAGE_NAME, (36, 36))
        except Exception:
            self.star_img = None
        # fonts (freetype)
        self.title_font = load_font(FONT_BOLD, 42)
        self.ui_font    = load_font(FONT_BOLD, 24)

    def run(self, level: int):

        import src.settings as S
        from .game import Game  

        # --- 1) Chuẩn hóa level & thiết lập thông số ---
        level = max(1, min(10, int(level)))
        speed = CHALLENGE_LEVELS[level - 1]          
        target_kills = 8 + 2 * (level - 1)           

        original_speed = S.ENEMY_SPEED
        S.ENEMY_SPEED = speed

        # --- 2) Tạo game và truyền tiêu chí qua màn ---
        game = Game()
        game.background = self.background
        game.target_kills = target_kills

        # --- 3) Chạy game (kết thúc khi đủ kill hoặc hết mạng/đóng cửa sổ) ---
        game.run()

        # --- 4) Thu kết quả ---
        completed   = bool(getattr(game, "completed", False))
        lives_left  = int(getattr(game, "lives", 0))
        score       = int(getattr(game, "score", 0))
        user_quit   = bool(getattr(game, "request_quit", False))

        # --- 5) Hiển thị màn kết quả (nếu người chơi không bấm X thoát) ---
        #   - Clear: tính số sao theo số mạng
        #   - Failed: sao = 0
        if not user_quit:
            if completed:
                stars = self._show_level_result(lives_left, title=f"Level {level} Clear!")
            else:
                stars = 0
                self._show_failed(title=f"Level {level} Failed!")
        else:
            # người chơi đóng cửa sổ: không popup, sao = 0
            stars = 0

        # --- 6) Khôi phục tốc độ gốc ---
        S.ENEMY_SPEED = original_speed

        # --- 7) Trả về cho main: (completed, stars, score, lives) ---
        return completed, stars, score, lives_left



    # ---------- UI helpers ----------
    def _show_level_result(self, lives_left: int, title: str) -> int:
        stars = stars_from_lives(lives_left)
        clock = pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return stars
                if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                    return stars

            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill((10, 10, 20))

            title_surf, _ = self.title_font.render(title, WHITE)
            self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 60)))

            # vẽ sao
            cx = WIDTH//2 - 60
            for i in range(stars):
                if self.star_img:
                    self.screen.blit(self.star_img, (cx + i*40, HEIGHT//2 - 10))
                else:
                    self._draw_star(self.screen, (cx + i*40 + 18, HEIGHT//2 + 8), 16, WHITE)

            sub_surf, _ = self.ui_font.render("Press any key to continue", WHITE)
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 70)))

            pygame.display.flip()
            clock.tick(FPS)

    def _show_failed(self, title: str):
        clock = pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                    return

            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill((10, 10, 20))

            title_surf, _ = self.title_font.render(title, WHITE)
            self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))

            sub_surf, _ = self.ui_font.render("Press any key to continue", WHITE)
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))

            pygame.display.flip()
            clock.tick(FPS)

    def _draw_star(self, surf, center, r, color):
        import math
        x0, y0 = center
        pts = []
        for i in range(10):
            ang = -math.pi/2 + i * math.pi/5
            rr = r if i % 2 == 0 else r * 0.5
            pts.append((x0 + rr*math.cos(ang), y0 + rr*math.sin(ang)))
        pygame.draw.polygon(surf, color, pts)
