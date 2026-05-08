from src.motor_control import Motors
import time

print("Testing motors...")
motors = Motors()

print("Forward 2 seconds")
motors._send_rpm(800, 800)
time.sleep(2)

print("Stop")
motors.stop()
time.sleep(1)

print("Turn right 2 seconds")
motors._send_rpm(800, -800)
time.sleep(2)

print("Stop")
motors.stop()
motors.close()
print("Done")