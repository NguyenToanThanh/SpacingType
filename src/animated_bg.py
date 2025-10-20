# src/animated_bg.py
import glob
import pygame

class AnimatedBackground:
    def __init__(self, frames_glob: str, size: tuple[int, int], fps: int = 24):
        paths = sorted(glob.glob(frames_glob))
        if not paths:
            raise FileNotFoundError(f"No frames found for: {frames_glob}")
        w, h = size
        self.frames = [
            pygame.transform.smoothscale(pygame.image.load(p).convert(), (w, h))
            for p in paths
        ]
        self.fps = max(1, int(fps))
        self.ms_per_frame = 1000 // self.fps
        self._acc = 0
        self._idx = 0

    def update(self, dt_ms: int):
        self._acc += dt_ms
        while self._acc >= self.ms_per_frame:
            self._idx = (self._idx + 1) % len(self.frames)
            self._acc -= self.ms_per_frame

    def draw(self, surf: pygame.Surface):
        surf.blit(self.frames[self._idx], (0, 0))
