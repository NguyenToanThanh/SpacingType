import pygame

class Explosion:
    """
    Hiệu ứng nổ đơn giản: hiển thị explosion_img trong 1 khoảng thời gian ngắn.
    """
    def __init__(self, x: int, y: int, lifetime_frames: int = 20):
        self.x = x
        self.y = y
        self.timer = lifetime_frames

    def draw(self, surface: pygame.Surface, explosion_img: pygame.Surface):
        surface.blit(explosion_img, (self.x - 20, self.y - 20))
        self.timer -= 1

    @property
    def done(self) -> bool:
        return self.timer <= 0
