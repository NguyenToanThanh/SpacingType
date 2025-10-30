# src/video_background.py
import pygame
import cv2
import numpy as np
from pathlib import Path

class VideoBackground:
    """Class để phát video làm background động"""
    
    def __init__(self, video_path: str, size: tuple[int, int], loop: bool = True):
        """
        Khởi tạo video background
        
        Args:
            video_path: Đường dẫn đến file video
            size: (width, height) của màn hình
            loop: Lặp lại video hay không
        """
        self.video_path = Path(video_path)
        self.size = size
        self.loop = loop
        
        # Mở video
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise FileNotFoundError(f"Không thể mở video: {video_path}")
        
        # Lấy thông tin video
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.ms_per_frame = 1000 / self.fps
        
        # Tracking
        self._time_accumulator = 0
        self.current_frame = None
        self.is_playing = True
        
        # Load frame đầu tiên
        self._load_next_frame()
        
        print(f"[VideoBackground] Loaded: {self.video_path.name}")
        print(f"[VideoBackground] FPS: {self.fps}, Frames: {self.total_frames}")
    
    def _load_next_frame(self):
        """Load frame tiếp theo từ video"""
        ret, frame = self.cap.read()
        
        if not ret:
            if self.loop:
                # Quay lại đầu video
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
            else:
                self.is_playing = False
                return
        
        if ret and frame is not None:
            # Chuyển đổi từ BGR (OpenCV) sang RGB (Pygame)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize về kích thước màn hình
            frame = cv2.resize(frame, self.size, interpolation=cv2.INTER_LINEAR)
            
            # Chuyển sang Pygame surface
            # NumPy array shape: (height, width, channels)
            # Pygame surfarray expects: (width, height, channels)
            # Nên ta cần transpose
            frame = np.transpose(frame, (1, 0, 2))  # (H, W, C) -> (W, H, C)
            
            self.current_frame = pygame.surfarray.make_surface(frame)
    
    def update(self, dt_ms: int):
        """
        Cập nhật video background
        
        Args:
            dt_ms: Delta time in milliseconds
        """
        if not self.is_playing:
            return
        
        self._time_accumulator += dt_ms
        
        # Load frame mới khi đủ thời gian
        while self._time_accumulator >= self.ms_per_frame:
            self._load_next_frame()
            self._time_accumulator -= self.ms_per_frame
    
    def draw(self, surface: pygame.Surface):
        """Vẽ frame hiện tại lên surface"""
        if self.current_frame:
            surface.blit(self.current_frame, (0, 0))
    
    def reset(self):
        """Reset video về đầu"""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self._time_accumulator = 0
        self._load_next_frame()
        self.is_playing = True
    
    def release(self):
        """Giải phóng resources"""
        if self.cap:
            self.cap.release()
            print(f"[VideoBackground] Released: {self.video_path.name}")
    
    def __del__(self):
        """Destructor - tự động release khi object bị xóa"""
        self.release()
