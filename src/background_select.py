import pygame
import cv2
import numpy as np
from pathlib import Path
from .settings import WIDTH, HEIGHT, FONT_BOLD
from .utils import load_font, load_image, is_video_file
from .settings import IMAGE_DIR

THUMB_W, THUMB_H = 200, 120
GAP = 20
ROWS, COLS = 2, 3

class BackgroundSelect:
    def __init__(self, filenames: list[str], title="Choose Background"):
        self.title = title
        self.items = filenames
        self.title_font = load_font(FONT_BOLD, 48)
        self.info_font = load_font(FONT_BOLD, 20)
        self.page = 0
        self.per_page = ROWS * COLS
        self._layout()
        self.hover_index = None
        
        # Cache video thumbnails
        self.video_thumbnails = {}
        self._load_video_thumbnails()

    def _layout(self):
        total_w = COLS * THUMB_W + (COLS - 1) * GAP
        total_h = ROWS * THUMB_H + (ROWS - 1) * GAP
        self.start_x = (WIDTH - total_w) // 2
        self.start_y = (HEIGHT - total_h) // 2
    
    def _load_video_thumbnails(self):
        """Load first frame of videos as thumbnails"""
        for filename in self.items:
            if is_video_file(filename):
                try:
                    video_path = IMAGE_DIR / filename
                    cap = cv2.VideoCapture(str(video_path))
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            # Convert BGR to RGB
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            # Resize to thumbnail size
                            frame = cv2.resize(frame, (THUMB_W, THUMB_H), interpolation=cv2.INTER_LINEAR)
                            # Convert to pygame surface
                            frame = np.transpose(frame, (1, 0, 2))
                            self.video_thumbnails[filename] = pygame.surfarray.make_surface(frame)
                        cap.release()
                except Exception as e:
                    print(f"[BackgroundSelect] Không thể load thumbnail từ {filename}: {e}")

    def _page_items(self):
        a = self.page * self.per_page
        b = a + self.per_page
        return self.items[a:b]

    def _draw_background(self, surf):
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

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_index = None
            mx, my = event.pos
            idx = 0
            for r in range(ROWS):
                for c in range(COLS):
                    x = self.start_x + c * (THUMB_W + GAP)
                    y = self.start_y + r * (THUMB_H + GAP)
                    rect = pygame.Rect(x, y, THUMB_W, THUMB_H)
                    if rect.collidepoint(mx, my) and idx < len(self._page_items()):
                        self.hover_index = idx
                    idx += 1

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return "__CANCEL__"
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                if (self.page + 1) * self.per_page < len(self.items):
                    self.page += 1
            if event.key in (pygame.K_LEFT, pygame.K_a):
                if self.page > 0:
                    self.page -= 1

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            idx = 0
            for r in range(ROWS):
                for c in range(COLS):
                    x = self.start_x + c * (THUMB_W + GAP)
                    y = self.start_y + r * (THUMB_H + GAP)
                    rect = pygame.Rect(x, y, THUMB_W, THUMB_H)
                    subs = self._page_items()
                    if idx < len(subs) and rect.collidepoint(mx, my):
                        return subs[idx]
                    idx += 1
        return None

    def draw(self, surf):
        self._draw_background(surf)
        title_surf, _ = self.title_font.render(self.title, (255, 255, 255))
        surf.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 100)))

        subs = self._page_items()
        idx = 0
        for r in range(ROWS):
            for c in range(COLS):
                x = self.start_x + c * (THUMB_W + GAP)
                y = self.start_y + r * (THUMB_H + GAP)
                rect = pygame.Rect(x, y, THUMB_W, THUMB_H)

                # Hover scale effect
                draw_rect = rect.copy()
                if idx == self.hover_index:
                    draw_rect.inflate_ip(10, 10)

                # Shadow
                shadow_rect = draw_rect.move(4, 4)
                pygame.draw.rect(surf, (10, 10, 20), shadow_rect, border_radius=10)

                # Border
                border_color = (100, 140, 220) if idx == self.hover_index else (50, 60, 80)
                pygame.draw.rect(surf, border_color, draw_rect, border_radius=10)

                # Image / label
                if idx < len(subs):
                    name = subs[idx]
                    
                    # Vẽ preview
                    if is_video_file(name):
                        # Vẽ thumbnail từ video (frame đầu tiên)
                        if name in self.video_thumbnails:
                            thumb = self.video_thumbnails[name]
                            # Scale thumbnail to fit draw_rect
                            scaled_thumb = pygame.transform.scale(thumb, (draw_rect.width, draw_rect.height))
                            surf.blit(scaled_thumb, draw_rect.topleft)
                        else:
                            # Fallback: background đen
                            pygame.draw.rect(surf, (20, 20, 30), draw_rect, border_radius=10)
                        
                        # Overlay với gradient tối phía dưới
                        overlay = pygame.Surface((draw_rect.width, 60), pygame.SRCALPHA)
                        for y in range(60):
                            alpha = int((y / 60) * 200)
                            pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y), (draw_rect.width, y))
                        surf.blit(overlay, (draw_rect.left, draw_rect.bottom - 60))
                        
                        # Icon play button nhỏ
                        center_x, center_y = draw_rect.center
                        triangle_size = 25
                        triangle_points = [
                            (center_x - triangle_size//2, center_y - triangle_size//2),
                            (center_x - triangle_size//2, center_y + triangle_size//2),
                            (center_x + triangle_size//2, center_y)
                        ]
                        # Bóng cho icon
                        shadow_points = [(x+2, y+2) for x, y in triangle_points]
                        pygame.draw.polygon(surf, (0, 0, 0, 128), shadow_points)
                        pygame.draw.polygon(surf, (255, 255, 255), triangle_points)
                        
                        # Label "ĐẶC BIỆT" thay vì "VIDEO"
                        special_label, _ = self.info_font.render("SECRET", (255, 215, 0))
                        label_rect = special_label.get_rect(center=(center_x, draw_rect.bottom - 25))
                        surf.blit(special_label, label_rect)
                    else:
                        # Image thông thường
                        try:
                            img = load_image(name, (draw_rect.width, draw_rect.height))
                            surf.blit(img, draw_rect.topleft)
                        except Exception:
                            label, _ = self.info_font.render(Path(name).name, (255, 255, 255))
                            surf.blit(label, label.get_rect(center=draw_rect.center))
                idx += 1

        # Hint
        hint = f"Page {self.page+1}/{max(1,(len(self.items)+self.per_page-1)//self.per_page)}  (A/D to swap, Esc exit)"
        hint_surf, _ = self.info_font.render(hint, (200, 200, 200))
        surf.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 40)))