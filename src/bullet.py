import math
import pygame
from .settings import WIDTH, SHIP_Y, WHITE

class Bullet:
    """
    Viên đạn gắn với 1 enemy cụ thể và 1 ký tự người chơi vừa gõ.
    Bay tới vị trí ký tự (snapshot) và biến mất khi chạm tới đó.
    """
    def __init__(self, target_enemy, typed_char: str, font: pygame.font.Font, char_index: int):
        self.x = WIDTH // 2
        self.y = SHIP_Y
        self.target_enemy = target_enemy
        self.typed_char = typed_char
        self.char_index = char_index  # Vị trí ký tự trong từ
        self.font = font
        self.hit = False  # Đã chạm mục tiêu hay chưa

        # Snapshot vị trí ký tự mục tiêu tại thời điểm bắn
        tx, ty = self._compute_char_position()
        self.target_x = tx
        self.target_y = ty

        # Tính vector hướng từ tàu tới điểm snapshot
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = max(1.0, math.hypot(dx, dy))

        self.dir_x = dx / distance
        self.dir_y = dy / distance
        self.speed = 10  # Giảm tốc độ viên đạn để phù hợp với game chậm hơn

    def _compute_char_position(self):
        """Tính tọa độ ký tự đích dựa trên char_index (tại thời điểm hiện tại)."""
        word = self.target_enemy.origin_word

        # X của ký tự thứ char_index
        text_before = word[:self.char_index]
        w_before = self.font.render(text_before, True, (255, 0, 0)).get_width()
        char_x = self.target_enemy.x + w_before

        # Y (giữa chiều cao chữ)
        ch = word[self.char_index]
        char_surface = self.font.render(ch, True, (255, 0, 0))
        char_y = self.target_enemy.y + char_surface.get_height() // 2

        # Tâm ký tự
        return (char_x + char_surface.get_width() // 2, char_y)

    def move(self):
        """Di chuyển đạn tiến gần về mục tiêu snapshot; snap và đánh dấu hit nếu sắp chạm."""
        if self.hit:
            return

        # Khoảng cách còn lại tới mục tiêu
        rem_dx = self.target_x - self.x
        rem_dy = self.target_y - self.y
        rem_dist = math.hypot(rem_dx, rem_dy)

        # Nếu một bước di chuyển sẽ vượt quá mục tiêu → gắn thẳng vào mục tiêu và hit
        if rem_dist <= self.speed:
            self.x = self.target_x
            self.y = self.target_y
            self.hit = True
            return

        # Ngược lại tiếp tục bay
        self.x += self.dir_x * self.speed
        self.y += self.dir_y * self.speed

    def draw(self, surface: pygame.Surface):
        """Vẽ viên đạn (không vẽ khi đã hit)."""
        if not self.hit:
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 5)
            pygame.draw.circle(surface, (255, 255, 0), (int(self.x), int(self.y)), 3)

    def is_hit(self) -> bool:
        """Đã chạm mục tiêu chưa."""
        return self.hit

    def is_out_of_bounds(self) -> bool:
        """Ra ngoài màn hình chưa (phòng hờ)."""
        return self.y < -10 or self.y > 800 or self.x < -10 or self.x > WIDTH + 10