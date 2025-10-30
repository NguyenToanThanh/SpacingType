# ============================================================
# FILE: challenge.py
# MÔ TẢ: Challenge Mode + màn kết quả sao (0-3)
# ============================================================

import pygame
from .settings import CHALLENGE_LEVELS, WIDTH, HEIGHT, WHITE, STAR_IMAGE_NAME, FPS, FONT_BOLD
from .utils import load_image, stars_from_lives, load_font


class Challenge:
    """Lớp quản lý chế độ Challenge với hệ thống sao"""
    
    def __init__(self, screen, background):
        """
        Khởi tạo bộ quản lý Challenge
        
        Args:
            screen: Bề mặt Pygame để hiển thị game
            background: Hình nền sử dụng
        """
        self.screen = screen  # Bề mặt hiển thị chính
        self.background = background  # Hình nền của game

        try:
            # Tải hình ảnh ngôi sao (kích thước 36x36 pixel) để hiển thị kết quả
            self.star_img = load_image(STAR_IMAGE_NAME, (36, 36))
        except Exception:
            # Nếu tải thất bại, sẽ dùng ngôi sao vẽ bằng code
            self.star_img = None

        # Font chữ cho tiêu đề (cỡ lớn)
        self.title_font = load_font(FONT_BOLD, 42)
        # Font chữ cho giao diện người dùng (cỡ vừa)
        self.ui_font    = load_font(FONT_BOLD, 24)

    def run(self, level: int):
        """
        Chạy và thực thi một màn challenge
        
        Args:
            level: Số thứ tự màn chơi (1-10)
            
        Returns:
            tuple: (completed, stars, score, lives_left)
                - completed: True nếu hoàn thành màn chơi
                - stars: Số sao đạt được (0-3)
                - score: Điểm số cuối cùng
                - lives_left: Số mạng còn lại
        """
        from .game import Game  # Import cục bộ để tránh import vòng

        # 1) Chuẩn hóa số màn: đảm bảo level nằm trong khoảng 1-10
        level = max(1, min(10, int(level)))
        # Lấy tốc độ tương ứng với màn từ cấu hình
        speed = CHALLENGE_LEVELS[level - 1]
        # Tính số kill cần đạt: màn 1 = 8 kills, màn 2 = 10 kills, màn 3 = 12 kills...
        target_kills = 8 + 2 * (level - 1)

        # 2) Tạo đối tượng game với tốc độ challenge
        game = Game(challenge_speed=speed)
        # Gán hình nền cho game
        game.background = self.background
        # Đặt mục tiêu số kill cho màn này
        game.target_kills = target_kills

        # 3) Chạy game
        game.run()

        # 3.1) Failsafe: đảm bảo có display và surface hợp lệ để vẽ popup kết quả
        self._handover_display_surface()

        # 4) Thu thập kết quả từ game vừa chơi
        completed  = bool(getattr(game, "completed", False))  # Đã hoàn thành chưa
        lives_left = int(getattr(game, "lives", 0))  # Số mạng còn lại
        score      = int(getattr(game, "score", 0))  # Điểm số
        user_quit  = bool(getattr(game, "request_quit", False))  # Người chơi thoát giữa chừng không

        # 4.1) Nếu display vẫn không sẵn sàng, trả về nhanh
        if not pygame.get_init() or pygame.display.get_surface() is None:
            # Tính số sao nếu hoàn thành, không thì 0 sao
            stars = stars_from_lives(lives_left) if completed else 0
            return completed, stars, score, lives_left

        # 4.2) Mở khóa event để chắc chắn nhận được phím bấm và chuột
        self._ensure_input_events_allowed()

        # 5) Hiển thị màn hình popup kết quả
        if not user_quit:  # Chỉ hiện popup nếu người chơi không thoát
            if completed:  # Nếu hoàn thành màn
                # Hiển thị màn "Level Clear" và tính số sao
                stars = self._show_level_result(lives_left, title=f"Level {level} Clear!")
            else:  # Nếu thất bại
                stars = 0
                # Hiển thị màn "Level Failed"
                self._show_failed(title=f"Level {level} Failed!")
        else:  # Người chơi thoát giữa chừng
            stars = 0

        # Trả về kết quả cuối cùng
        return completed, stars, score, lives_left

    # ------------- Failsafe handover -------------
    def _handover_display_surface(self):
        """
        Đảm bảo Challenge có surface hợp lệ để vẽ.
        - Nếu display đang tắt -> khởi tạo lại và tạo cửa sổ windowed
        - Nếu display có surface -> đồng bộ self.screen với surface hiện tại
        """
        try:
            # Nếu Pygame chưa khởi tạo hoặc display surface là None -> khởi tạo lại
            if not pygame.get_init():
                pygame.init()  # Khởi tạo lại Pygame

            surf = pygame.display.get_surface()  # Lấy surface hiện tại
            if surf is None:
                # Có thể trước đó game chạy FULLSCREEN rồi bị quit display
                # Khởi tạo lại cửa sổ windowed để hiện popup kết quả
                pygame.display.init()  # Khởi tạo module display
                pygame.display.set_caption("Challenge Result")  # Đặt tiêu đề cửa sổ
                surf = pygame.display.set_mode((WIDTH, HEIGHT))  # Tạo cửa sổ windowed
            # Đồng bộ screen với surface vừa lấy/tạo
            self.screen = surf
        except Exception as e:
            # In cảnh báo nếu có lỗi (không crash game)
            print(f"[WARN] _handover_display_surface failed: {e}")

    # ------------- Popup screens -------------

    
    def _show_level_result(self, lives_left: int, title: str) -> int:
        """
        Hiển thị màn hình Level Clear với số sao dựa trên số mạng còn lại.
        Có debounce để tránh ăn input còn sót/giữ phím.
        
        Args:
            lives_left: Số mạng còn lại
            title: Tiêu đề hiển thị
            
        Returns:
            int: Số sao đạt được (0-3)
        """
        # Tính số sao dựa trên số mạng còn lại
        stars = stars_from_lives(lives_left)
        clock = pygame.time.Clock()  # Đồng hồ để kiểm soát FPS

        # --- Cài đặt debounce để tránh input thừa ---
        pygame.event.clear()  # Xóa toàn bộ event còn sót trong hàng đợi
        pygame.key.set_repeat(0)  # Tắt tính năng lặp phím trong popup
        start_ms = pygame.time.get_ticks()  # Lưu thời điểm bắt đầu
        debounce_ms = 300  # Chặn input trong 300ms đầu
        ready_for_input = False  # Cờ: chỉ nhận input sau khi người chơi nhả hết phím

        while True:  # Vòng lặp hiển thị popup
            now = pygame.time.get_ticks()  # Thời gian hiện tại
            events = pygame.event.get()  # Lấy tất cả event

            # Xử lý event QUIT (đóng cửa sổ) - luôn cho phép
            for e in events:
                if e.type == pygame.QUIT:
                    return stars  # Trả về số sao và thoát

            # Kiểm tra xem đã sẵn sàng nhận input chưa
            if not ready_for_input:
                # Chờ qua thời gian debounce
                if now - start_ms >= debounce_ms:
                    # Kiểm tra xem có phím hoặc chuột nào đang được giữ không
                    keys = pygame.key.get_pressed()
                    mouse_pressed = any(pygame.mouse.get_pressed())
                    # Chỉ sẵn sàng khi KHÔNG có phím/chuột nào được giữ
                    if not any(keys) and not mouse_pressed:
                        ready_for_input = True
            else:
                # Đã sẵn sàng -> nhận phím/chuột để thoát popup
                for e in events:
                    if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                        return stars  # Trả về số sao khi người chơi bấm phím/chuột

            # --- Vẽ màn hình ---
            # Vẽ background
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill((10, 10, 20))  # Màu nền tối nếu không có background

            # Vẽ tiêu đề ở giữa màn hình, phía trên
            title_surf, _ = self.title_font.render(title, WHITE)
            self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))

            # Vẽ các ngôi sao theo hàng ngang
            cx = WIDTH // 2 - 60  # Vị trí x bắt đầu (căn giữa cho 3 sao)
            for i in range(stars):
                if self.star_img:  # Nếu có hình ảnh sao
                    # Vẽ hình sao, mỗi sao cách nhau 40 pixel
                    self.screen.blit(self.star_img, (cx + i * 40, HEIGHT // 2 - 10))
                else:  # Nếu không có hình, vẽ sao bằng polygon
                    self._draw_star(self.screen, (cx + i * 40 + 18, HEIGHT // 2 + 8), 16, WHITE)

            # Vẽ chữ hướng dẫn
            hint = "Press any key to continue"
            # Nếu chưa sẵn sàng nhận input, thêm "..." để báo hiệu đang chờ
            if not ready_for_input:
                hint += " ..."
            sub_surf, _ = self.ui_font.render(hint, WHITE)
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))

            # Cập nhật màn hình
            pygame.display.flip()
            # Giới hạn FPS
            clock.tick(FPS)


    def _show_failed(self, title: str):
        """
        Hiển thị màn hình Level Failed (có debounce giống Level Clear).
        
        Args:
            title: Tiêu đề hiển thị
        """
        clock = pygame.time.Clock()

        # --- Cài đặt debounce ---
        pygame.event.clear()  # Xóa event còn sót
        pygame.key.set_repeat(0)  # Tắt lặp phím
        start_ms = pygame.time.get_ticks()  # Lưu thời điểm bắt đầu
        debounce_ms = 300  # Chặn input 300ms
        ready_for_input = False  # Cờ sẵn sàng nhận input

        while True:  # Vòng lặp hiển thị popup
            now = pygame.time.get_ticks()
            events = pygame.event.get()

            # Xử lý đóng cửa sổ
            for e in events:
                if e.type == pygame.QUIT:
                    return

            # Kiểm tra sẵn sàng nhận input
            if not ready_for_input:
                if now - start_ms >= debounce_ms:  # Đã qua thời gian debounce
                    keys = pygame.key.get_pressed()
                    mouse_pressed = any(pygame.mouse.get_pressed())
                    # Sẵn sàng khi không có phím/chuột được giữ
                    if not any(keys) and not mouse_pressed:
                        ready_for_input = True
            else:
                # Nhận input để thoát
                for e in events:
                    if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                        return

            # --- Vẽ màn hình ---
            # Vẽ background
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill((10, 10, 20))

            # Vẽ tiêu đề "Failed"
            title_surf, _ = self.title_font.render(title, WHITE)
            self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

            # Vẽ chữ hướng dẫn
            hint = "Press any key to continue"
            if not ready_for_input:
                hint += " ..."  # Thêm "..." nếu chưa sẵn sàng
            sub_surf, _ = self.ui_font.render(hint, WHITE)
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))

            # Cập nhật và giới hạn FPS
            pygame.display.flip()
            clock.tick(FPS)


    # ------------- Utils -------------

    def _draw_star(self, surf, center, r, color):
        """
        Vẽ ngôi sao 5 cánh bằng polygon
        
        Args:
            surf: Surface để vẽ
            center: Tâm của ngôi sao (x, y)
            r: Bán kính ngôi sao
            color: Màu vẽ
        """
        import math
        x0, y0 = center  # Tọa độ tâm
        pts = []  # Danh sách các điểm của ngôi sao
        for i in range(10):  # 10 điểm: 5 đỉnh nhọn + 5 đỉnh lõm
            # Tính góc cho mỗi điểm (bắt đầu từ trên cùng)
            ang = -math.pi/2 + i * math.pi/5
            # Đỉnh nhọn có bán kính r, đỉnh lõm có bán kính r*0.5
            rr = r if i % 2 == 0 else r * 0.5
            # Tính tọa độ x, y của điểm
            pts.append((x0 + rr*math.cos(ang), y0 + rr*math.sin(ang)))
        # Vẽ polygon từ danh sách điểm
        pygame.draw.polygon(surf, color, pts)

    def _ensure_input_events_allowed(self):
        """
        Đảm bảo các event input (phím, chuột, quit) được phép xử lý
        """
        try:
            # Cho phép tất cả event
            pygame.event.set_allowed(None)
            # Đảm bảo các event quan trọng được cho phép
            pygame.event.set_allowed((pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT))
        except Exception:
            # Bỏ qua lỗi nếu có
            pass