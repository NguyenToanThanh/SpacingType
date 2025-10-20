# ============================================================
# IMPORT LIBRARIES & CONSTANTS
# ============================================================
import math
import random
import pygame

from .settings import WIDTH, HEIGHT, FPS, WHITE, WORDS, SPAWN_DELAYMS, SHIP_Y
from .utils import load_image, load_sound
from .enemy import Enemy
from .bullet import Bullet
from .explosion import Explosion
from .ship import draw_ship, draw_rotated_ship

YELLOW = (255, 255, 0)


# ============================================================
# CLASS GAME
# ============================================================
class Game:
    """Quản lý toàn bộ game Space Typing."""

    def __init__(self, music_file=None, video_background=None):
        # Pygame initialization
        pygame.init()
        pygame.key.set_repeat(1, 1)
        pygame.key.start_text_input()
        pygame.mixer.init()

        # Window & Display
        self.win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Space Typing Game")
        self.clock = pygame.time.Clock()
        self.delta_time = 0
        
        # Video background (nếu có)
        self.video_background = video_background

        # Font & HUD
        self.font = pygame.font.SysFont("Arial", 32)
        self.score = 0
        self.lives = 3
        self.typed_word = ""
        
        # Cache cho HUD text để giảm render calls
        self._hud_cache = {}
        self._last_score = -1
        self._last_lives = -1
        self._last_kills = -1

        # Challenge Mode
        self.kills = 0
        self.target_kills = None
        self.completed = False
        self.request_quit = False

        # ============================================================
        # ASSETS - BACKGROUND
        # ============================================================
        try:
            self.background = load_image("background3.jpg", (WIDTH, HEIGHT))
        except Exception as e:
            print(f"[WARN] Không thể tải background: {e}")
            self.background = None

        # ============================================================
        # ASSETS - IMAGES
        # ============================================================
        try:
            self.explosion_img = load_image("explosion.png", (40, 40))
        except:
            self.explosion_img = None

        # ============================================================
        # ASSETS - SOUND EFFECTS
        # ============================================================
        try:
            self.shoot_sound = load_sound("ban.wav")
            if self.shoot_sound:
                self.shoot_sound.set_volume(0.3)
        except Exception as e:
            print(f"[WARN] Không thể nạp âm thanh ban.wav: {e}")
            self.shoot_sound = None

        try:
            self.explosion_sound = load_sound("no.wav")
            if self.explosion_sound:
                self.explosion_sound.set_volume(0.5)
        except Exception as e:
            print(f"[WARN] Không thể nạp âm thanh no.wav: {e}")
            self.explosion_sound = None

        # ============================================================
        # BACKGROUND MUSIC
        # ============================================================
        # Sử dụng music_file được truyền vào, hoặc mặc định music3.mp3
        music_to_load = music_file if music_file else "music3.mp3"
        
        try:
            self.bg_music = load_sound(music_to_load)
            if self.bg_music:
                self.music_channel = pygame.mixer.Channel(5)
                self.music_channel.set_volume(0.9)
                self.music_channel.play(self.bg_music, loops=-1)
                print(f"[INFO] 🎵 Nhạc nền đang phát: {music_to_load}")
            else:
                self.music_channel = None
        except Exception as e:
            print(f"[WARN] Không thể phát nhạc nền {music_to_load}: {e}")
            self.music_channel = None

        # ============================================================
        # GAME ENTITIES
        # ============================================================
        self.enemies = []
        self.bullets = []
        self.explosions = []
        self.last_spawn_ms = pygame.time.get_ticks()
        self.locked = None
        self.angle = 0.0

    # ============================================================
    # UTILITY METHODS
    # ============================================================
    def _enemy_center_x(self, enemy):
        """Tính toạ độ X trung tâm của enemy."""
        shown = "_" * enemy.progress + enemy.origin_word[enemy.progress:]
        text_width = self.font.size(shown)[0]
        return int(enemy.x + text_width / 2)

    def _update_ship_aim(self):
        """Cập nhật góc ngắm của tàu."""
        if self.locked and self.locked in self.enemies:
            tx = self._enemy_center_x(self.locked)
            ty = self.locked.y
            self.angle = math.atan2(ty - SHIP_Y, tx - (WIDTH // 2))
        else:
            self.angle = 0.0

    # ============================================================
    # GAME LOGIC
    # ============================================================
    def spawn_enemy(self):
        """Spawn enemy mới theo thời gian."""
        now = pygame.time.get_ticks()
        if now - self.last_spawn_ms > SPAWN_DELAYMS:
            self.enemies.append(Enemy(random.choice(WORDS)))
            self.last_spawn_ms = now

    def destroy_enemy(self, enemy):
        """Phá huỷ enemy và cập nhật điểm."""
        self.score += len(enemy.origin_word) * 10
        self.kills += 1
        self.explosions.append(Explosion(enemy.x, enemy.y))
        
        if self.explosion_sound:
            self.explosion_sound.play()
        
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        
        if enemy is self.locked:
            self.locked = None
            self.typed_word = ""
        
        if self.target_kills and self.kills >= self.target_kills:
            self.completed = True

    def handle_typed_char(self, ch):
        """Xử lý ký tự người chơi nhập."""
        if not self.locked:
            # Tìm enemy khớp ký tự đầu tiên
            candidates = [e for e in self.enemies if e.required_char() == ch]
            if candidates:
                # Chọn enemy gần nhất (y lớn nhất)
                candidates.sort(key=lambda e: e.y, reverse=True)
                self.locked = candidates[0]
                self.typed_word = ch
                self.bullets.append(Bullet(self.locked, ch, self.font, self.locked.progress))
                
                if self.shoot_sound:
                    self.shoot_sound.play()
                
                self.locked.hit_char(ch)
                
                if self.locked.is_complete():
                    self.destroy_enemy(self.locked)
        else:
            # Kiểm tra ký tự tiếp theo
            if self.locked.required_char() == ch:
                self.typed_word += ch
                self.bullets.append(Bullet(self.locked, ch, self.font, self.locked.progress))
                
                if self.shoot_sound:
                    self.shoot_sound.play()
                
                self.locked.hit_char(ch)
                
                if self.locked.is_complete():
                    self.destroy_enemy(self.locked)
            else:
                # Sai ký tự -> reset lock
                self.locked = None
                self.typed_word = ""

    def handle_keydown(self, event):
        """Xử lý phím đặc biệt."""
        if event.key == pygame.K_ESCAPE:
            # Nếu đang trong challenge mode, ESC sẽ thoát về menu
            if self.target_kills:
                self.request_quit = True
            else:
                # Classic mode: chỉ unlock target
                self.locked = None
                self.typed_word = ""
        elif event.key == pygame.K_BACKSPACE and self.typed_word:
            self.typed_word = self.typed_word[:-1]

    # ============================================================
    # UPDATE & RENDER
    # ============================================================
    def update(self):
        """Cập nhật trạng thái game."""
        # Update video background nếu có
        if self.video_background:
            self.video_background.update(self.delta_time * 1000)  # Convert to ms
        
        # Update bullets
        for b in self.bullets[:]:
            b.move()
            if b.is_hit() or b.is_out_of_bounds():
                self.bullets.remove(b)

        # Update enemies
        for enemy in self.enemies[:]:
            enemy.move()
            if enemy.y > HEIGHT:
                self.enemies.remove(enemy)
                self.lives -= 1
                if enemy is self.locked:
                    self.locked = None
                    self.typed_word = ""

        # Update explosions
        for explosion in self.explosions[:]:
            explosion.timer -= 1
            if explosion.timer <= 0:
                self.explosions.remove(explosion)

        # Update ship aim
        self._update_ship_aim()

    def draw(self):
        """Vẽ toàn bộ game."""
        # Background - video hoặc image
        if self.video_background:
            self.video_background.draw(self.win)
        elif self.background:
            self.win.blit(self.background, (0, 0))
        else:
            self.win.fill((0, 0, 0))

        # Enemies
        for enemy in self.enemies:
            color = YELLOW if enemy is self.locked else WHITE
            enemy.draw(self.win, self.font, color)

        # Bullets
        for bullet in self.bullets:
            bullet.draw(self.win)

        # Explosions
        if self.explosion_img:
            for explosion in self.explosions:
                explosion.draw(self.win, self.explosion_img)

        # Ship
        if self.locked and self.locked in self.enemies:
            draw_rotated_ship(self.win, self.angle)
        else:
            draw_ship(self.win)

        # HUD - với caching để tối ưu
        # Chỉ render lại khi giá trị thay đổi
        if self._last_score != self.score:
            self._hud_cache['score'] = self.font.render(f"Score: {self.score}", True, WHITE)
            self._last_score = self.score
        
        if self._last_lives != self.lives:
            self._hud_cache['lives'] = self.font.render(f"Lives: {self.lives}", True, WHITE)
            self._last_lives = self.lives
        
        if self.target_kills and self._last_kills != self.kills:
            self._hud_cache['kills'] = self.font.render(f"Kills: {self.kills}/{self.target_kills}", True, WHITE)
            self._last_kills = self.kills
        
        # Vẽ cached surfaces
        self.win.blit(self._hud_cache.get('score', self.font.render("Score: 0", True, WHITE)), (10, 10))
        self.win.blit(self._hud_cache.get('lives', self.font.render("Lives: 3", True, WHITE)), (10, 50))
        
        locked_text = f"Locked: {self.locked.origin_word if self.locked else '-'}"
        locked_surface = self.font.render(locked_text, True, WHITE)
        self.win.blit(locked_surface, (10, 90))
        
        typing_text = f"Typing: {self.typed_word}"
        typing_surface = self.font.render(typing_text, True, WHITE)
        self.win.blit(typing_surface, (10, HEIGHT - 50))
        
        if self.target_kills:
            self.win.blit(self._hud_cache.get('kills', self.font.render(f"Kills: 0/{self.target_kills}", True, WHITE)), (10, 130))
            # Hiển thị hướng dẫn ESC cho challenge mode
            esc_hint = self.font.render("Press ESC to quit", True, (150, 150, 150))
            self.win.blit(esc_hint, (WIDTH - 220, HEIGHT - 40))

        pygame.display.flip()

    # ============================================================
    # MAIN GAME LOOP
    # ============================================================
    def run(self):
        """Vòng lặp chính của game."""
        running = True
        
        while running:
            # Calculate delta time TRƯỚC khi update
            dt_ms = self.clock.tick(FPS)  # milliseconds
            self.delta_time = dt_ms / 1000.0  # seconds
            
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)
                elif event.type == pygame.TEXTINPUT:
                    self.handle_typed_char(event.text)

            # Spawn & Update
            self.spawn_enemy()
            self.update()

            # Check end conditions
            if self.lives <= 0 or (self.target_kills and self.completed) or self.request_quit:
                running = False

            # Render
            self.draw()

        # ============================================================
        # GAME OVER
        # ============================================================
        pygame.key.stop_text_input()
        
        # Dừng nhạc nền
        if self.music_channel:
            self.music_channel.stop()

        # Hiển thị màn hình Game Over (chỉ cho classic mode)
        if not self.target_kills:
            if self.background:
                self.win.blit(self.background, (0, 0))
            else:
                self.win.fill((0, 0, 0))
            
            end_text = self.font.render(f"Game Over! Score: {self.score}", True, WHITE)
            text_rect = end_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.win.blit(end_text, text_rect)
            pygame.display.flip()
            pygame.time.wait(2000)