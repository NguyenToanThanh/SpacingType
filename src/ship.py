# ship.py
import pygame, math
from .utils import load_image
from .settings import WIDTH, SHIP_Y

_ship_img = None

def _init_ship():
    global _ship_img
    if _ship_img is None:
        img = load_image("spaceship.png", (80, 80))
        if img.get_alpha() is None:
            bg_color = img.get_at((0, 0))[:3] 
            img.set_colorkey(bg_color)
        _ship_img = img


def draw_ship(surface: pygame.Surface):
    _init_ship()
    rect = _ship_img.get_rect(center=(WIDTH // 2, SHIP_Y))
    surface.blit(_ship_img, rect)

def draw_rotated_ship(surface: pygame.Surface, angle_rad: float):

    _init_ship()
    deg = -math.degrees(angle_rad) - 90  # bù góc cho đúng mũi tàu
    rotated = pygame.transform.rotate(_ship_img, deg)
    rect = rotated.get_rect(center=(WIDTH // 2, SHIP_Y))
    surface.blit(rotated, rect)
