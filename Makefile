run:
	@echo "Starting LockLens..."
	@DISPLAY=:0 ffmpeg -f x11grab -r 30 -s 800x480 -i :0.0 \
		-c:v libx264 -preset ultrafast -crf 23 \
		dashboard_recording.mp4 & \
	DISPLAY=:0 PYTHONPATH=/home/mekarape/LockLens python3 src/main.py; \
	killall ffmpeg 2>/dev/null; \
	echo "Recording saved to dashboard_recording.mp4"

demo:
	@echo "Running motor demo..."
	@PYTHONPATH=/home/mekarape/LockLens python3 demo_movement.py

stop:
	@killall ffmpeg 2>/dev/null || true
	@echo "Stopped recording"

.PHONY: run demo stop