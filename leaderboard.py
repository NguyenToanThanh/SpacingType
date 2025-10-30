# ============================================================
# FILE: leaderboard.py
# MÔ TẢ: Hiển thị bảng xếp hạng cho Classic và Challenge modes
#        với hệ thống scroll, drag scrollbar, và lưu/load từ JSON
# ============================================================

import json
from pathlib import Path
import pygame

from .settings import WIDTH, HEIGHT, WHITE, FONT_BOLD
from .utils import load_font, safe_json_load, safe_json_save

DEFAULT_DATA_FILE = Path("save/leaderboard.json")


# ============================================================
# HELPER FUNCTION - Xử lý render text cho cả pygame.font và freetype
# ============================================================
def render_text(font, text, color):
    """
    Trả về Surface an toàn cho cả pygame.font.Font và pygame.freetype.Font.
    
    pygame có 2 hệ thống font khác nhau:
    - pygame.font.Font.render(text, antialias, color) -> Surface
    - pygame.freetype.Font.render(text, color) -> (Surface, Rect)
    
    Function này normalize output thành Surface để sử dụng thống nhất.
    
    Args:
        font: pygame.font.Font hoặc pygame.freetype.Font instance
        text (str): Text cần render
        color (tuple): RGB color
        
    Returns:
        pygame.Surface: Rendered text surface
    """
    # Import freetype nếu có
    try:
        import pygame.freetype as ft
    except Exception:
        ft = None

    # pygame.font.Font -> render(text, antialias, color) -> Surface
    if isinstance(font, pygame.font.Font):
        return font.render(text, True, color)

    # pygame.freetype.Font -> render(text, color) -> (Surface, Rect)
    if ft is not None and isinstance(font, ft.Font):
        surf, _ = font.render(text, color)
        return surf

    # Fallback: thử gọi render và bóc phần Surface nếu trả về tuple
    out = font.render(text, color)
    return out[0] if isinstance(out, tuple) else out


# ============================================================
# LEADERBOARD CLASS - Quản lý bảng xếp hạng với scroll
# ============================================================
class Leaderboard:
    """
    Hiển thị và quản lý bảng xếp hạng cho 2 game modes: Classic và Challenge.
    
    Features:
    - Lưu/load dữ liệu từ JSON file
    - Scroll với mouse wheel và drag scrollbar
    - Toggle giữa Classic/Challenge mode bằng A/D hoặc Left/Right
    - ESC để thoát về menu
    
    Data Structure:
    {
        "classic": [
            {"name": "Player1", "score": 1000},
            {"name": "Player2", "score": 900}, ...
        ],
        "challenge": [
            {"name": "Player1", "level": 10, "lives": 3},
            {"name": "Player2", "level": 9, "lives": 2}, ...
        ]
    }
    
    Attributes:
        data_file (Path): Đường dẫn file JSON lưu leaderboard
        font_* (pygame.Font): Các font cho UI components
        scrollbar_drag (bool): True khi đang drag scrollbar
        scrollbar_drag_offset (int): Offset chuột so với đầu scrollbar
        mode_index (int): 0=Classic, 1=Challenge
        scroll_offset (int): Số dòng đã scroll (0-based)
        max_visible_rows (int): Số dòng hiển thị tối đa trên màn hình
        data (dict): Dữ liệu leaderboard {"classic": [], "challenge": []}
    """
    
    def __init__(self):
        """
        Khởi tạo Leaderboard với fonts, state và load dữ liệu từ JSON.
        """
        # File lưu leaderboard (có thể override cho testing)
        self.data_file = DEFAULT_DATA_FILE
        
        # Fonts cho các thành phần UI
        self.font_title = load_font(FONT_BOLD, 64)   # "LEADERBOARD"
        self.font_header = load_font(FONT_BOLD, 32)  # Headers cột
        self.font_entry = load_font(FONT_BOLD, 28)   # Entries bảng
        self.font_num = load_font(FONT_BOLD, 28)     # Số liệu (score/level/lives)
        # Sử dụng font hệ thống cho hint để tránh lỗi phông/AttributeError
        self.font_hint = pygame.font.SysFont(None, 20)

        # Scrollbar drag state
        self.scrollbar_drag = False         # Đang drag scrollbar?
        self.scrollbar_drag_offset = 0      # Offset chuột so với đầu scrollbar

        # Mode state
        self.mode_index = 0  # 0 = classic, 1 = challenge
        self.modes = ["classic", "challenge"]

        # Scroll state
        self.scroll_offset = 0              # Dòng bắt đầu hiển thị (0-based)
        self.max_visible_rows = 10          # Số dòng hiển thị tối đa

        # Data
        self.data = {"classic": [], "challenge": []}
        self._load()  # Load từ JSON file

    # ============================================================
    # PUBLIC API - Interface cho external code
    # ============================================================
    
    def set_data_file(self, path: Path):
        """
        Override file path cho lưu/load dữ liệu (dùng cho testing).
        
        Args:
            path (Path): Đường dẫn file JSON mới
        """
        self.data_file = Path(path)
        self._load()

    def get_top(self, mode: str, n: int = 10) -> list[dict]:
        """
        Lấy top N records cho mode cụ thể.
        
        Args:
            mode (str): "classic" hoặc "challenge"
            n (int): Số records muốn lấy (default 10)
            
        Returns:
            list[dict]: Danh sách top N records đã sort
        """
        return (self.data.get(mode, []) or [])[: max(0, int(n))]

    def get_rank(self, mode: str, key: dict) -> int | None:
        """
        Tìm rank (1-based) của một record trong leaderboard.
        
        Args:
            mode (str): "classic" hoặc "challenge"
            key (dict): Record cần tìm (phải match chính xác)
                - Classic: {"name": "...", "score": 123}
                - Challenge: {"name": "...", "level": 5, "lives": 2}
                
        Returns:
            int: Rank (1-based) nếu tìm thấy, None nếu không có
        """
        rows = self.data.get(mode, []) or []
        for i, row in enumerate(rows):
            if row == key:
                return i + 1
        return None

    # ============================================================
    # IO - Load/Save JSON
    # ============================================================
    
    def _load(self):
        """
        Load dữ liệu leaderboard từ JSON file.
        Nếu file không tồn tại hoặc invalid, khởi tạo data rỗng.
        """
        loaded = safe_json_load(self.data_file, default=None)
        if isinstance(loaded, dict):
            self.data = loaded
            self.data.setdefault("classic", [])
            self.data.setdefault("challenge", [])
        else:
            self.data = {"classic": [], "challenge": []}

    def _save(self):
        """
        Lưu dữ liệu leaderboard vào JSON file.
        """
        safe_json_save(self.data_file, self.data)

    # ============================================================
    # UPDATE - Thêm scores mới
    # ============================================================
    
    def add_classic(self, name: str, score: int):
        """
        Thêm score mới cho Classic mode.
        
        Process:
        1. Tạo record {"name": "...", "score": 123}
        2. Thêm vào danh sách
        3. Sort theo score giảm dần (cao nhất lên đầu)
        4. Giữ tối đa 50 records
        5. Lưu vào JSON
        
        Args:
            name (str): Tên người chơi
            score (int): Điểm số
        """
        row = {"name": str(name), "score": int(score)}
        self.data["classic"].append(row)
        # Sort giảm dần theo score
        self.data["classic"].sort(key=lambda x: x.get("score", 0), reverse=True)
        # Giữ tối đa 50 records
        self.data["classic"] = self.data["classic"][:50]
        self._save()

    def add_challenge(self, name: str, level: int, lives: int):
        """
        Thêm score mới cho Challenge mode.
        
        Process:
        1. Tạo record {"name": "...", "level": 5, "lives": 2}
        2. Thêm vào danh sách
        3. Sort theo (level giảm dần, lives giảm dần)
        4. Giữ tối đa 50 records
        5. Lưu vào JSON
        
        Args:
            name (str): Tên người chơi
            level (int): Level đạt được (1-10)
            lives (int): Số mạng còn lại (0-3)
        """
        row = {"name": str(name), "level": int(level), "lives": int(lives)}
        self.data["challenge"].append(row)
        # Sort: level cao hơn lên trước, nếu bằng thì lives cao hơn lên trước
        self.data["challenge"].sort(key=lambda x: (x.get("level", 0), x.get("lives", 0)), reverse=True)
        # Giữ tối đa 50 records
        self.data["challenge"] = self.data["challenge"][:50]
        self._save()

    def add_score(self, mode: str, row: dict):
        """
        Generic method để thêm score (dùng cho programmatic/testing).
        
        Args:
            mode (str): "classic" hoặc "challenge"
            row (dict): Data record
                - Classic: {"name": "...", "score": 123}
                - Challenge: {"name": "...", "level": 5, "lives": 2}
                
        Raises:
            ValueError: Nếu mode không hợp lệ
        """
        if mode not in ("classic", "challenge"):
            raise ValueError("mode must be 'classic' or 'challenge'")
        if mode == "classic":
            name = str(row.get("name", ""))
            try:
                score = int(row.get("score", 0))
            except Exception:
                score = 0
            self.add_classic(name, score)
        else:
            name = str(row.get("name", ""))
            try:
                level = int(row.get("level", 0))
            except Exception:
                level = 0
            try:
                lives = int(row.get("lives", 0))
            except Exception:
                lives = 0
            self.add_challenge(name, level, lives)

    # ============================================================
    # INPUT HANDLING - Keyboard và mouse controls
    # ============================================================
    
    def handle(self, event):
        """
        Xử lý input events cho leaderboard.
        
        Controls:
        - ESC/Backspace: Thoát về menu (return "__EXIT__")
        - A/D hoặc Left/Right: Toggle giữa Classic/Challenge mode
        - Up/Down arrow: Scroll lên/xuống 1 dòng
        - Mouse wheel: Scroll up (button 4) / down (button 5)
        - Mouse drag: Click và kéo scrollbar để scroll nhanh
        
        Args:
            event (pygame.Event): Event cần xử lý
            
        Returns:
            str: "__EXIT__" nếu người dùng nhấn ESC, None nếu không
        """
        if event.type == pygame.KEYDOWN:
            # ESC hoặc Backspace: Thoát về menu
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return "__EXIT__"
                
            # A/D hoặc Left/Right: Toggle mode
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                self.mode_index = 1 - self.mode_index  # toggle 0 <-> 1
                self.scroll_offset = 0  # Reset scroll khi đổi mode
                
            # Up arrow: Scroll lên
            if event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
                
            # Down arrow: Scroll xuống
            if event.key == pygame.K_DOWN:
                mode = self.modes[self.mode_index]
                total = len(self.data.get(mode, []))
                max_scroll = max(0, total - self.max_visible_rows)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Mouse wheel up
            if event.button == 4:
                self.scroll_offset = max(0, self.scroll_offset - 1)
                
            # Mouse wheel down
            elif event.button == 5:
                mode = self.modes[self.mode_index]
                total = len(self.data.get(mode, []))
                max_scroll = max(0, total - self.max_visible_rows)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
                
            # Left click: Kiểm tra click vào scrollbar để bắt đầu drag
            elif event.button == 1:
                # Tính toán lại vùng bảng xếp hạng và scrollbar
                head_rect = pygame.Rect(WIDTH // 2 - 360, 200, 720, 52)
                table_top = head_rect.bottom + 22
                table_bottom = HEIGHT - 60
                row_height = 40
                self.max_visible_rows = max(1, (table_bottom - table_top) // row_height)
                
                # Vị trí scrollbar
                scrollbar_x = head_rect.right + 10
                scrollbar_y = table_top
                
                # Tính kích thước scrollbar dựa trên tỷ lệ visible/total
                total_rows = len(self.data.get(self.modes[self.mode_index], []))
                scrollbar_h = (self.max_visible_rows / max(1, total_rows)) * (table_bottom - table_top)
                scrollbar_h = min(table_bottom - table_top, max(30, scrollbar_h))
                
                max_scroll = max(0, total_rows - self.max_visible_rows)
                if max_scroll > 0:
                    # Vị trí thanh cuộn hiện tại
                    bar_y = table_top + int((self.scroll_offset / max_scroll) * (table_bottom - table_top - scrollbar_h)) if max_scroll else table_top
                    
                    # Kiểm tra click vào scrollbar
                    mouse_x, mouse_y = event.pos
                    if scrollbar_x <= mouse_x <= scrollbar_x + 12 and bar_y <= mouse_y <= bar_y + scrollbar_h:
                        self.scrollbar_drag = True
                        self.scrollbar_drag_offset = mouse_y - bar_y  # Lưu offset chuột so với đầu scrollbar
                        
        elif event.type == pygame.MOUSEBUTTONUP:
            # Thả chuột: Dừng drag
            if event.button == 1:
                self.scrollbar_drag = False
                
        elif event.type == pygame.MOUSEMOTION:
            # Di chuyển chuột khi đang drag scrollbar
            if self.scrollbar_drag:
                # Tính toán lại vùng bảng xếp hạng
                head_rect = pygame.Rect(WIDTH // 2 - 360, 200, 720, 52)
                table_top = head_rect.bottom + 22
                table_bottom = HEIGHT - 60
                row_height = 40
                self.max_visible_rows = max(1, (table_bottom - table_top) // row_height)
                
                total_rows = len(self.data.get(self.modes[self.mode_index], []))
                max_scroll = max(0, total_rows - self.max_visible_rows)
                
                # Tính kích thước scrollbar
                scrollbar_h = (self.max_visible_rows / max(1, total_rows)) * (table_bottom - table_top)
                scrollbar_h = min(table_bottom - table_top, max(30, scrollbar_h))
                
                # Tính scroll offset từ vị trí chuột
                mouse_y = event.pos[1]
                rel_y = mouse_y - table_top - self.scrollbar_drag_offset
                rel_y = max(0, min(rel_y, (table_bottom - table_top - scrollbar_h)))
                
                if max_scroll > 0:
                    self.scroll_offset = int((rel_y / (table_bottom - table_top - scrollbar_h)) * max_scroll)
                    self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
                    
        return None

    # ------------------ DRAW ------------------
    def draw(self, surf: pygame.Surface, background: pygame.Surface | None = None):
        # background
        if background:
            surf.blit(background, (0, 0))
        else:
            surf.fill((14, 16, 24))

        # title
        title = render_text(self.font_title, "LEADERBOARD", WHITE)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 70)))

        # mode box + arrows
        mode_name = "Classic" if self.modes[self.mode_index] == "classic" else "Challenge"
        mode_text = render_text(self.font_header, f"Game Mode: {mode_name}", WHITE)
        box = pygame.Rect(0, 0, mode_text.get_width() + 60, 56)
        box.center = (WIDTH // 2, 140)
        pygame.draw.rect(surf, (70, 70, 90), box, border_radius=14)
        surf.blit(mode_text, mode_text.get_rect(center=box.center))

        # table header box
        head_rect = pygame.Rect(WIDTH // 2 - 360, 200, 720, 52)
        pygame.draw.rect(surf, (90, 92, 110), head_rect, border_radius=12)

        # Tính toán vùng bảng xếp hạng không đè lên hint
        table_top = head_rect.bottom + 22
        table_bottom = HEIGHT - 60  # chừa chỗ cho hint
        row_height = 40
        self.max_visible_rows = max(1, (table_bottom - table_top) // row_height)

        if self.modes[self.mode_index] == "classic":
            COL_RANK_X = head_rect.x + 20
            COL_NAME_X = head_rect.x + 140
            COL_SCORE_R = head_rect.right - 20
            h_rank = render_text(self.font_header, "RANK", WHITE)
            h_name = render_text(self.font_header, "NAME", WHITE)
            h_score = render_text(self.font_header, "SCORE", WHITE)
            surf.blit(h_rank, (COL_RANK_X, head_rect.centery - h_rank.get_height() // 2))
            surf.blit(h_name, (COL_NAME_X, head_rect.centery - h_name.get_height() // 2))
            surf.blit(h_score, h_score.get_rect(right=COL_SCORE_R, centery=head_rect.centery))

            all_rows = self.data.get("classic") or []
            rows = all_rows[self.scroll_offset:self.scroll_offset + self.max_visible_rows]
            y = table_top
            if not all_rows:
                msg = render_text(self.font_entry, "No scores yet...", (180, 180, 180))
                surf.blit(msg, msg.get_rect(center=(WIDTH // 2, y + 80)))
            else:
                for i, row in enumerate(rows):
                    rank = render_text(self.font_entry, f"{self.scroll_offset + i + 1}.", (255, 220, 0))
                    surf.blit(rank, (COL_RANK_X, y))
                    name = render_text(self.font_entry, str(row.get("name", ""))[:18], WHITE)
                    surf.blit(name, (COL_NAME_X, y))
                    score = render_text(self.font_num, str(row.get("score", 0)), (200, 255, 200))
                    surf.blit(score, score.get_rect(right=COL_SCORE_R, y=y))
                    y += row_height
        else:
            COL_RANK_X = head_rect.x + 20
            COL_NAME_X = head_rect.x + 140
            COL_LEVEL_R = head_rect.x + 520
            COL_LIVES_R = head_rect.right - 20
            h_rank = render_text(self.font_header, "RANK", WHITE)
            h_name = render_text(self.font_header, "NAME", WHITE)
            h_level = render_text(self.font_header, "LEVEL", WHITE)
            h_lives = render_text(self.font_header, "LIVES", WHITE)
            surf.blit(h_rank, (COL_RANK_X, head_rect.centery - h_rank.get_height() // 2))
            surf.blit(h_name, (COL_NAME_X, head_rect.centery - h_name.get_height() // 2))
            surf.blit(h_level, h_level.get_rect(right=COL_LEVEL_R, centery=head_rect.centery))
            surf.blit(h_lives, h_lives.get_rect(right=COL_LIVES_R, centery=head_rect.centery))

            all_rows = self.data.get("challenge") or []
            rows = all_rows[self.scroll_offset:self.scroll_offset + self.max_visible_rows]
            y = table_top
            if not all_rows:
                msg = render_text(self.font_entry, "No scores yet...", (180, 180, 180))
                surf.blit(msg, msg.get_rect(center=(WIDTH // 2, y + 80)))
            else:
                for i, row in enumerate(rows):
                    rank = render_text(self.font_entry, f"{self.scroll_offset + i + 1}.", (255, 220, 0))
                    surf.blit(rank, (COL_RANK_X, y))
                    name = render_text(self.font_entry, str(row.get("name", ""))[:18], WHITE)
                    surf.blit(name, (COL_NAME_X, y))
                    level = render_text(self.font_num, str(row.get("level", 0)), (200, 255, 255))
                    lives = render_text(self.font_num, str(row.get("lives", 0)), (255, 230, 180))
                    surf.blit(level, level.get_rect(right=COL_LEVEL_R, y=y))
                    surf.blit(lives, lives.get_rect(right=COL_LIVES_R, y=y))
                    y += row_height

        # Vẽ thanh cuộn dọc nếu cần
        total_rows = len(all_rows)
        if total_rows > self.max_visible_rows:
            scrollbar_x = head_rect.right + 10
            scrollbar_y = table_top
            scrollbar_w = 12
            scrollbar_h = (self.max_visible_rows / total_rows) * (table_bottom - table_top)
            scrollbar_h = min(table_bottom - table_top, max(30, scrollbar_h))
            max_scroll = max(0, total_rows - self.max_visible_rows)
            bar_y = table_top + int((self.scroll_offset / max_scroll) * (table_bottom - table_top - scrollbar_h)) if max_scroll else table_top
            # Nền thanh cuộn
            pygame.draw.rect(surf, (60, 60, 80), (scrollbar_x, table_top, scrollbar_w, table_bottom - table_top), border_radius=6)
            # Thanh cuộn
            pygame.draw.rect(surf, (180, 180, 220), (scrollbar_x, bar_y, scrollbar_w, scrollbar_h), border_radius=6)

        # hint (luôn ở dưới cùng, không bị che, font rõ ràng)
        hint = render_text(self.font_hint, "A/D to switch mode • up/down or drag scrollbar • ESC to exit", (220, 220, 220))
        surf.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 34)))