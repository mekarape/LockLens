run:
	@echo "Starting LockLens dashboard..."
	@rm -f dashboard_recording.mp4
	@DISPLAY=:0 PYTHONPATH=/home/mekarape/LockLens python3 src/main.py & \
	APP_PID=$$!; \
	echo "Waiting for dashboard to draw..."; \
	sleep 3; \
	echo "Starting recording..."; \
	DISPLAY=:0 ffmpeg -y \
		-f x11grab -draw_mouse 0 -framerate 30 -video_size 800x480 -i :0.0 \
		-c:v libx264 -pix_fmt yuv420p -preset ultrafast -crf 23 \
		dashboard_recording.mp4 & \
	FFMPEG_PID=$$!; \
	wait $$APP_PID; \
	kill -INT $$FFMPEG_PID 2>/dev/null || true; \
	wait $$FFMPEG_PID 2>/dev/null || true; \
	echo "Recording saved to dashboard_recording.mp4"

stop:
	@killall ffmpeg 2>/dev/null || true
	@echo "Stopped recording"

.PHONY: run stop