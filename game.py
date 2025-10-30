# ============================================================
# SPACE TYPING GAME - MAIN GAME LOGIC
# ============================================================
# File: game.py
# Mô tả: Quản lý toàn bộ logic game, render, input handling
# Chức năng chính:
#   - Spawn và quản lý enemies
#   - Xử lý input từ bàn phím (gõ từ)
#   - Hệ thống lock target
#   - Collision detection (enemy vs ship)
#   - Lives system (3 mạng)
#   - Screen shake và explosion effects
#   - HUD rendering với hearts
# ============================================================

import math
import random
import pygame

from .settings import WIDTH, HEIGHT, FPS, WHITE, WORDS, SPAWN_DELAYMS, SHIP_Y
from .utils import load_image, load_sound
from .enemy import Enemy
from .bullet import Bullet
from .explosion import Explosion, ScreenShake
from .ship import draw_ship, draw_rotated_ship

# Constants
YELLOW = (255, 255, 0)


class Game:
    """
    Class chính quản lý toàn bộ game Space Typing.
    
    Chức năng:
        - Khởi tạo pygame, window, assets (images, sounds, music)
        - Spawn enemies theo thời gian
        - Xử lý input (typing, lock target, backspace, ESC)
        - Update game logic (enemies movement, collision, lives)
        - Render (background, enemies, bullets, explosions, ship, HUD)
        - Game loop chính
    """

    def __init__(self, music_file=None, video_background=None, challenge_speed=None):
        """
        Khởi tạo game.
        
        Args:
            music_file (str, optional): File nhạc nền. Mặc định "music3.mp3"
            video_background (VideoBackground, optional): Video làm background động
            challenge_speed (float, optional): Tốc độ rơi cho Challenge mode
        """
        # Pygame initialization
        pygame.init()
        pygame.key.set_repeat(1, 1)
        pygame.key.start_text_input()
        pygame.mixer.init()

        # Window & Display
        self.win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN)
        pygame.display.set_caption("Space Typing Game")
        self.clock = pygame.time.Clock()
        self.delta_time = 0
        
        # Video background (nếu có)
        self.video_background = video_background
        
        # Challenge mode speed
        self.challenge_speed = challenge_speed
        self.is_challenge_mode = challenge_speed is not None

        # Font & HUD
        self.font = pygame.font.SysFont("Arial", 32)
        self.score = 0
        self.lives = 3  # Phi thuyền có 3 mạng
        self.max_lives = 3  # Số mạng tối đa
        self.typed_word = ""
        
        # Hệ thống va chạm với phi thuyền
        self.ship_collision_count = 0  # Số lần enemy chạm phi thuyền
        self.ship_invulnerable_timer = 0  # Thời gian bất tử sau khi bị hit
        self.ship_flash_timer = 0  # Timer cho hiệu ứng nhấp nháy
        
        # Cache cho HUD text để giảm render calls
        self._hud_cache = {}
        self._last_score = -1
        self._last_lives = -1
        self._last_kills = -1

        # Challenge Mode
        self.kills = 0
        self.target_kills = None
        self.completed = False

        # ============================================================
        # ASSETS - BACKGROUND
        # ============================================================
        try:
            self.background = load_image("backgrounds/background3.jpg", (WIDTH, HEIGHT))
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
        self.screen_shake = None  # Screen shake effect
        self.last_spawn_ms = pygame.time.get_ticks()
        self.locked = None
        self.angle = 0.0

    # ============================================================
    # PRIVATE UTILITY METHODS
    # ============================================================
    
    def _enemy_center_x(self, enemy):
        """
        Tính toạ độ X trung tâm của enemy để ngắm bắn.
        
        Args:
            enemy (Enemy): Enemy cần tính toạ độ
            
        Returns:
            int: Toạ độ X trung tâm của từ enemy
        """
        shown = "_" * enemy.progress + enemy.origin_word[enemy.progress:]
        text_width = self.font.size(shown)[0]
        return int(enemy.x + text_width / 2)

    def _update_ship_aim(self):
        """
        Cập nhật góc xoay của phi thuyền để ngắm về enemy đang lock.
        Nếu không có lock thì angle = 0 (hướng thẳng lên).
        """
        if self.locked and self.locked in self.enemies:
            tx = self._enemy_center_x(self.locked)
            ty = self.locked.y
            self.angle = math.atan2(ty - SHIP_Y, tx - (WIDTH // 2))
        else:
            self.angle = 0.0
    
    def _draw_hearts(self, x, y):
        """
        Vẽ các icon trái tim thể hiện số mạng còn lại.
        
        Args:
            x (int): Toạ độ X bắt đầu vẽ
            y (int): Toạ độ Y vẽ
            
        Hiển thị:
            - Đỏ/Hồng: Tim còn mạng
            - Xám: Tim đã mất
            - Màu thay đổi theo số lives (đỏ sáng khi 1 mạng)
        """
        heart_size = 12
        heart_spacing = 18
        
        for i in range(self.max_lives):
            heart_x = x + i * heart_spacing
            
            # Chọn màu theo lives còn lại
            if i < self.lives:
                if self.lives == 1:
                    color = (255, 50, 50)  # Đỏ sáng - nguy hiểm!
                elif self.lives == 2:
                    color = (255, 150, 50)  # Cam - cảnh báo
                else:
                    color = (255, 50, 100)  # Hồng - khỏe mạnh
            else:
                color = (80, 80, 80)  # Xám - đã mất
            
            self._draw_heart_shape(self.win, heart_x, y, heart_size, color, filled=(i < self.lives))
    
    def _draw_heart_shape(self, surface, x, y, size, color, filled=True):
        """
        Vẽ một trái tim bằng parametric equations.
        
        Args:
            surface (pygame.Surface): Surface để vẽ
            x, y (int): Toạ độ trung tâm trái tim
            size (int): Kích thước trái tim
            color (tuple): Màu RGB
            filled (bool): Vẽ solid hay chỉ outline
        """
        points = []
        scale = size / 20.0
        
        # Parametric heart equations
        for t in range(0, 360, 10):
            angle = math.radians(t)
            heart_x = 16 * math.sin(angle) ** 3
            heart_y = -(13 * math.cos(angle) - 5 * math.cos(2*angle) - 
                       2 * math.cos(3*angle) - math.cos(4*angle))
            
            points.append((x + heart_x * scale, y + heart_y * scale))
        
        if filled:
            pygame.draw.polygon(surface, color, points)
        else:
            pygame.draw.polygon(surface, color, points, 2)

    # ============================================================
    # CORE GAME LOGIC METHODS
    # ============================================================
    
    def check_ship_collision(self, enemy):
        """
        Kiểm tra va chạm giữa enemy và phi thuyền (circle collision).
        
        Args:
            enemy (Enemy): Enemy cần kiểm tra
            
        Returns:
            bool: True nếu va chạm, False nếu không
        """
        ship_x = WIDTH // 2
        ship_y = SHIP_Y
        ship_radius = 40
        
        dx = enemy.x - ship_x
        dy = enemy.y - ship_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        return distance < ship_radius
    
    def hit_ship(self, enemy):
        """
        Xử lý khi enemy chạm vào phi thuyền.
        
        Args:
            enemy (Enemy): Enemy gây va chạm
            
        Side effects:
            - Giảm 1 lives
            - Tạo explosion tại phi thuyền
            - Screen shake mạnh
            - Xóa enemy
            - Unlock nếu enemy đang bị lock
            - Bật invulnerability (60 frames = 1 giây)
        """
        if self.ship_invulnerable_timer > 0:
            return
        
        self.lives -= 1
        self.explosions.append(Explosion(WIDTH // 2, SHIP_Y, lifetime_frames=40))
        self.screen_shake = ScreenShake(intensity=20, duration=20)
        
        if self.explosion_sound:
            self.explosion_sound.play()
        
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        
        if enemy is self.locked:
            self.locked = None
            self.typed_word = ""
        
        self.ship_invulnerable_timer = 60
        self.ship_flash_timer = 60
        
        print(f"💥 PHI THUYỀN BỊ HIT! Lives còn lại: {self.lives}/3")
    
    def spawn_enemy(self):
        """
        Spawn enemy mới theo thời gian (mỗi SPAWN_DELAYMS milliseconds).
        Enemy tự động tránh spawn chồng lên nhau qua existing_enemies.
        """
        now = pygame.time.get_ticks()
        if now - self.last_spawn_ms > SPAWN_DELAYMS:
            # Truyền challenge_speed nếu đang ở Challenge mode
            new_enemy = Enemy(
                random.choice(WORDS), 
                existing_enemies=self.enemies,
                use_challenge_speed=self.is_challenge_mode,
                challenge_speed=self.challenge_speed
            )
            self.enemies.append(new_enemy)
            self.last_spawn_ms = now

    def destroy_enemy(self, enemy):
        """
        Phá hủy enemy khi gõ đúng hết từ.
        
        Args:
            enemy (Enemy): Enemy bị phá hủy
            
        Side effects:
            - Tăng score (+10 cho mỗi ký tự)
            - Tăng kills (dùng cho Challenge mode)
            - Tạo explosion effect
            - Screen shake (càng dài từ càng mạnh)
            - Xóa enemy khỏi danh sách
            - Unlock nếu đang lock
            - Check win condition (Challenge mode)
        """
        self.score += len(enemy.origin_word) * 10
        self.kills += 1
        
        self.explosions.append(Explosion(enemy.x, enemy.y, lifetime_frames=30))
        
        shake_intensity = min(15, 5 + len(enemy.origin_word))
        self.screen_shake = ScreenShake(intensity=shake_intensity, duration=12)
        
        if self.explosion_sound:
            self.explosion_sound.play()
        
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        
        if enemy is self.locked:
            self.locked = None
            self.typed_word = ""
        
        if self.target_kills and self.kills >= self.target_kills:
            self.completed = True

    # ============================================================
    # INPUT HANDLING METHODS
    # ============================================================
    
    def handle_typed_char(self, ch):
        """
        Xử lý ký tự người chơi gõ (a-z, A-Z).
        
        Args:
            ch (str): Ký tự người chơi vừa gõ
            
        Logic:
            - Chưa lock: Tìm enemy bắt đầu bằng ký tự 'ch', chọn enemy gần nhất (nguy hiểm nhất)
            - Đã lock: 
                + Gõ đúng → Bắn bullet, tăng progress, kiểm tra complete
                + Gõ sai → Bỏ qua, GIỮ NGUYÊN lock (không auto-switch)
        
        Note:
            Sau khi sửa lock target system, gõ sai sẽ KHÔNG tự động 
            chuyển sang enemy khác. Người chơi phải ESC hoặc Backspace.
        """
        if not self.locked:
            # Chưa lock → Tìm enemy khớp ký tự đầu
            candidates = [e for e in self.enemies if e.required_char() == ch]
            if candidates:
                # Chọn enemy gần nhất (y lớn nhất)
                candidates.sort(key=lambda e: e.y, reverse=True)
                self.locked = candidates[0]
                self.typed_word = ch
                self.bullets.append(Bullet(self.locked, self.font, self.locked.progress))
                
                if self.shoot_sound:
                    self.shoot_sound.play()
                
                self.locked.hit_char(ch)
                
                if self.locked.is_complete():
                    self.destroy_enemy(self.locked)
        else:
            # Đã lock → CHỈ bắn vào enemy đó
            if self.locked not in self.enemies:
                self.locked = None
                self.typed_word = ""
                return
            
            if self.locked.required_char() == ch:
                # ✅ Gõ đúng
                self.typed_word += ch
                self.bullets.append(Bullet(self.locked, self.font, self.locked.progress))
                
                if self.shoot_sound:
                    self.shoot_sound.play()
                
                self.locked.hit_char(ch)
                
                if self.locked.is_complete():
                    self.destroy_enemy(self.locked)
            else:
                # ❌ Gõ sai → Bỏ qua, giữ nguyên lock
                print(f"⚠️ Gõ sai! Cần gõ '{self.locked.required_char()}' cho '{self.locked.origin_word}'")

    def handle_keydown(self, event):
        """
        Xử lý các phím đặc biệt (ESC, Backspace).
        
        Args:
            event (pygame.Event): Event KEYDOWN
            
        Keys:
            - ESC: Hủy lock target
            - Backspace: Xóa ký tự cuối, giảm progress enemy, tăng HP lại
        """
        if event.key == pygame.K_ESCAPE:
            self.locked = None
            self.typed_word = ""
            print("🚫 Đã hủy lock target")
            
        elif event.key == pygame.K_BACKSPACE:
            if self.typed_word and self.locked:
                self.typed_word = self.typed_word[:-1]
                
                if self.locked.progress > 0:
                    self.locked.progress -= 1
                    self.locked.current_hp += 1
                
                if not self.typed_word:
                    self.locked = None
                    print("🔓 Đã unlock target (xóa hết từ)")
            elif self.typed_word and not self.locked:
                self.typed_word = self.typed_word[:-1]

    # ============================================================
    # UPDATE & RENDER METHODS
    # ============================================================
    
    def update(self):
        """
        Update tất cả game entities và logic (gọi mỗi frame).
        
        Thứ tự update:
            1. Video background (nếu có)
            2. Screen shake effect
            3. Ship invulnerability timer
            4. Bullets (move + remove nếu hit/out of bounds)
            5. Enemies (move + collision check + remove nếu qua màn hình)
            6. Explosions (tự động remove khi done)
            7. Ship aim angle (theo locked enemy)
        """
        # Video background
        if self.video_background:
            self.video_background.update(self.delta_time * 1000)
        
        # Screen shake
        if self.screen_shake:
            self.screen_shake.update()
            if not self.screen_shake.active:
                self.screen_shake = None
        
        # Invulnerability timers
        if self.ship_invulnerable_timer > 0:
            self.ship_invulnerable_timer -= 1
        if self.ship_flash_timer > 0:
            self.ship_flash_timer -= 1
        
        # Bullets
        for b in self.bullets[:]:
            b.move()
            if b.is_hit() or b.is_out_of_bounds():
                self.bullets.remove(b)

        # Enemies
        for enemy in self.enemies[:]:
            enemy.move(other_enemies=self.enemies)
            
            # Ship collision
            if self.check_ship_collision(enemy):
                self.hit_ship(enemy)
                continue
            
            # Remove nếu rơi qua màn hình
            if enemy.y > HEIGHT + 50:
                self.enemies.remove(enemy)
                if enemy is self.locked:
                    self.locked = None
                    self.typed_word = ""

        # Explosions
        for explosion in self.explosions[:]:
            if explosion.done:
                self.explosions.remove(explosion)

        # Ship aim
        self._update_ship_aim()

    def draw(self):
        """
        Render toàn bộ game lên màn hình (gọi mỗi frame).
        
        Thứ tự vẽ (từ xa đến gần):
            1. Background (video/image) với screen shake
            2. Enemies với shake offset
            3. Bullets với shake offset
            4. Explosions với shake offset (vẽ TRƯỚC ship)
            5. Ship (có flash effect khi bị hit, xoay khi lock)
            6. HUD (không shake): Score, Lives hearts, Locked, Typing, Kills, Warning
        
        Note:
            - HUD dùng caching để tối ưu (chỉ render khi giá trị thay đổi)
            - Screen shake apply cho tất cả entities TRỪ HUD
        """
        # Screen shake offset
        shake_offset = (0, 0)
        if self.screen_shake:
            shake_offset = self.screen_shake.get_offset()
        
        # Background
        if self.video_background:
            self.video_background.draw(self.win)
        elif self.background:
            self.win.blit(self.background, shake_offset)
        else:
            self.win.fill((0, 0, 0))

        # Enemies (với shake)
        for enemy in self.enemies:
            color = YELLOW if enemy is self.locked else WHITE
            # Tạo temporary surface để apply shake
            temp_x = enemy.x + shake_offset[0]
            temp_y = enemy.y + shake_offset[1]
            # Lưu vị trí gốc
            orig_x, orig_y = enemy.x, enemy.y
            enemy.x, enemy.y = temp_x, temp_y
            enemy.draw(self.win, self.font)
            # Restore vị trí gốc
            enemy.x, enemy.y = orig_x, orig_y

        # Bullets (với shake)
        for bullet in self.bullets:
            # Lưu vị trí gốc
            orig_x, orig_y = bullet.x, bullet.y
            bullet.x += shake_offset[0]
            bullet.y += shake_offset[1]
            bullet.draw(self.win)
            # Restore
            bullet.x, bullet.y = orig_x, orig_y

        # Explosions (với shake) - vẽ TRƯỚC ship để không che ship
        for explosion in self.explosions:
            # Lưu vị trí gốc
            orig_x, orig_y = explosion.x, explosion.y
            explosion.x += shake_offset[0]
            explosion.y += shake_offset[1]
            explosion.draw(self.win, self.explosion_img)
            # Restore
            explosion.x, explosion.y = orig_x, orig_y

        # Ship (với shake và flash effect khi bị hit)
        # Hiệu ứng nhấp nháy khi bị hit
        draw_ship_flag = True
        if self.ship_flash_timer > 0:
            # Nhấp nháy mỗi 5 frames
            draw_ship_flag = (self.ship_flash_timer // 5) % 2 == 0
        
        if draw_ship_flag:
            if self.locked and self.locked in self.enemies:
                draw_rotated_ship(self.win, self.angle, shake_offset)
            else:
                draw_ship(self.win, shake_offset)

        # HUD - với caching để tối ưu (KHÔNG shake HUD)
        # Chỉ render lại khi giá trị thay đổi
        if self._last_score != self.score:
            self._hud_cache['score'] = self.font.render(f"Score: {self.score}", True, WHITE)
            self._last_score = self.score
        
        if self._last_lives != self.lives:
            # Lives với text đơn giản (sẽ vẽ hearts bằng hình sau)
            self._hud_cache['lives_text'] = self.font.render(f"Lives:", True, WHITE)
            self._last_lives = self.lives
        
        if self.target_kills and self._last_kills != self.kills:
            self._hud_cache['kills'] = self.font.render(f"Kills: {self.kills}/{self.target_kills}", True, WHITE)
            self._last_kills = self.kills
        
        # Vẽ cached surfaces
        self.win.blit(self._hud_cache.get('score', self.font.render("Score: 0", True, WHITE)), (10, 10))
        
        # Vẽ Lives với hearts tự vẽ
        self.win.blit(self._hud_cache.get('lives_text', self.font.render("Lives:", True, WHITE)), (10, 50))
        self._draw_hearts(80, 58)  # Vẽ hearts bên cạnh text "Lives:"
        
        locked_text = f"Locked: {self.locked.origin_word if self.locked else '-'}"
        locked_surface = self.font.render(locked_text, True, WHITE)
        self.win.blit(locked_surface, (10, 90))
        
        typing_text = f"Typing: {self.typed_word}"
        typing_surface = self.font.render(typing_text, True, WHITE)
        self.win.blit(typing_surface, (10, HEIGHT - 50))
        
        if self.target_kills:
            self.win.blit(self._hud_cache.get('kills', self.font.render(f"Kills: 0/{self.target_kills}", True, WHITE)), (10, 130))
        
        # Warning khi có enemy gần phi thuyền
        dangerous_enemies = [e for e in self.enemies if e.y > SHIP_Y - 100]
        if dangerous_enemies:
            warning_text = " DANGER!!!!"
            warning_color = (255, 50, 50) if (pygame.time.get_ticks() // 200) % 2 == 0 else (255, 150, 50)
            warning_surface = self.font.render(warning_text, True, warning_color)
            warning_rect = warning_surface.get_rect(center=(WIDTH // 2, HEIGHT - 100))
            self.win.blit(warning_surface, warning_rect)

        pygame.display.flip()

    # ============================================================
    # MAIN GAME LOOP
    # ============================================================
    
    def run(self):
        """
        Vòng lặp chính của game.
        
        Flow:
            1. Calculate delta time (FPS control)
            2. Process events (QUIT, KEYDOWN, TEXTINPUT)
            3. Spawn enemies
            4. Update game logic
            5. Check end conditions (lives <= 0 hoặc target_kills đạt được)
            6. Render
            7. Repeat
        
        End conditions:
            - Classic mode: lives <= 0
            - Challenge mode: lives <= 0 hoặc kills >= target_kills
        
        Post-loop:
            - Stop music
            - Show Game Over screen (chỉ Classic mode)
            - Challenge mode: không show Game Over (do challenge.py xử lý)
        """
        running = True
        
        while running:
            # Delta time
            dt_ms = self.clock.tick(FPS)
            self.delta_time = dt_ms / 1000.0
            
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)
                elif event.type == pygame.TEXTINPUT:
                    self.handle_typed_char(event.text)

            # Game logic
            self.spawn_enemy()
            self.update()

            # End conditions
            if self.lives <= 0 or (self.target_kills and self.completed):
                running = False

            # Render
            self.draw()

        # ============================================================
        # POST-GAME CLEANUP
        # ============================================================
        pygame.key.stop_text_input()
        
        if self.music_channel:
            self.music_channel.stop()

        # Game Over screen (chỉ Classic mode)
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