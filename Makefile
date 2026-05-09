run:
	@echo "Starting LockLens dashboard + recording..."
	@rm -f dashboard_recording.mp4
	@DISPLAY=:0 PYTHONPATH=/home/mekarape/LockLens python3 src/main.py & \
	APP_PID=$$!; \
	echo $$APP_PID > .locklens_app.pid; \
	echo "Waiting for dashboard to draw..."; \
	sleep 3; \
	DISPLAY=:0 ffmpeg -y \
		-f x11grab -draw_mouse 0 -framerate 30 -video_size 800x480 -i :0.0 \
		-c:v libx264 -pix_fmt yuv420p -preset ultrafast -crf 23 \
		dashboard_recording.mp4 & \
	FFMPEG_PID=$$!; \
	echo $$FFMPEG_PID > .locklens_ffmpeg.pid; \
	wait $$APP_PID; \
	kill -INT $$FFMPEG_PID 2>/dev/null || true; \
	rm -f .locklens_app.pid .locklens_ffmpeg.pid; \
	echo "Recording saved to dashboard_recording.mp4"

stop:
	@echo "Stopping LockLens dashboard + recording..."
	@if [ -f .locklens_ffmpeg.pid ]; then kill -INT $$(cat .locklens_ffmpeg.pid) 2>/dev/null || true; fi
	@if [ -f .locklens_app.pid ]; then kill $$(cat .locklens_app.pid) 2>/dev/null || true; fi
	@pkill -f "python3 src/main.py" 2>/dev/null || true
	@pkill -f "ffmpeg.*x11grab" 2>/dev/null || true
	@rm -f .locklens_app.pid .locklens_ffmpeg.pid
	@echo "Stopped."

.PHONY: run stop