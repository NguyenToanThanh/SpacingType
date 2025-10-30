# ============================================================
# SPACE TYPING GAME - MAIN ENTRY POINT
# ============================================================
# File: main.py
# Mô tả: Điểm khởi động chính của game, quản lý state và luồng chuyển đổi giữa các màn hình
# Chức năng chính:
#   - Khởi tạo pygame và mixer
#   - Phát nhạc nền chính (nhacnen.mp3)
#   - Quản lý 4 states: MENU, CLASSIC, CHALLENGE, LEADERBOARD
#   - Xử lý chuyển đổi giữa các states
#   - Xử lý input global (F12 screenshot, ESC/Exit)
#   - Tích hợp video background cho gameplay
# ============================================================

import pygame
from .settings import WIDTH, HEIGHT, STATE_MENU, STATE_CLASSIC, STATE_CHALLENGE, STATE_LEADERBOARD, FPS, VSYNC, IMAGE_DIR, SOUND_DIR
from .utils import load_image, load_progress, save_progress, take_screenshot
from .game import Game
from .menu import MainMenu
from .leaderboard import Leaderboard
from .challenge import Challenge
from .level_select import LevelSelect
from .name_prompt import NamePrompt


def main():
    """
    Hàm chính của game - điều khiển toàn bộ luồng game.
    
    Flow:
        1. Khởi tạo pygame, mixer, screen (fullscreen)
        2. Load nhạc nền chính (nhacnen.mp3)
        3. Khởi tạo các screen: menu, leaderboard
        4. Vòng lặp chính với state machine:
           - STATE_MENU: Menu chính (Classic, Challenge, Leaderboard, Exit)
           - STATE_CLASSIC: Classic mode (chơi đến hết mạng)
           - STATE_CHALLENGE: Challenge mode (10 levels, 3 sao mỗi level)
           - STATE_LEADERBOARD: Bảng xếp hạng
        5. Xử lý exit và cleanup
    
    States:
        - MENU: Menu chính với 4 options
        - CLASSIC: Chơi vô hạn cho đến khi hết 3 mạng
        - CHALLENGE: Chọn level (1-10), mục tiêu kills, tính sao
        - LEADERBOARD: Hiển thị top scores
    
    Input:
        - F12: Chụp màn hình (menu, level select)
        - ESC: Quay về menu hoặc thoát
        - Exit button: Thoát game
    """
    # ============================================================
    # INITIALIZATION
    # ============================================================
    pygame.init()
    pygame.mixer.init()

    # ============================================================
    # BACKGROUND MUSIC - Nhạc nền chính (chạy suốt khi không trong gameplay)
    # ============================================================
    try:
        pygame.mixer.music.load(str(SOUND_DIR / "nhacnen.mp3"))
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)  # -1 = loop vô hạn
    except Exception as e:
        print("Không thể tải hoặc phát nhạc nền:", e)

    # ============================================================
    # DISPLAY SETUP - Fullscreen với hardware acceleration và vsync
    # ============================================================
    # HWSURFACE: Hardware surface cho render nhanh hơn
    # DOUBLEBUF: Double buffering chống screen tearing
    # FULLSCREEN: Chế độ toàn màn hình
    # vsync: Đồng bộ với màn hình (giảm tearing)
    flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=1 if VSYNC else 0)
    pygame.display.set_caption("Space Typing Game")

    # ============================================================
    # BACKGROUND IMAGE - Background mặc định cho menu/leaderboard
    # ============================================================
    try:
        background = load_image("background.jpg", (WIDTH, HEIGHT))
    except Exception:
        background = None

    # ============================================================
    # INITIALIZE SCREENS
    # ============================================================
    lb = Leaderboard()  # Bảng xếp hạng (persistent data)
    state = STATE_MENU   # State ban đầu

    # Callback functions để chuyển state từ menu
    def goto_classic():
        nonlocal state
        state = STATE_CLASSIC

    def goto_challenge():
        nonlocal state
        state = STATE_CHALLENGE

    def goto_leaderboard():
        nonlocal state
        state = STATE_LEADERBOARD

    menu = MainMenu(goto_classic, goto_challenge, goto_leaderboard, background)

    # ============================================================
    # MAIN GAME LOOP - State machine điều khiển luồng game
    # ============================================================
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # ============================================================
        # STATE: MENU - Menu chính
        # ============================================================
        if state == STATE_MENU:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                # Xử lý phím F12 để chụp màn hình menu
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F12:
                    take_screenshot(screen)
                else:
                    menu.handle(e)
            
            # Kiểm tra xem người chơi có nhấn nút Exit không
            if menu.should_quit:
                running = False
            
            menu.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)

        # ============================================================
        # STATE: CLASSIC - Classic Mode (chơi đến hết mạng)
        # ============================================================
        elif state == STATE_CLASSIC:
            # Import động để tránh circular dependencies
            from .utils import list_background_files, get_music_for_background, is_video_file
            from .background_select import BackgroundSelect
            from .video_background import VideoBackground

            # --- 1) Background Selection Screen ---
            bg_files = list_background_files()  # Lấy danh sách backgrounds từ assets/images/backgrounds/
            chosen_bg = None

            if bg_files:
                # Hiển thị màn hình chọn background
                selector = BackgroundSelect(bg_files)
                while chosen_bg is None and running:
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT:
                            running = False
                            chosen_bg = "__CANCEL__"  # Đánh dấu người chơi đóng game
                            break
                        res = selector.handle(e)  # ESC trả về "__CANCEL__"
                        if res is not None:
                            chosen_bg = res
                    if not running:
                        break
                    selector.draw(screen)
                    pygame.display.flip()
                    clock.tick(FPS)
                if not running:
                    break
                if chosen_bg == "__CANCEL__":
                    # Xóa events tránh event leak
                    pygame.event.clear()
                    state = STATE_MENU  # Quay về menu
                    continue

            # --- 2) Music Handling ---
            # 🔇 Tạm dừng nhạc nền chính khi vào gameplay
            pygame.mixer.music.pause()

            # 🎵 Lấy nhạc tương ứng với background đã chọn
            # Mapping trong utils.py: background.jpg -> music3.mp3, etc.
            music_file = get_music_for_background(chosen_bg) if chosen_bg and chosen_bg != "__CANCEL__" else None

            # --- 3) Video Background Setup ---
            # Hỗ trợ cả video (.mp4, .avi, .webm) và image (.jpg, .png)
            video_bg = None
            print(f"[Main] Chosen background: {chosen_bg}")
            print(f"[Main] Is video file: {is_video_file(chosen_bg) if chosen_bg else False}")
            
            if chosen_bg and chosen_bg != "__CANCEL__":
                if is_video_file(chosen_bg):
                    # Tạo video background (sử dụng OpenCV)
                    try:
                        video_path = IMAGE_DIR / chosen_bg
                        print(f"[Main] Loading video from: {video_path}")
                        video_bg = VideoBackground(str(video_path), (WIDTH, HEIGHT))
                        print(f"[Main] ✅ Video background loaded successfully: {chosen_bg}")
                    except Exception as e:
                        print(f"[Main] ❌ Lỗi load video: {e}")
                        import traceback
                        traceback.print_exc()
                        video_bg = None
            
            # --- 4) Create and Run Game ---
            print(f"[Main] Creating game with video_bg: {video_bg is not None}")
            game = Game(music_file=music_file, video_background=video_bg)
            print(f"[Main] Game.video_background: {game.video_background is not None}")
            
            # Set image background nếu không phải video
            if chosen_bg and chosen_bg != "__CANCEL__" and not is_video_file(chosen_bg):
                try:
                    game.background = load_image(chosen_bg, (WIDTH, HEIGHT))
                except Exception:
                    pass

            game.run()  # Chạy game cho đến khi hết mạng hoặc QUIT
            
            # --- 5) Cleanup Video Background ---
            if video_bg:
                video_bg.release()  # Giải phóng OpenCV resources

            # --- 6) Restore Main Music ---
            # 🔊 Phát lại nhạc nền chính sau khi thoát gameplay
            pygame.mixer.music.unpause()

            # --- 7) Check Quit Request ---
            # Nếu người chơi đóng giữa chừng (X button)
            if getattr(game, "request_quit", False):
                running = False
                break

            # --- 8) Name Prompt & Save Score ---
            prompt = NamePrompt("Enter your name (Classic)")
            player_name = prompt.run(screen, background, default_if_empty="Player")
            
            # Kiểm tra xem người dùng có muốn thoát game không
            if player_name == "__QUIT__" or prompt.user_quit:
                running = False  # Thoát game
                break
            
            lb.add_classic(player_name, game.score)  # Lưu vào leaderboard
            
            # QUAN TRỌNG: Xóa TẤT CẢ events còn sót lại (đặc biệt là ESC)
            pygame.event.clear()
            
            # Reset flag should_quit của menu trước khi về menu
            menu.should_quit = False
            
            state = STATE_MENU  # Quay về menu

        # ============================================================
        # STATE: CHALLENGE - Challenge Mode (10 levels với mục tiêu kills)
        # ============================================================
        elif state == STATE_CHALLENGE:
            # --- 1) Load Progress Data ---
            # Progress chứa: unlocked_level (level cao nhất đã mở), stars (sao mỗi level)
            progress = load_progress()
            unlocked = progress.get("unlocked_level", 1)  # Mặc định unlock level 1
            stars_arr = progress.get("stars", [0] * 10)   # Mảng 10 số sao (0-3 mỗi level)

            # --- 2) Level Selection Screen ---
            selector = LevelSelect(unlocked, stars_arr)
            chosen = None
            while chosen is None:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        running = False
                        chosen = -1  # Đánh dấu QUIT
                    # Xử lý phím F12 để chụp màn hình level select
                    elif e.type == pygame.KEYDOWN and e.key == pygame.K_F12:
                        take_screenshot(screen)
                    else:
                        lv = selector.handle(e)  # Trả về level (1-10) hoặc -1 (ESC)
                        if lv is not None:
                            chosen = lv
                if not running:
                    break
                selector.draw(screen)
                pygame.display.flip()
                clock.tick(FPS)

            if not running:
                break
            if chosen == -1:  # ESC pressed
                # Xóa events tránh event leak
                pygame.event.clear()
                state = STATE_MENU
                continue

            # --- 3) Pause Main Music ---
            pygame.mixer.music.pause()

            # --- 4) Run Challenge Level ---
            # Challenge.run() trả về: (completed, stars, score, lives)
            # completed: True nếu đủ kills, False nếu hết mạng
            # stars: 0-3 sao dựa trên lives còn lại
            ch = Challenge(screen, background)
            completed, stars, score, lives = ch.run(chosen)

            # --- 5) Restore Main Music ---
            pygame.mixer.music.unpause()

            # --- 6) Name Prompt & Save Score ---
            prompt = NamePrompt(f"Enter your name (Challenge L{chosen})")
            player_name = prompt.run(screen, background, default_if_empty="Player")
            
            # Kiểm tra xem người dùng có muốn thoát game không
            if player_name == "__QUIT__" or prompt.user_quit:
                running = False
                break
            
            lb.add_challenge(player_name, chosen, lives if lives is not None else 0)

            # --- 7) Update Progress ---
            # Lưu số sao cao nhất cho level này
            if stars is None:
                stars = 0
            idx = chosen - 1
            stars_arr[idx] = max(int(stars_arr[idx]), int(stars))
            
            # Unlock level tiếp theo nếu hoàn thành và chưa unlock
            if completed and chosen >= unlocked and chosen < 10:
                unlocked = chosen + 1
            
            save_progress(unlocked, stars_arr)
            
            # QUAN TRỌNG: Xóa TẤT CẢ events còn sót lại (đặc biệt là ESC)
            pygame.event.clear()
            
            # Reset flag should_quit của menu trước khi về menu
            menu.should_quit = False
            
            state = STATE_MENU  # Quay về menu

        # ============================================================
        # STATE: LEADERBOARD - Bảng xếp hạng
        # ============================================================
        elif state == STATE_LEADERBOARD:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                result = lb.handle(e)  # Trả về "__EXIT__" khi ESC
                if result == "__EXIT__":
                    # Xóa events tránh event leak
                    pygame.event.clear()
                    state = STATE_MENU
            lb.draw(screen, background)
            pygame.display.flip()
            clock.tick(FPS)

    # ============================================================
    # CLEANUP - Dừng nhạc và thoát pygame
    # ============================================================
    pygame.mixer.music.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
