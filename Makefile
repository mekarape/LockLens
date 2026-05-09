run:
	@echo "Starting LockLens dashboard + recording..."
	@rm -f dashboard_recording.mp4
	@DISPLAY=:0 PYTHONPATH=/home/mekarape/LockLens python3 src/main.py > locklens.log 2>&1 & echo $$! > .locklens_app.pid
	@sleep 3
	@DISPLAY=:0 ffmpeg -y -hide_banner -loglevel error \
		-f x11grab -draw_mouse 0 -framerate 30 -video_size 800x480 -i :0.0 \
		-c:v libx264 -pix_fmt yuv420p -preset ultrafast -crf 23 \
		dashboard_recording.mp4 > ffmpeg.log 2>&1 & echo $$! > .locklens_ffmpeg.pid
	@echo "Running. To stop: make stop"

stop:
	@echo "Stopping LockLens..."
	@if [ -f .locklens_ffmpeg.pid ]; then kill -INT $$(cat .locklens_ffmpeg.pid) 2>/dev/null || true; fi
	@sleep 1
	@if [ -f .locklens_app.pid ]; then kill -TERM $$(cat .locklens_app.pid) 2>/dev/null || true; fi
	@sleep 1
	@pkill -9 -f "python3 src/main.py" 2>/dev/null || true
	@pkill -9 -f "ffmpeg.*x11grab" 2>/dev/null || true
	@rm -f .locklens_app.pid .locklens_ffmpeg.pid
	@echo "Stopped."

.PHONY: run stop