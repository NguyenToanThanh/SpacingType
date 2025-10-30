import random
import pygame
import math
from .settings import WIDTH  # Import WIDTH để giới hạn vị trí

class Enemy:
    def __init__(self, word: str, existing_enemies=None, use_challenge_speed=False, challenge_speed=None):
        self.origin_word = word
        self.progress = 0  # Số ký tự đã gõ đúng
        
        # Tính chiều rộng từ để giới hạn spawn
        temp_font = pygame.font.SysFont("Arial", 32)
        self.word_width = temp_font.size(word)[0]
        
        # Vị trí xuất phát - tránh chồng lên enemy khác
        self.x, self.y = self._find_spawn_position(existing_enemies)
        
        # Tốc độ phụ thuộc vào độ dài từ
        word_length = len(word)
        
        if use_challenge_speed and challenge_speed is not None:
            # CHALLENGE MODE: Sử dụng tốc độ từ CHALLENGE_LEVELS
            # Điều chỉnh theo độ dài từ
            if word_length <= 4:  # Từ ngắn - Rơi nhanh hơn
                speed_multiplier = 1.2
            elif word_length <= 7:  # Từ trung bình
                speed_multiplier = 1.0
            elif word_length <= 10:  # Từ dài - Rơi chậm hơn
                speed_multiplier = 0.8
            else:  # Từ rất dài - Rơi rất chậm
                speed_multiplier = 0.6
            
            self.base_speed = challenge_speed * speed_multiplier
        else:
            # CLASSIC MODE: Giữ nguyên logic cũ - tốc độ cực chậm
            if word_length <= 4:  # Từ ngắn (3-4 ký tự) - Rơi cực chậm
                self.base_speed = random.uniform(0.2, 0.35)  # Giảm thêm
            elif word_length <= 7:  # Từ trung bình (5-7 ký tự) - Rơi siêu chậm
                self.base_speed = random.uniform(0.15, 0.25)
            elif word_length <= 10:  # Từ dài (8-10 ký tự) - Rơi cực kỳ chậm
                self.base_speed = random.uniform(0.1, 0.2)
            else:  # Từ rất dài (11+ ký tự) - Rơi như rùa bò
                self.base_speed = random.uniform(0.08, 0.15)
        
        self.speed = self.base_speed
        
        # Bộ đếm thời gian cho movement
        self.time = 0
        
        # Target phi thuyền
        self.target_ship = True
        self.target_x = WIDTH // 2
        
        # Tốc độ di chuyển ngang - chậm hơn tốc độ rơi để tạo đường cong mượt
        self.horizontal_speed = self.base_speed * 0.6  # 60% tốc độ rơi
        
        # HP System - thanh máu
        self.max_hp = len(word)  # Máu = số ký tự trong từ
        self.current_hp = self.max_hp
    
    def _find_spawn_position(self, existing_enemies):
        """
        Tìm vị trí spawn không chồng lên enemy khác và không thoát ra ngoài màn hình
        
        Giới hạn:
            - X: Từ margin_left đến (WIDTH - margin_right - word_width)
            - Y: Từ -200 đến -50 (spawn phía trên màn hình)
        """
        max_attempts = 20
        min_spawn_distance = 120  # Khoảng cách tối thiểu giữa các enemy khi spawn
        
        # Tính margin để từ không bị cắt
        margin_left = 10  # Khoảng cách từ mép trái
        margin_right = 10  # Khoảng cách từ mép phải
        
        # Giới hạn X: từ không được spawn quá sát mép trái hoặc vượt quá mép phải
        min_x = margin_left
        max_x = WIDTH - margin_right - self.word_width
        
        # Đảm bảo min_x < max_x (trường hợp từ quá dài)
        if min_x >= max_x:
            min_x = margin_left
            max_x = WIDTH - margin_right - 20  # Dự phòng cho từ rất dài
        
        for attempt in range(max_attempts):
            # Spawn trong giới hạn an toàn
            x = random.randint(int(min_x), int(max_x))
            y = random.randint(-200, -50)  # Spawn phía trên màn hình
            
            # Kiểm tra khoảng cách với các enemy hiện có
            if existing_enemies:
                too_close = False
                for other in existing_enemies:
                    dx = x - other.x
                    dy = y - other.y
                    distance = math.sqrt(dx * dx + dy * dy)
                    
                    if distance < min_spawn_distance:
                        too_close = True
                        break
                
                if not too_close:
                    return (x, y)
            else:
                return (x, y)
        
        # Nếu không tìm được vị trí tốt, spawn ở vùng xa với giới hạn
        safe_x = random.randint(int(min_x), int(max_x))
        safe_y = random.randint(-300, -150)
        return (safe_x, safe_y)

    def move(self, other_enemies=None):
        """
        Di chuyển enemy xuống dưới - LUÔN LUÔN HƯỚNG VỀ PHI THUYỀN với collision avoidance.
        
        GIỚI HẠN: Enemy không được di chuyển ra ngoài màn hình (giới hạn X).
        PRIORITY: Hướng về phi thuyền > Collision avoidance
        """
        self.time += 1
        
        # 1. Di chuyển theo trục Y (rơi xuống) - LUÔN RƠI
        self.y += self.speed
        
        # 2. Cập nhật tốc độ di chuyển ngang dựa trên progress
        # Tăng tốc độ horizontal để enemy hướng về tàu nhanh hơn
        progress = max(0, min(1, self.y / 600))  # Clamp progress trong [0, 1]
        if progress < 0.2:  # 20% đầu: tăng tốc nhanh
            self.horizontal_speed = self.base_speed * 1.0  # Tăng từ 0.5 lên 1.0
        elif progress < 0.5:  # 20-50%: tăng tốc mạnh
            self.horizontal_speed = self.base_speed * 1.5  # Tăng từ 0.9 lên 1.5
        else:  # 50-100%: tăng tốc CỰC MẠNH để lao vào phi thuyền
            self.horizontal_speed = self.base_speed * 2.0  # Tăng từ 1.3 lên 2.0
        
        # 3. Di chuyển theo trục X (hướng về phi thuyền) - LUÔN LUÔN DI CHUYỂN
        dx = self.target_x - self.x  # Khoảng cách đến phi thuyền
        
        # LUÔN DI CHUYỂN về phía phi thuyền (không có điều kiện dừng)
        if abs(dx) > 0.1:
            # Tính hướng di chuyển (-1: trái, +1: phải)
            direction = 1 if dx > 0 else -1
            
            # Di chuyển với tốc độ horizontal_speed (không giới hạn bởi dx)
            # Cho phép di chuyển nhanh ngay cả khi gần mục tiêu
            self.x += direction * self.horizontal_speed
        
        # 4. Collision avoidance - tránh chồng lên các enemy khác (ƯU TIÊN THẤP HƠN)
        if other_enemies:
            self.avoid_collision(other_enemies)
        
        # 5. GIỚI HẠN VỊ TRÍ X - Không cho enemy ra ngoài màn hình
        # Làm SAU collision avoidance để đảm bảo không ra ngoài
        margin_left = 10
        margin_right = 10
        min_x = margin_left
        max_x = WIDTH - margin_right - self.word_width
        
        # Clamp vị trí X trong giới hạn
        if self.x < min_x:
            self.x = min_x
        elif self.x > max_x:
            self.x = max_x
    
    def avoid_collision(self, other_enemies):
        """
        Tránh va chạm với các enemy khác - CHỈ ĐẨY NGANG, KHÔNG ẢNH HƯỞNG TRỤC Y.
        
        Lưu ý: Chỉ đẩy theo trục X để tránh làm gián đoạn chuyển động hướng về tàu.
        """
        # Reset offset trước khi tính toán
        push_x = 0
        collision_count = 0
        
        for other in other_enemies:
            if other is self:
                continue
            
            # Tính khoảng cách đến enemy khác
            dx = self.x - other.x
            dy = self.y - other.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Ngưỡng va chạm (dựa trên độ dài từ)
            base_distance = 60  # Giảm từ 80 xuống 60 - cho phép gần nhau hơn
            word_factor = (len(self.origin_word) + len(other.origin_word)) * 3  # Giảm từ 5 xuống 3
            min_distance = base_distance + word_factor
            
            if distance < min_distance and distance > 0.1:  # Tránh chia cho 0
                # Tính lực đẩy để tách ra - CHỈ THEO TRỤC X
                overlap = min_distance - distance
                push_strength = overlap * 0.2  # Giảm từ 0.5 xuống 0.2 (nhẹ hơn nhiều)
                
                # CHỈ ĐẨY THEO TRỤC X - KHÔNG ẢNH HƯỞNG TRỤC Y
                # Normalize chỉ theo X
                if abs(dx) > 0.1:
                    push_x += (dx / abs(dx)) * push_strength  # Chỉ lấy hướng (-1 hoặc +1)
                
                collision_count += 1
        
        # Áp dụng offset (CHỈ TRỤC X)
        max_push = 3  # Giảm từ 5 xuống 3
        if collision_count > 0:
            # Nếu va chạm nhiều enemy, đẩy mạnh hơn một chút
            max_push = min(5, 3 + collision_count * 0.5)
        
        # CHỈ ÁP DỤNG PUSH CHO TRỤC X - KHÔNG ĐỘNG VÀO Y
        self.x += max(-max_push, min(max_push, push_x))
        # KHÔNG CÓ: self.y += ...

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
        """Trả về màu dựa trên tốc độ - điều chỉnh cho tốc độ cực chậm"""
        if self.speed > 0.3:
            return (255, 100, 100)  # Đỏ vừa - nhanh (với tốc độ mới)
        elif self.speed > 0.2:
            return (255, 150, 150)  # Đỏ nhạt
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
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        """Vẽ enemy lên màn hình"""
        shown = "_" * self.progress + self.origin_word[self.progress:]
        
        # Chọn màu động dựa trên tốc độ
        dynamic_color = self.get_color_by_speed()
        
        # Render text với màu động
        current_text = font.render(shown, True, dynamic_color)
        
        # LOẠI BỎ mũi tên - gây rối mắt và không cần thiết
        # Người chơi có thể thấy enemy di chuyển về phía phi thuyền
        # if self.target_ship and abs(self.target_x - self.x) > 5:
        #     ... (removed)
        
        # Vẽ HP bar trước (phía trên)
        self.draw_hp_bar(surface, font)
        
        # Vẽ text chính
        surface.blit(current_text, (self.x, self.y))
        
        # Vẽ speed indicator bar - LOẠI BỎ vì tốc độ đều và chậm
        # if self.speed > 0.6:
