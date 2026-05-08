#!/bin/bash
# records the screen for dashboard overlay in demo video
# usage: ./record_dashboard.sh
# press Ctrl+C to stop recording

DISPLAY=:0
OUTPUT="dashboard_recording_$(date +%Y%m%d_%H%M%S).mp4"

echo "Recording dashboard to $OUTPUT"
echo "Press Ctrl+C to stop..."

ffmpeg -f x11grab -r 30 -s 800x480 -i :0.0 \
  -c:v libx264 -preset ultrafast -crf 23 \
  "$OUTPUT"

echo "Saved to $OUTPUT"