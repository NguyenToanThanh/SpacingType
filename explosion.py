# ============================================================
# explosion.py — Hiệu ứng nổ và rung màn hình trong game
# ============================================================

import pygame
import random
import math


# ------------------------------------------------------------
# CLASS: Explosion
# ------------------------------------------------------------
class Explosion:
    """
    Hiệu ứng nổ nâng cao với các thành phần:
    - Phóng to / thu nhỏ (scale animation)
    - Xoay hình ảnh (rotation)
    - Tạo hạt (particle effect)
    - Hiệu ứng lóe sáng (flash effect)
    """

    def __init__(self, x: int, y: int, lifetime_frames: int = 30):
        """Khởi tạo một vụ nổ tại vị trí (x, y)."""

        # Tọa độ trung tâm vụ nổ
        self.x = x
        self.y = y

        # Thời gian tồn tại (tính theo frame)
        self.timer = lifetime_frames
        self.max_lifetime = lifetime_frames
        
        # ---------------------------
        # Thuộc tính animation chính
        # ---------------------------
        self.scale = 0.5          # Bắt đầu nhỏ
        self.max_scale = 2.0      # Phóng to tối đa gấp đôi
        self.rotation = 0         # Góc xoay hiện tại
        self.rotation_speed = random.uniform(-15, 15)  # Tốc độ xoay ngẫu nhiên (± độ/frame)
        
        # ---------------------------
        # Hiệu ứng lóe sáng ban đầu
        # ---------------------------
        self.flash_duration = 5   # Số frame lóe sáng (flash effect)
        
        # ---------------------------
        # Khởi tạo particle (tia lửa, khói)
        # ---------------------------
        self.particles = []
        num_particles = random.randint(30, 55)  # Số lượng hạt mỗi lần nổ
        self.max_particle_life = 45  # Lưu tuổi thọ MAX để tính alpha đúng
        
        for _ in range(num_particles):
            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-3, 3),   # Vận tốc theo trục X
                'vy': random.uniform(-3, 3),   # Vận tốc theo trục Y
                'size': random.randint(1, 4),  # Kích thước hạt
                'color': random.choice([
                   (180, 0, 255),   # Tím đậm
                   (200, 100, 255), # Tím nhạt
                   (160, 80, 200),  # Tím khói
                   (120, 60, 160),  # Tím tối
                   (220, 180, 255), # Hồng tím sáng
                ]),
                'life': random.randint(25, 45) # Tuổi thọ của hạt (frame)
            }
            self.particles.append(particle)
    

    # ------------------------------------------------------------
    # CẬP NHẬT HIỆU ỨNG (theo từng frame)
    # ------------------------------------------------------------
    def update(self):
        """Cập nhật trạng thái animation của vụ nổ."""

        # Giảm timer (đếm ngược đến khi kết thúc)
        self.timer -= 1
        
        # Tính tiến trình animation (0 → 1)
        progress = 1 - (self.timer / self.max_lifetime)

        # Giai đoạn 1: phóng to nhanh (0%–30%)
        if progress < 0.3:
            self.scale = 0.5 + (progress / 0.3) * (self.max_scale - 0.5)

        # Giai đoạn 2: giữ kích thước (30%–70%)
        elif progress < 0.7:
            self.scale = self.max_scale

        # Giai đoạn 3: thu nhỏ dần và mờ đi (70%–100%)
        else:
            fade_progress = (progress - 0.7) / 0.3
            self.scale = self.max_scale * (1 - fade_progress * 0.5)
        
        # Cập nhật góc xoay
        self.rotation += self.rotation_speed
        
        # ---------------------------
        # Cập nhật từng particle
        # ---------------------------
        for particle in self.particles[:]:  # Duyệt bản sao vì có thể xóa phần tử
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']

            # Trọng lực kéo hạt rơi xuống
            particle['vy'] += 0.15

            # Ma sát làm hạt chậm lại
            particle['vx'] *= 0.98

            # Giảm tuổi thọ
            particle['life'] -= 1
            
            # Nếu hết life, xóa hạt
            if particle['life'] <= 0:
                self.particles.remove(particle)


    # ------------------------------------------------------------
    # VẼ HIỆU ỨNG NỔ LÊN MÀN HÌNH
    # ------------------------------------------------------------
    def draw(self, surface: pygame.Surface, explosion_img: pygame.Surface = None):
        """Vẽ vụ nổ cùng hiệu ứng (flash, particle, ảnh xoay)."""

        # Luôn cập nhật mỗi khi vẽ
        self.update()
        
        # (1) Hiệu ứng flash lóe sáng ở vài frame đầu
        if self.timer > self.max_lifetime - self.flash_duration:
            # Độ trong suốt (alpha) giảm dần theo thời gian
            flash_alpha = int(200 * (1 - (self.max_lifetime - self.timer) / self.flash_duration))
            flash_surf = pygame.Surface((80, 80))
            flash_surf.set_alpha(flash_alpha)
            flash_surf.fill((255, 255, 200))  # Ánh sáng vàng nhạt
            surface.blit(flash_surf, (self.x - 40, self.y - 40))
        
        # (2) Vẽ từng particle (tia lửa, khói)
        for particle in self.particles:
            # Tính alpha dựa trên tuổi thọ MAX thực tế, không chia cứng
            alpha = int(255 * min(1.0, particle['life'] / self.max_particle_life))
            
            # Vẽ trực tiếp bằng circle (đơn giản hơn dùng surface)
            pygame.draw.circle(
                surface,
                particle['color'],
                (int(particle['x']), int(particle['y'])),
                particle['size']
            )
        
        # (3) Vẽ ảnh chính của vụ nổ (nếu có ảnh explosion.png)
        if explosion_img:
            # Scale và xoay ảnh - ĐẢM BẢO SCALE KHÔNG ÂM
            scale_value = max(0.1, self.scale)  # Tối thiểu 0.1 để tránh âm
            scaled_size = (int(40 * scale_value), int(40 * scale_value))
            
            # Đảm bảo kích thước tối thiểu 1x1 pixel
            scaled_size = (max(1, scaled_size[0]), max(1, scaled_size[1]))
            
            scaled_img = pygame.transform.scale(explosion_img, scaled_size)
            rotated_img = pygame.transform.rotate(scaled_img, self.rotation)
            
            # Làm mờ dần khi gần hết thời gian
            if self.timer < 10:
                alpha = int(255 * (self.timer / 10))
                rotated_img.set_alpha(alpha)
            
            # Căn giữa ảnh
            rect = rotated_img.get_rect(center=(self.x, self.y))
            surface.blit(rotated_img, rect)
        
        else:
            # (Fallback) Nếu không có ảnh, vẽ hình tròn nổ thay thế
            progress = 1 - (self.timer / self.max_lifetime)
            radius = int(20 * self.scale)
            
            # Màu chuyển dần từ vàng → cam → đỏ
            if progress < 0.3:
                color = (255, 255, 100)
            elif progress < 0.6:
                color = (255, 150, 50)
            else:
                color = (200, 100, 100)
            
            # Độ mờ giảm dần
            alpha = int(255 * (self.timer / self.max_lifetime))
            
            # Tạo surface riêng cho vòng tròn
            circle_surf = pygame.Surface((radius * 2, radius * 2))
            circle_surf.set_colorkey((0, 0, 0))
            circle_surf.set_alpha(alpha)
            
            # Vẽ vòng tròn nổ
            pygame.draw.circle(circle_surf, color, (radius, radius), radius)
            surface.blit(circle_surf, (self.x - radius, self.y - radius))

    # ------------------------------------------------------------
    # Kiểm tra xem hiệu ứng nổ đã kết thúc chưa
    # ------------------------------------------------------------
    @property
    def done(self) -> bool:
        """Trả về True nếu vụ nổ kết thúc (timer = 0 và không còn particle)."""
        return self.timer <= 0 and len(self.particles) == 0



# ------------------------------------------------------------
# CLASS: ScreenShake — Hiệu ứng rung màn hình
# ------------------------------------------------------------
class ScreenShake:
    """Tạo hiệu ứng rung màn hình khi có va chạm hoặc nổ."""

    def __init__(self, intensity=10, duration=15):
        """
        intensity: độ mạnh của rung (số pixel tối đa dịch chuyển)
        duration: số frame hiệu ứng kéo dài
        """
        self.intensity = intensity
        self.duration = duration
        self.timer = duration  # Thời gian còn lại

    # --------------------------------------------------------
    def update(self):
        """Giảm timer mỗi frame cho đến khi hết."""
        if self.timer > 0:
            self.timer -= 1

    # --------------------------------------------------------
    def get_offset(self):
        """
        Trả về (offset_x, offset_y) — khoảng dịch chuyển màn hình hiện tại.
        Nếu timer = 0, trả về (0,0).
        """
        if self.timer <= 0:
            return (0, 0)
        
        # Cường độ rung giảm dần theo thời gian
        current_intensity = self.intensity * (self.timer / self.duration)
        
        # Tạo dịch chuyển ngẫu nhiên theo trục X và Y
        offset_x = random.randint(-int(current_intensity), int(current_intensity))
        offset_y = random.randint(-int(current_intensity), int(current_intensity))
        
        return (offset_x, offset_y)
    
    # --------------------------------------------------------
    @property
    def active(self):
        """Trả về True nếu hiệu ứng rung vẫn còn hoạt động."""
        return self.timer > 0
