import random
import pygame
import math

class Enemy:
    def __init__(self, word: str):
        self.origin_word = word
        self.progress = 0  # Số ký tự đã gõ đúng
        
        # Vị trí xuất phát
        self.x = random.randint(50, 750)
        self.y = random.randint(-150, -50)
        
        # Tốc độ ban đầu - RẤT CHẬM để dễ chơi
        self.base_speed = random.uniform(0.4, 1.2)  # Giảm xuống 0.4-1.2 (rất chậm)
        self.speed = self.base_speed
        
        # Gia tốc - rất nhẹ, hầu như không có
        self.acceleration = random.choice([0, 0, 0, 0, 0, 0.003, 0.005])  # Hầu như không tăng tốc
        
        # Chuyển động ngang (swing/sway)
        movement_type = random.choice(['straight', 'swing', 'zigzag', 'spiral'])
        self.movement_type = movement_type
        
        if movement_type == 'swing':
            self.swing_enabled = True
            self.swing_amplitude = random.uniform(20, 40)  # Biên độ lắc
            self.swing_frequency = random.uniform(0.015, 0.035)  # Tần số lắc
        elif movement_type == 'zigzag':
            self.swing_enabled = True
            self.swing_amplitude = random.uniform(30, 50)
            self.swing_frequency = random.uniform(0.05, 0.08)  # Tần số cao hơn = zigzag sắc nét
        elif movement_type == 'spiral':
            self.swing_enabled = True
            self.swing_amplitude = random.uniform(15, 35)
            self.swing_frequency = random.uniform(0.03, 0.05)
            self.spiral_growth = random.uniform(0.3, 0.6)  # Biên độ tăng dần
        else:  # straight
            self.swing_enabled = False
            self.swing_amplitude = 0
            self.swing_frequency = 0
        
        self.swing_offset = random.uniform(0, 2 * math.pi)  # Phase offset ngẫu nhiên
        self.time = 0  # Bộ đếm thời gian cho animation
        self.spiral_growth = getattr(self, 'spiral_growth', 0)
        
        # Hướng về phi thuyền
        self.target_ship = random.random() < 0.25  # 25% hướng về phi thuyền
        if self.target_ship:
            self.target_x = 400  # Vị trí phi thuyền (giữa màn hình)
            self.horizontal_speed = random.uniform(0.1, 0.3)  # Tốc độ ngang rất chậm
        else:
            self.horizontal_speed = 0
        
        # Cache rendering
        self._cached_text = None
        self._cached_progress = -1
        
        # Lưu vị trí X gốc để tính swing
        self.base_x = self.x
        
        # HP System - thanh máu
        self.max_hp = len(word)  # Máu = số ký tự trong từ
        self.current_hp = self.max_hp

    def move(self):
        """Di chuyển enemy xuống dưới với chuyển động thông minh"""
        # Tăng tốc độ theo thời gian (nếu có acceleration)
        self.speed += self.acceleration
        self.speed = min(self.speed, 2.5)  # Giới hạn tốc độ tối đa ở 2.5 (rất chậm)
        
        # Di chuyển xuống
        self.y += self.speed
        
        # Chuyển động đặc biệt theo loại
        if self.swing_enabled:
            self.time += 1
            
            if self.movement_type == 'swing':
                # Lắc lư mượt mà như con lắc
                swing_offset = math.sin(self.time * self.swing_frequency + self.swing_offset) * self.swing_amplitude
                self.x = self.base_x + swing_offset
                
            elif self.movement_type == 'zigzag':
                # Zigzag sắc nét (tam giác wave)
                wave = (self.time * self.swing_frequency + self.swing_offset) % (2 * math.pi)
                # Tạo tam giác wave thay vì sine wave
                if wave < math.pi:
                    zigzag_offset = (wave / math.pi) * 2 - 1  # -1 to 1
                else:
                    zigzag_offset = 1 - ((wave - math.pi) / math.pi) * 2  # 1 to -1
                self.x = self.base_x + zigzag_offset * self.swing_amplitude
                
            elif self.movement_type == 'spiral':
                # Spiral: biên độ tăng dần theo thời gian
                current_amplitude = self.swing_amplitude + (self.time * self.spiral_growth)
                current_amplitude = min(current_amplitude, self.swing_amplitude * 2.5)  # Giới hạn
                swing_offset = math.sin(self.time * self.swing_frequency + self.swing_offset) * current_amplitude
                self.x = self.base_x + swing_offset
        
        # Hướng về phía phi thuyền (nếu được chọn)
        if self.target_ship:
            dx = self.target_x - self.base_x
            if abs(dx) > 5:  # Chỉ di chuyển nếu còn xa
                move_x = self.horizontal_speed if dx > 0 else -self.horizontal_speed
                self.base_x += move_x
                if not self.swing_enabled:  # Nếu không swing thì cập nhật x trực tiếp
                    self.x = self.base_x

    def required_char(self) -> str:
        """Trả về ký tự tiếp theo cần gõ"""
        if self.progress < len(self.origin_word):
            return self.origin_word[self.progress].lower()
        return ""

    def hit_char(self, ch: str) -> bool:
        """
        Xử lý khi gõ đúng ký tự
        Returns True nếu enemy hoàn thành (gõ hết từ)
        """
        if ch.lower() == self.required_char():
            self.progress += 1
            self.current_hp -= 1  # Giảm HP khi bị hit
            return self.is_complete()
        return False

    def is_complete(self) -> bool:
        """
        METHOD QUAN TRỌNG - Kiểm tra enemy đã bị tiêu diệt hết chưa
        """
        return self.progress >= len(self.origin_word)

    def get_color_by_speed(self):
        """Trả về màu dựa trên tốc độ - nhanh hơn = đỏ hơn"""
        if self.speed > 2.0:
            return (255, 50, 50)  # Đỏ sáng - rất nhanh
        elif self.speed > 1.5:
            return (255, 100, 100)  # Đỏ vừa - nhanh
        elif self.speed > 0.8:
            return (255, 150, 150)  # Đỏ nhạt - trung bình
        else:
            return (255, 200, 200)  # Hồng nhạt - chậm
    
    def draw_hp_bar(self, surface: pygame.Surface, font: pygame.font.Font):
        """Vẽ thanh HP phía trên enemy"""
        if self.max_hp <= 0:
            return
        
        # Tính chiều dài thanh HP dựa trên text width
        text_width = font.size(self.origin_word)[0]
        bar_width = max(40, text_width)  # Ít nhất 40px
        bar_height = 5
        bar_x = self.x
        bar_y = self.y - 12  # Vẽ phía trên chữ
        
        # Background (màu xám đậm)
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        
        # HP bar (màu xanh lá -> vàng -> đỏ theo HP)
        hp_ratio = self.current_hp / self.max_hp
        filled_width = int(bar_width * hp_ratio)
        
        # Chọn màu theo HP ratio
        if hp_ratio > 0.6:
            hp_color = (50, 255, 50)  # Xanh lá - khỏe
        elif hp_ratio > 0.3:
            hp_color = (255, 255, 50)  # Vàng - trung bình
        else:
            hp_color = (255, 50, 50)  # Đỏ - yếu
        
        if filled_width > 0:
            pygame.draw.rect(surface, hp_color, (bar_x, bar_y, filled_width, bar_height))
        
        # Viền thanh HP
        pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Hiển thị số HP nếu từ dài (> 5 ký tự)
        if self.max_hp > 5:
            hp_text = font.render(f"{self.current_hp}/{self.max_hp}", True, (255, 255, 255))
            # Scale down font size
            small_font = pygame.font.SysFont("Arial", 16)
            hp_text = small_font.render(f"{self.current_hp}/{self.max_hp}", True, (255, 255, 255))
            text_rect = hp_text.get_rect()
            text_rect.midtop = (bar_x + bar_width // 2, bar_y + bar_height + 2)
            surface.blit(hp_text, text_rect)
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font, color=(255, 0, 0)):
        """Vẽ enemy lên màn hình với cache và visual effects"""
        shown = "_" * self.progress + self.origin_word[self.progress:]
        
        # Chọn màu động dựa trên tốc độ
        dynamic_color = self.get_color_by_speed()
        
        # Render text với màu động
        current_text = font.render(shown, True, dynamic_color)
        
        # Vẽ trail effect cho enemy nhanh (có gia tốc)
        if self.acceleration > 0.01:  # Giảm ngưỡng từ 0.02 xuống 0.01
            trail_color = (dynamic_color[0], dynamic_color[1], dynamic_color[2], 100)
            trail_alpha = max(50, min(150, int(self.acceleration * 5000)))  # Tăng multiplier để trail vẫn hiển thị rõ
            trail_surf = font.render(shown, True, dynamic_color)
            trail_surf.set_alpha(trail_alpha)
            surface.blit(trail_surf, (self.x, self.y - 3))  # Trail phía sau
        
        # Vẽ glow effect cho enemy đang hướng về phi thuyền
        if self.target_ship:
            glow_color = (255, 220, 100)  # Màu vàng cam
            glow_text = font.render(shown, True, glow_color)
            # Vẽ glow nhấp nháy nhẹ
            glow_alpha = int(150 + 50 * math.sin(self.time * 0.1))
            glow_text.set_alpha(glow_alpha)
            # Vẽ nhiều lớp offset để tạo hiệu ứng glow
            for offset in [(2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                surface.blit(glow_text, (self.x + offset[0], self.y + offset[1]))
        
        # Vẽ indicator cho các movement type đặc biệt
        if self.movement_type == 'spiral':
            # Vẽ dấu xoắn nhỏ bên cạnh
            spiral_color = (150, 150, 255)
            pygame.draw.circle(surface, spiral_color, (int(self.x - 10), int(self.y + 10)), 3, 1)
        elif self.movement_type == 'zigzag':
            # Vẽ dấu zigzag nhỏ
            zigzag_color = (255, 150, 255)
            pygame.draw.line(surface, zigzag_color, (int(self.x - 12), int(self.y + 8)), (int(self.x - 8), int(self.y + 12)), 2)
        
        # Vẽ HP bar trước (phía trên)
        self.draw_hp_bar(surface, font)
        
        # Vẽ text chính
        surface.blit(current_text, (self.x, self.y))
        
        # Vẽ speed indicator bar nếu tốc độ cao (bây giờ ít khi xuất hiện vì tốc độ chậm)
        if self.speed > 2.0:  # Điều chỉnh ngưỡng cho tốc độ mới
            bar_width = 30
            bar_height = 3
            bar_x = self.x
            bar_y = self.y - 8
            # Background bar
            pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # Speed bar (màu đỏ tăng dần)
            speed_ratio = min(1.0, (self.speed - 2.0) / 1.5)  # Điều chỉnh cho tốc độ rất chậm
            bar_color = (255, int(255 * (1 - speed_ratio)), 0)
            pygame.draw.rect(surface, bar_color, (bar_x, bar_y, int(bar_width * speed_ratio), bar_height))