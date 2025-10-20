import sys
import os
import pygame

# Fix for PyInstaller: support both relative and absolute imports
try:
    from .settings import WIDTH, HEIGHT, STATE_MENU, STATE_CLASSIC, STATE_CHALLENGE, STATE_LEADERBOARD, FPS, VSYNC, IMAGE_DIR, SOUND_DIR
    from .utils import load_image, load_progress, save_progress
    from .game import Game
    from .menu import MainMenu
    from .leaderboard import Leaderboard
    from .challenge import Challenge
    from .level_select import LevelSelect
    from .name_prompt import NamePrompt
except ImportError:
    # Running as standalone executable
    from settings import WIDTH, HEIGHT, STATE_MENU, STATE_CLASSIC, STATE_CHALLENGE, STATE_LEADERBOARD, FPS, VSYNC, IMAGE_DIR, SOUND_DIR
    from utils import load_image, load_progress, save_progress
    from game import Game
    from menu import MainMenu
    from leaderboard import Leaderboard
    from challenge import Challenge
    from level_select import LevelSelect
    from name_prompt import NamePrompt


def main():
    pygame.init()
    pygame.mixer.init()

    # --- Phát nhạc nền chính ---
    try:
        music_path = str(SOUND_DIR / "nhacnen.mp3")
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print("Không thể tải hoặc phát nhạc nền:", e)

    # Tạo display với hardware acceleration và vsync nếu có
    flags = pygame.HWSURFACE | pygame.DOUBLEBUF
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=1 if VSYNC else 0)
    pygame.display.set_caption("Space Typing Game")

    try:
        background = load_image("background.jpg", (WIDTH, HEIGHT))
    except Exception:
        background = None

    lb = Leaderboard()
    state = STATE_MENU

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

    running = True
    clock = pygame.time.Clock()

    while running:
        if state == STATE_MENU:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                else:
                    menu.handle(e)
            menu.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)

        elif state == STATE_CLASSIC:
            try:
                from .utils import list_background_files, get_music_for_background, is_video_file
                from .background_select import BackgroundSelect
                from .video_background import VideoBackground
            except ImportError:
                from utils import list_background_files, get_music_for_background, is_video_file
                from background_select import BackgroundSelect
                from video_background import VideoBackground

            bg_files = list_background_files()
            chosen_bg = None

            if bg_files:
                selector = BackgroundSelect(bg_files)
                while chosen_bg is None and running:
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT:
                            running = False
                            chosen_bg = "__CANCEL__"
                            break
                        res = selector.handle(e)
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
                    state = STATE_MENU
                    continue

            # 🔇 Tạm dừng nhạc nền khi vào gameplay
            pygame.mixer.music.pause()

            # 🎵 Lấy nhạc tương ứng với background
            music_file = get_music_for_background(chosen_bg) if chosen_bg and chosen_bg != "__CANCEL__" else None

            # Set background - hỗ trợ cả video và image
            video_bg = None
            print(f"[Main] Chosen background: {chosen_bg}")
            print(f"[Main] Is video file: {is_video_file(chosen_bg) if chosen_bg else False}")
            
            if chosen_bg and chosen_bg != "__CANCEL__":
                if is_video_file(chosen_bg):
                    # Tạo video background
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
            
            # --- Khởi tạo game với nhạc và video background ---
            print(f"[Main] Creating game with video_bg: {video_bg is not None}")
            game = Game(music_file=music_file, video_background=video_bg)
            print(f"[Main] Game.video_background: {game.video_background is not None}")
            
            # Set image background nếu không phải video
            if chosen_bg and chosen_bg != "__CANCEL__" and not is_video_file(chosen_bg):
                try:
                    game.background = load_image(chosen_bg, (WIDTH, HEIGHT))
                except Exception:
                    pass

            game.run()  # chạy game
            
            # Cleanup video background
            if video_bg:
                video_bg.release()

            # 🔊 Phát lại nhạc nền chính sau khi thoát gameplay
            pygame.mixer.music.unpause()

            # Nếu người chơi đóng giữa chừng
            if getattr(game, "request_quit", False):
                running = False
                break

            # --- Nhập tên người chơi ---
            prompt = NamePrompt("Enter your name (Classic)")
            player_name = prompt.run(screen, background, default_if_empty="Player")
            lb.add_classic(player_name, game.score)
            state = STATE_MENU

        elif state == STATE_CHALLENGE:
            progress = load_progress()
            unlocked = progress.get("unlocked_level", 1)
            stars_arr = progress.get("stars", [0] * 10)

            selector = LevelSelect(unlocked, stars_arr)
            chosen = None
            while chosen is None:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        running = False
                        chosen = -1
                    lv = selector.handle(e)
                    if lv is not None:
                        chosen = lv
                if not running:
                    break
                selector.draw(screen)
                pygame.display.flip()
                clock.tick(FPS)

            if not running:
                break
            if chosen == -1:
                state = STATE_MENU
                continue

            pygame.mixer.music.pause()

            ch = Challenge(screen, background)
            completed, stars, score, lives = ch.run(chosen)

            pygame.mixer.music.unpause()

            prompt = NamePrompt(f"Enter your name (Challenge L{chosen})")
            player_name = prompt.run(screen, background, default_if_empty="Player")
            lb.add_challenge(player_name, chosen, lives if lives is not None else 0)

            if stars is None:
                stars = 0
            idx = chosen - 1
            stars_arr[idx] = max(int(stars_arr[idx]), int(stars))
            if completed and chosen >= unlocked and chosen < 10:
                unlocked = chosen + 1
            save_progress(unlocked, stars_arr)
            state = STATE_MENU

        elif state == STATE_LEADERBOARD:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                result = lb.handle(e)
                if result == "__EXIT__":
                    state = STATE_MENU
            lb.draw(screen, background)
            pygame.display.flip()
            clock.tick(FPS)

    pygame.mixer.music.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
