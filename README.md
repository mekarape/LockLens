# LockLens

**AI vision tracking for any Linux-based robot. Specify a target in plain English. LockLens locks on and follows. No markers. No setup.**

Built for the AMD Developer Hackathon 2026, Track 3: Launch and Fund Your Startup.

---

## The Problem

Following robots have been stuck with April tags and fiducial markers for years. You print a tag, tape it to something, and hope it stays in frame. The moment the tag is occluded or removed, tracking fails completely. There is no way to ensure a consistent experience across different environments and targets. The system is rigid, fragile, and requires physical setup every time.

LockLens replaces all of that with open-vocabulary AI vision running on AMD hardware.

---

## What It Is

LockLens is a pay-per-inference AI vision platform that enables any Linux-based robot to follow a target specified in plain English. A user types a target description on a touchscreen and the system locks on, follows in real time, and carries your belongings with it. No physical markers required.

The reference implementation runs on a custom hoverboard conversion platform with 8.5 inch hub motors, Flipsky VESC motor controllers, and a Raspberry Pi 4B. The same software stack is designed to deploy on any Linux device with a camera and a serial port.

---

## Hardware Stack

### Drive Platform
- Hoverboard chassis with 8.5 inch brushless hub motors
- Custom plywood deck with swivel casters
- Mounted milk crate cargo bed for carrying belongings
- 36V lithium battery pack (stock hoverboard battery) with onboard charging circuit
- Emergency stop button wired into power distribution

### Motor Control
- 2x Flipsky VESC motor controllers
- Master/slave configuration over CAN bus
- UART communication from Raspberry Pi 4B to master VESC
- CAN bus forwards commands from master to slave automatically
- Custom power distribution block tapping 36V battery

### Computing and Sensing
- Raspberry Pi 4B (main compute)
- Raspberry Pi Camera Module 3, 12MP IMX708, autofocus, CSI ribbon cable
- 5 inch DSI touchscreen for live dashboard

### Audio and Lighting
- ZX 4 ohm 5W speaker
- Adafruit 20W stereo Class D amplifier (MAX9744)
- Buck converter stepping 36V down to 12V powering the audio amplifier
- 1ft 12V LED underglow strip powered by a dedicated buck converter tapped off the main 36V battery

### Power Distribution
- 36V main battery feeds motor controllers directly
- Buck converter (36V to 12V) powers audio amplifier
- Buck converter (36V to 12V) powers LED underglow strip
- Raspberry Pi powered via dedicated USB-C buck converter (36V to 5V)
- All grounds common through power distribution block

### Custom Hardware
- Custom PCB ADC (MCP3008 based) designed and soldered for analog sensor integration

---

## Software Stack

| Layer | Technology |
|---|---|
| Vision inference | Qwen2.5-VL-7B-Instruct |
| Inference server | vLLM 0.17.1 on ROCm 7.2 |
| GPU | AMD MI300X (192GB VRAM) via AMD Developer Cloud |
| Camera | Picamera2 |
| Motor control | pyvesc over UART/CAN |
| Dashboard | Tkinter native desktop UI |
| Audio | pygame.mixer |
| Billing | X402 micropayment per inference call |
| Language | Python 3.13 |

---

## How It Works

```
CSI Camera (Raspberry Pi 4B)
        | JPEG frame captured every cycle via camera thread
inference_client.py
        | base64 encoded frame + plain English target prompt
        | HTTP POST to AMD Developer Cloud
Qwen2.5-VL on AMD MI300X GPU
        | returns {found, cx, cy, w, h, confidence}
motor_control.py proportional controller
        | rolling average smoothing over last 6 frames
        | error = smooth_cx - 0.18 (camera offset calibrated)
        | left_rpm = base + correction
        | right_rpm = base - correction
        | UART to master Flipsky VESC
        | CAN bus to slave Flipsky VESC
Hub motors drive wagon toward target
        |
Tkinter dashboard updates every 100ms
        | live: status, latency, confidence, cost, bounding box overlay
X402 meters each inference call
```

### Search and Re-acquisition

When the target is lost the wagon stops and waits for the next inference cycle to reacquire. Target re-acquisition with directional search and audio feedback is planned for a future release.

### Target Switching

The user can type a new target in plain English at any time via the touchscreen dashboard. The system immediately sends the new prompt with the next frame with no restart required.

### Camera Offset Calibration

The camera is physically offset from the wagon center. The center reference point is calibrated to cx 0.18 instead of 0.5 to compensate. A wide deadband of 0.25 prevents corrections for small positional noise.

---

## Architecture

```
locklens/
    src/
        inference_client.py   camera frame encoding, AMD HTTP, response parsing
        motor_control.py      PID controller, VESC UART/CAN, search behavior
        audio.py              lock-on sound playback
        main.py               orchestrator, camera thread, inference thread, Tkinter UI
    sounds/
        locked.wav            plays on target acquisition
    Makefile                  single command to run and record
    requirements.txt
    .env                      AMD endpoint (not committed)
```

---

## Setup

### Requirements

```bash
pip install -r requirements.txt --break-system-packages
```

### Environment

Create a `.env` file in the project root:

```
AMD_ENDPOINT=http://YOUR_AMD_INSTANCE_IP:8000/v1/chat/completions
```

### AMD Developer Cloud

1. Sign up for the AMD AI Developer Program at developer.amd.com
2. Claim $100 in GPU credits
3. Spin up an MI300X instance with the vLLM 0.17.1 image
4. SSH in, enter the Docker container, and start the inference server:

```bash
ssh root@YOUR_AMD_IP
docker exec -it rocm /bin/bash
vllm serve Qwen/Qwen2.5-VL-7B-Instruct --host 0.0.0.0 --port 8000
```

5. Open port 8000 on the firewall in a second terminal:

```bash
ssh root@YOUR_AMD_IP
ufw allow 8000
```

### Running LockLens

```bash
make run
```

This starts the screen recorder and LockLens simultaneously. Press Ctrl+C to stop. The dashboard recording is saved to `dashboard_recording.mp4`.

Or run manually:

```bash
DISPLAY=:0 PYTHONPATH=/home/mekarape/LockLens python3 src/main.py
```

Type a target description in the input field and press Enter to begin tracking.

---

## Tuning

| Parameter | Default | Description |
|---|---|---|
| `kp` | 0.08 | Proportional gain, increase for faster response, decrease if oscillating |
| `base_speed` | 0.35 | Forward tracking speed (0.0 to 1.0) |
| `search_speed` | 0.15 | Rotation speed during target search |
| `max_rpm` | 4000 | Maximum motor RPM |
| `cx_history_size` | 6 | Number of frames to average for smooth tracking |
| Camera center offset | 0.18 | Calibrate to your camera position |
| Standoff threshold | 0.6 | Bbox height at which wagon stops to maintain distance |

---

## Business Model

LockLens charges per inference call via X402 micropayments. Each frame processed costs a fraction of a cent. There is no subscription, no upfront cost, and no charge when the robot is idle. This model scales directly with usage. A warehouse robot running 8 hours a day at 10fps generates predictable, metered revenue.

Target customers: robotics startups, university labs, warehouse automation teams, and hobbyist builders who need AI vision without ML engineering overhead.

---

## Roadmap

- VL53L0X ToF sensor integration for collision avoidance (hardware already on platform)
- Voice target input via Whisper on AMD GPU
- Multi-camera support
- Edge inference mode for low-latency offline operation
- REST API for third-party robot integration
- Web dashboard for fleet management
- Directional search rotation when target is lost
- Audio lock-on confirmation tone

---

## Built With

- AMD Developer Cloud, MI300X GPU infrastructure
- Qwen2.5-VL, Alibaba open-source vision-language model
- vLLM, high-throughput inference serving on ROCm
- X402, micropayment protocol for per-inference billing
- lablab.ai, AMD Developer Hackathon platform

---

## License

MIT. See LICENSE file.

---

*Built solo for the AMD Developer Hackathon, May 2026.*