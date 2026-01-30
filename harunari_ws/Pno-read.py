from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time
import math

class KeyboardOpenLoopControl:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)

        # ===== パラメータ =====
        self.WHEEL_RADIUS = 0.13   # 車輪半径[m]
        self.GEAR_RATIO = 25
        self.dt = 0.05

        self.target_speed = 0.0

    def read_actual_speed(self):
        raw = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)

        if isinstance(raw, str) and '=' in raw:
            motor_rpm = float(raw.split('=')[-1])
        else:
            motor_rpm = float(raw)

        motor_rpm = -motor_rpm
        wheel_rpm = motor_rpm / self.GEAR_RATIO
        speed = (2 * math.pi * self.WHEEL_RADIUS * wheel_rpm) / 60.0
        return speed

    def update_target(self):
        if keyboard.is_pressed("w"):
            self.target_speed = 0.13
        elif keyboard.is_pressed("s"):
            self.target_speed = -0.2
        else:
            self.target_speed = 0.0

    def run(self):
        try:
            while True:
                self.update_target()
                act = self.read_actual_speed()
                motor_amps = self.controller.read_value(cmds.READ_MOTOR_AMPS, 0)

                # ---- Open Loop（P制御なし）----
                cmd_speed = self.target_speed

                # m/s → Roboteq CMD（経験的スケーリング）
                cmd = int(-cmd_speed * 1000)

                # 飽和
                cmd = max(min(cmd, 1000), -1000)

                self.controller.send_command(cmds.DUAL_DRIVE, cmd, cmd)

                print(
                    f"TARGET:{self.target_speed:+.2f} "
                    f"ACT:{act:+.2f} "
                    f"CMD:{cmd} "
                    f"AMPS:{motor_amps}"
                )

                time.sleep(self.dt)

        except KeyboardInterrupt:
            self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
            print("制御停止")

if __name__ == "__main__":
    KeyboardOpenLoopControl().run()
