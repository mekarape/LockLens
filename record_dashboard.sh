#!/bin/bash
# records the screen for dashboard overlay in demo video
# usage: ./record_dashboard.sh
# press Ctrl+C to stop recording

OUTPUT="dashboard_recording_$(date +%Y%m%d_%H%M%S).mp4"

echo "Waiting 3 seconds for dashboard to draw..."
sleep 3

echo "Recording dashboard to $OUTPUT"
echo "Press Ctrl+C to stop..."

DISPLAY=:0 ffmpeg -y \
  -f x11grab -draw_mouse 0 -framerate 30 -video_size 800x480 -i :0.0 \
  -c:v libx264 -pix_fmt yuv420p -preset ultrafast -crf 23 \
  "$OUTPUT"

echo "Saved to $OUTPUT"