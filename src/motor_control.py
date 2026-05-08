import time
import serial
import pyvesc
from pyvesc.VESC.messages import SetRPM
from src.audio import play_searching

class Motors:
    # left motor on UART, right motor on CAN bus (slave ID 88)
    # left_multiplier and right_multiplier set for correct forward direction
    # kp and base_speed are tunable variables
    def __init__(
        self,
        port="/dev/ttyAMA0",
        baud=115200,
        slave_can_id=88,
        max_rpm=4000,
        left_multiplier=1,
        right_multiplier=-1,
        kp=0.4,
        base_speed=0.45,
        search_speed=0.2,
    ):
        self.port = port
        self.baud = baud
        self.slave_can_id = slave_can_id
        self.max_rpm = int(max_rpm)
        self.left_multiplier = int(left_multiplier)
        self.right_multiplier = int(right_multiplier)
        self.kp = kp
        self.base_speed = base_speed
        self.search_speed = search_speed
        self.ser = serial.Serial(self.port, self.baud, timeout=0.1)
        self.last_cx = 0.18

    # proportional control converts target position to motor speeds
    # error > 0 --> target is right of center, correction turns wagon right
    # error < 0 --> target is left of center, correction turns wagon left
    def track(self, result):
        print(f"track called: found={result.get('found')}, confidence={result.get('confidence', 0):.2f}, cx={result.get('cx', 'N/A')}")

        if not result["found"]:
            self.search()
            return

        cx = result["cx"]
        self.last_cx = cx
        # camera offset calibrated to 0.18
        error = cx - 0.18
        # deadband — ignore small errors to reduce jitter
        if abs(error) < 0.08:
            error = 0
        correction = error * self.kp

        # maintain ~2 foot standoff using bbox height as distance proxy
        bh = result.get("h", 0)
        if bh > 0.6:
            self.stop()
            return

        left_speed = self.base_speed + correction
        right_speed = self.base_speed - correction
        left_rpm = int(left_speed * self.max_rpm * self.left_multiplier)
        right_rpm = int(right_speed * self.max_rpm * self.right_multiplier)
        self._send(SetRPM(left_rpm))
        self._send(SetRPM(right_rpm, can_id=self.slave_can_id))

    # called when target is lost or confidence drops below threshold
    # rotate toward last known target
    # rotates then returns to let main loop recheck for target
    def search(self):
        play_searching()
        if self.last_cx >= 0.18:
            left_rpm = int(self.search_speed * self.max_rpm * self.left_multiplier)
            right_rpm = int(-self.search_speed * self.max_rpm * self.right_multiplier)
        else:
            left_rpm = int(-self.search_speed * self.max_rpm * self.left_multiplier)
            right_rpm = int(self.search_speed * self.max_rpm * self.right_multiplier)
        self._send(SetRPM(left_rpm))
        self._send(SetRPM(right_rpm, can_id=self.slave_can_id))
        time.sleep(0.3)

    # zero out both motors
    def stop(self):
        self._send(SetRPM(0))
        self._send(SetRPM(0, can_id=self.slave_can_id))

    # send helper functions to VESC via UART/CAN bus
    def _send(self, msg):
        packet = pyvesc.encode(msg)
        self.ser.write(packet)
        self.ser.flush()

    # stop motors
    # close serial connection
    def close(self):
        try:
            self.stop()
            time.sleep(0.05)
        finally:
            self.ser.close()

    def set_speed(self, left_speed, right_speed):
        # set motor speeds directly in range -1.0 to 1.0
        left_rpm = int(left_speed * self.max_rpm * self.left_multiplier)
        right_rpm = int(right_speed * self.max_rpm * self.right_multiplier)
        self._send(SetRPM(left_rpm))
        self._send(SetRPM(right_rpm, can_id=self.slave_can_id))