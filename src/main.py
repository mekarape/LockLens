from src.inference_client import get_target_location
from src.motor_control import Motors
from src.audio import play_searching, play_locked
from picamera2 import Picamera2
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tkinter as tk
import time
import threading
import io
import os

camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"size": (640, 480)}))
camera.start()
motors = Motors()

target = ""
running = False
latest_result = {"found": False}
frame_count = 0
total_cost = 0.0
latest_frame = None
frame_lock = threading.Lock()

def camera_loop():
    global latest_frame
    while True:
        frame = camera.capture_array()
        img = Image.fromarray(frame).convert("RGB")
        with frame_lock:
            latest_frame = img.copy()
        time.sleep(0.033)

def inference_loop():
    global target, running, latest_result, frame_count, total_cost
    while True:
        if not running or not target:
            time.sleep(0.1)
            continue

        with frame_lock:
            frame = latest_frame.copy() if latest_frame else None

        if frame is None:
            continue

        buf = io.BytesIO()
        frame.save(buf, format="JPEG")
        buf.seek(0)

        with open("current.jpg", "wb") as f:
            f.write(buf.read())

        start = time.time()
        results = get_target_location("current.jpg", target)
        latency = int((time.time() - start) * 1000)

        latest_result = results
        latest_result["latency"] = latency
        frame_count += 1
        total_cost += 0.001
        motors.track(results)

        time.sleep(0.3)

class LockLensApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LockLens")
        self.root.configure(bg="#0D1117")
        self.root.geometry("800x480")

        # Keep fullscreen, but DO NOT use overrideredirect(True).
        # overrideredirect breaks Entry keyboard focus on X11/Openbox.
        self.root.attributes("-fullscreen", True)

        self.root.bind("<Escape>", lambda e: self.stop_and_quit())

        self.pink = "#FF375F"
        self.navy = "#0D1117"
        self.card = "#161D2A"
        self.muted = "#3A4A60"
        self.white = "#FFFFFF"

        self.build_ui()
        self.root.after(500, self.focus_target_input)
        self.update_ui()

    def focus_target_input(self):
        self.root.lift()
        self.target_entry.focus_set()
        self.target_entry.icursor(tk.END)

    def build_ui(self):
        self.left = tk.Frame(self.root, bg=self.navy)
        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right = tk.Frame(self.root, bg=self.navy, width=240)
        self.right.pack(side=tk.RIGHT, fill=tk.Y)
        self.right.pack_propagate(False)

        self.canvas = tk.Canvas(self.left, bg="#111820", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        logo_frame = tk.Frame(self.right, bg=self.navy)
        logo_frame.pack(fill=tk.X, padx=14, pady=(14, 0))

        tk.Label(
            logo_frame,
            text="⬤",
            fg=self.pink,
            bg=self.navy,
            font=("Arial", 8),
        ).pack(side=tk.LEFT)

        tk.Label(
            logo_frame,
            text=" LockLens",
            fg=self.white,
            bg=self.navy,
            font=("Arial", 13, "bold"),
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="ready")
        self.status_label = tk.Label(
            self.right,
            textvariable=self.status_var,
            fg=self.pink,
            bg=self.card,
            font=("Arial", 9, "bold"),
            padx=10,
            pady=4,
        )
        self.status_label.pack(fill=tk.X, padx=14, pady=(8, 0))

        metrics = tk.Frame(self.right, bg=self.navy)
        metrics.pack(fill=tk.X, padx=14, pady=(8, 0))

        self.latency_var = tk.StringVar(value="--")
        self.conf_var = tk.StringVar(value="--")
        self.frames_var = tk.StringVar(value="0")
        self.cost_var = tk.StringVar(value="0.000")

        self.make_metric(metrics, "LATENCY", self.latency_var, 0, 0)
        self.make_metric(metrics, "CONFIDENCE", self.conf_var, 0, 1)
        self.make_metric(metrics, "FRAMES", self.frames_var, 1, 0)
        self.make_metric(metrics, "COST", self.cost_var, 1, 1)

        target_card = tk.Frame(self.right, bg=self.card)
        target_card.pack(fill=tk.X, padx=14, pady=(8, 0))

        tk.Label(
            target_card,
            text="TRACKING TARGET",
            fg=self.muted,
            bg=self.card,
            font=("Arial", 8),
        ).pack(anchor=tk.W, padx=8, pady=(6, 0))

        self.target_display = tk.Label(
            target_card,
            text='"--"',
            fg=self.white,
            bg=self.card,
            font=("Arial", 11),
        )
        self.target_display.pack(anchor=tk.W, padx=8)

        self.target_entry = tk.Entry(
            target_card,
            bg="#0D1117",
            fg=self.white,
            insertbackground=self.white,
            font=("Arial", 10),
            relief=tk.FLAT,
            takefocus=True,
            highlightthickness=1,
            highlightcolor=self.pink,
            highlightbackground=self.muted,
        )
        self.target_entry.pack(fill=tk.X, padx=8, pady=(4, 8))
        self.target_entry.insert(0, "describe target...")

        self.target_entry.bind("<Button-1>", self.on_target_click)
        self.target_entry.bind("<FocusIn>", self.on_target_click)
        self.target_entry.bind("<Return>", self.change_target)

        btn_frame = tk.Frame(self.right, bg=self.navy)
        btn_frame.pack(fill=tk.X, padx=14, pady=(8, 0))

        tk.Button(
            btn_frame,
            text="START",
            bg=self.pink,
            fg=self.white,
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=0,
            pady=10,
            command=self.start_tracking,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        tk.Button(
            btn_frame,
            text="STOP",
            bg=self.card,
            fg=self.pink,
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=0,
            pady=10,
            command=self.stop_tracking,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            self.right,
            text="AMD MI300X · ROCm 7.2 · vLLM",
            fg=self.muted,
            bg=self.navy,
            font=("Arial", 8),
        ).pack(side=tk.BOTTOM, pady=8)

    def on_target_click(self, event=None):
        if self.target_entry.get() == "describe target...":
            self.target_entry.delete(0, tk.END)
        self.target_entry.focus_set()
        self.target_entry.icursor(tk.END)

    def make_metric(self, parent, label, var, row, col):
        frame = tk.Frame(parent, bg=self.card)
        frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        tk.Label(
            frame,
            text=label,
            fg=self.muted,
            bg=self.card,
            font=("Arial", 8),
        ).pack(anchor=tk.W, padx=8, pady=(6, 0))

        tk.Label(
            frame,
            textvariable=var,
            fg=self.pink,
            bg=self.card,
            font=("Courier", 16, "bold"),
        ).pack(anchor=tk.W, padx=8, pady=(0, 6))

    def change_target(self, event=None):
        global target, running

        val = self.target_entry.get().strip()

        if val and val != "describe target...":
            target = val
            running = True
            self.target_display.config(text=f'"{val}"')
            self.target_entry.delete(0, tk.END)
            self.status_var.set("tracking")
            self.focus_target_input()

    def start_tracking(self):
        global running
        running = True
        self.status_var.set("tracking")
        self.focus_target_input()

    def stop_tracking(self):
        global running
        running = False
        motors.stop()
        self.status_var.set("stopped")
        self.focus_target_input()

    def stop_and_quit(self):
        global running
        running = False
        motors.stop()
        motors.close()
        camera.stop()
        self.root.destroy()

    def update_ui(self):
        with frame_lock:
            frame = latest_frame.copy() if latest_frame else None

        if frame:
            w = self.canvas.winfo_width() or 480
            h = self.canvas.winfo_height() or 480
            frame = frame.resize((w, h))

            if latest_result.get("found"):
                draw = ImageDraw.Draw(frame)
                cx = latest_result.get("cx", 0.5) * w
                cy = latest_result.get("cy", 0.5) * h
                bw = latest_result.get("w", 0.2) * w
                bh = latest_result.get("h", 0.3) * h

                x1 = cx - bw / 2
                y1 = cy - bh / 2
                x2 = cx + bw / 2
                y2 = cy + bh / 2

                draw.rectangle([x1, y1, x2, y2], outline="#FF375F", width=2)

                conf = int(latest_result.get("confidence", 0) * 100)
                draw.text((x1, y1 - 18), f"{target} · {conf}%", fill="#FF375F")

            photo = ImageTk.PhotoImage(frame)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas.image = photo

        if latest_result.get("latency"):
            self.latency_var.set(str(latest_result["latency"]))

        if latest_result.get("confidence"):
            self.conf_var.set(str(int(latest_result["confidence"] * 100)))

        self.frames_var.set(str(frame_count))
        self.cost_var.set(f"${total_cost:.3f}")

        status = self.status_var.get()
        colors = {
            "tracking": "#FF375F",
            "searching": "#BF9FFF",
            "stopped": "#9FE0FF",
            "ready": "#BDC8E0",
        }
        self.status_label.config(fg=colors.get(status, "#BDC8E0"))

        self.root.after(100, self.update_ui)

if __name__ == "__main__":
    camera_thread = threading.Thread(target=camera_loop, daemon=True)
    camera_thread.start()

    inference_thread = threading.Thread(target=inference_loop, daemon=True)
    inference_thread.start()

    root = tk.Tk()
    app = LockLensApp(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        running = False

        try:
            motors.stop()
            motors.close()
        except Exception:
            pass

        try:
            camera.stop()
        except Exception:
            pass

        print("LockLens stopped")