# assets/images/tools/extract_frames.py
import os, cv2
from pathlib import Path

# BASE = thư mục 'assets' (tự suy ra từ vị trí script)
ASSETS_DIR = Path(__file__).resolve().parents[2]   # .../assets
BG_DIR     = ASSETS_DIR / "images" / "backgrounds"

VIDEO  = BG_DIR / "background6.mp4"
OUTDIR = BG_DIR / "background6_frames"

FPS_OUT = 24
W, H = 1280, 720   # đổi theo WIDTH, HEIGHT của game

OUTDIR.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(str(VIDEO))
if not cap.isOpened():
    raise SystemExit(f"Không mở được file: {VIDEO.resolve()}")

orig_fps = cap.get(cv2.CAP_PROP_FPS) or 30
step = max(1, int(round(orig_fps / FPS_OUT)))

i = saved = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    if i % step == 0:
        frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(OUTDIR / f"{saved+1:04d}.png"), frame)
        saved += 1
    i += 1
cap.release()
print(f"Đã xuất {saved} ảnh PNG vào {OUTDIR.resolve()}")
