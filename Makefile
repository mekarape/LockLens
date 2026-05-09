run:
	@echo "Starting LockLens dashboard + recording..."
	@rm -f dashboard_recording.mp4
	@trap 'echo "Stopping..."; pkill -f "python3 src/main.py" 2>/dev/null || true; pkill -f "ffmpeg.*x11grab" 2>/dev/null || true; exit 0' INT TERM; \
	DISPLAY=:0 PYTHONPATH=/home/mekarape/LockLens python3 src/main.py & \
	sleep 3; \
	echo "Recording dashboard_recording.mp4..."; \
	DISPLAY=:0 ffmpeg -y -hide_banner -loglevel error \
		-f x11grab -draw_mouse 0 -framerate 30 -video_size 800x480 -i :0.0 \
		-c:v libx264 -pix_fmt yuv420p -preset ultrafast -crf 23 \
		dashboard_recording.mp4 & \
	wait

stop:
	@echo "Stopping LockLens..."
	@pkill -9 -f "python3 src/main.py" 2>/dev/null || true
	@pkill -9 -f "ffmpeg.*x11grab" 2>/dev/null || true
	@echo "Stopped."

.PHONY: run stop