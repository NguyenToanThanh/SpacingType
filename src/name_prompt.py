import pygame
from .settings import WIDTH, HEIGHT, FONT_BOLD, FPS
from .utils import load_font

class NamePrompt:
    def __init__(self, title="Enter your name"):
        self.title = title
        self.font_title = load_font(FONT_BOLD, 50)
        self.font_input = load_font(FONT_BOLD, 40)
        self.font_hint  = load_font(FONT_BOLD, 22)
        self.text = ""
        self.active = True
        self.hover = False
        self.placeholder = "Your name here..."

    def _draw_gradient_background(self, surf):
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

    def run(self, screen, background=None, default_if_empty="Player"):
        clock = pygame.time.Clock()
        pygame.key.start_text_input()

        base_box_w, box_h = 500, 70
        rect = pygame.Rect((WIDTH - base_box_w)//2, HEIGHT//2 - box_h//2, base_box_w, box_h)

        while self.active:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.key.stop_text_input()
                    return default_if_empty or "Player"
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        pygame.key.stop_text_input()
                        return default_if_empty or "Player"
                    if e.key == pygame.K_BACKSPACE:
                        if self.text:
                            self.text = self.text[:-1]
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        pygame.key.stop_text_input()
                        name = self.text.strip()
                        return name if name else (default_if_empty or "Player")
                elif e.type == pygame.TEXTINPUT:
                    self.text += e.text
                elif e.type == pygame.MOUSEMOTION:
                    self.hover = rect.collidepoint(e.pos)
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if rect.collidepoint(e.pos):
                        self.hover = True

            # Vẽ nền
            if background:
                screen.blit(background, (0, 0))
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 80))
                screen.blit(overlay, (0, 0))
            else:
                self._draw_gradient_background(screen)

            # Tiêu đề
            title_surf, _ = self.font_title.render(self.title, (255, 255, 255))
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 110)))

            # Hiệu ứng scale nhẹ khi hover
            draw_rect = rect.copy()
            if self.hover:
                draw_rect.inflate_ip(10, 8)

            # Shadow đa lớp
            shadow1 = draw_rect.move(4, 4)
            shadow2 = draw_rect.inflate(10, 10)
            pygame.draw.rect(screen, (10, 10, 20), shadow2, border_radius=14)
            pygame.draw.rect(screen, (20, 20, 30), shadow1, border_radius=14)

            # Glow nhẹ khi active
            if self.hover or self.text:
                glow_surf = pygame.Surface((draw_rect.width + 30, draw_rect.height + 30), pygame.SRCALPHA)
                pygame.draw.ellipse(glow_surf, (150, 180, 255, 60), glow_surf.get_rect())
                screen.blit(glow_surf, glow_surf.get_rect(center=draw_rect.center))

            # Viền & nền input
            pygame.draw.rect(screen, (30, 36, 56), draw_rect, border_radius=12)
            pygame.draw.rect(screen, (120, 150, 220) if self.hover else (90, 110, 160), draw_rect, width=2, border_radius=12)

            # Text nhập hoặc placeholder
            if self.text:
                text_surf, _ = self.font_input.render(self.text, (255, 255, 255))
            else:
                text_surf, _ = self.font_input.render(self.placeholder, (160, 160, 160))
            screen.blit(text_surf, text_surf.get_rect(midleft=(draw_rect.x + 20, draw_rect.centery)))

            # Hint
            hint_text = "Press ENTER to confirm • ESC to cancel"
            hint_surf, _ = self.font_hint.render(hint_text, (200, 200, 200))
            screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 90)))

            pygame.display.flip()
            clock.tick(FPS)