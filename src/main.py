from src.inference_client import get_target_location
from src.motor_control import Motors
from src.audio import play_searching, play_locked
from picamera2 import Picamera2
import asyncio
import websockets
import json
import time
import threading
import subprocess

# initialize hardware and shared state
camera = Picamera2()
camera.configure(camera.create_preview_configuration())
camera.start()
motors = Motors()

# shared state between main loop and websocket handler
# target is plain english description of what to follow
target = ""
running = False

# runs continuously in a background thread
# captures frames and sends to AMD cloud for inference
# passes results to motor controller every cycle
def main_loop():
    while True:
        # idle until user sets a target and hits start
        if not running or not target:
            time.sleep(0.1)
            continue
        image_path = "current.jpg"
        camera.capture_file(image_path)
        results = get_target_location(image_path, target)
        motors.track(results)

# handles incoming websocket messages from dashboard.html
# commands: start, stop, target:<new target>
async def handler(websocket, path):
    global target, running
    async for message in websocket:
        data = json.loads(message)
        command = data.get("command", "")
        if command == "start":
            running = True
        # stop motors immediately and pause inference loop
        elif command == "stop":
            running = False
            motors.stop()
        # update target and resume tracking immediately
        elif command.startswith("target:"):
            target = command.replace("target:", "").strip()
            running = True

if __name__ == "__main__":
    # launch dashboard in fullscreen kiosk mode
    subprocess.Popen([
        "chromium-browser",
        "--kiosk",
        "--no-sandbox",
        "file:///home/mekarape/LockLens/dashboard.html"
    ])

    # start tracking loop in background thread so it doesn't block websocket
    loop_thread = threading.Thread(target=main_loop, daemon=True)
    loop_thread.start()

    # start websocket server on localhost port 8765
    start_server = websockets.serve(handler, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)

    try:
        # run forever until Ctrl+C
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        # clean shutdown — stop motors before closing
        motors.stop()
        motors.close()
        camera.stop()
        print("LockLens stopped")