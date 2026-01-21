from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

class KeyboardSpeedControl:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)

        self.target_speed = 0.0   # m/s
        self.MAX_SPEED = 1.0      # m/s
        self.MAX_CMD = 1000       # Roboteq仕様

    def speed_ms_to_cmd(self, speed_ms):
        speed_ms = max(min(speed_ms, self.MAX_SPEED), -self.MAX_SPEED)
        return int(-speed_ms / self.MAX_SPEED * self.MAX_CMD)

    def update_target_speed(self):
        if keyboard.is_pressed("w"):
            self.target_speed = 0.1
        elif keyboard.is_pressed("s"):
            self.target_speed = -0.1
        else:
            self.target_speed = 0.0

    def run(self):
        try:
            while True:
                self.update_target_speed()
                cmd = self.speed_ms_to_cmd(self.target_speed)

                self.controller.send_command(cmds.DUAL_DRIVE, cmd, cmd)
                print(f"TARGET:{self.target_speed:+.2f} m/s → CMD:{cmd}")

                time.sleep(0.05)

        except KeyboardInterrupt:
            self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
            print("停止")

if __name__ == "__main__":
    KeyboardSpeedControl().run()
