from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time
import math

class KeyboardPControl:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)

        # ===== パラメータ =====
        self.Kp = 0.5 # P制御ゲイン
        self.WHEEL_RADIUS = 0.13 # 車輪半径[m]
        self.GEAR_RATIO = 25 # ギア比
        self.dt = 0.05 # 制御周期[s]

        self.target_speed = 0.0

    def read_actual_speed(self):
        raw = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)

        if isinstance(raw, str) and '=' in raw:
            motor_rpm = float(raw.split('=')[-1])
        else:
            motor_rpm = float(raw)

        motor_rpm = -motor_rpm  # 前進符号合わせ
        wheel_rpm = motor_rpm / self.GEAR_RATIO
        speed = (2 * math.pi * self.WHEEL_RADIUS * wheel_rpm) / 60.0
        return speed

    def update_target(self):
        if keyboard.is_pressed("w"):
            self.target_speed = 0.1
        elif keyboard.is_pressed("s"):
            self.target_speed = -0.2
        else:
            self.target_speed = 0.0

    def run(self):
        try:
            while True:
                self.update_target()
                act = self.read_actual_speed()
                err = self.target_speed - act
                motor_amps = self.controller.read_value(cmds.READ_MOTOR_AMPS, 0)

                # ---- P制御 ----
                cmd_speed = self.target_speed + self.Kp * err

                # m/s → Roboteq CMD
                cmd = int(-cmd_speed * 1000)

                # 飽和
                cmd = max(min(cmd, 1000), -1000)

                self.controller.send_command(cmds.DUAL_DRIVE, cmd, cmd)

                print(
                    f"TARGET:{self.target_speed:+.2f} "
                    f"ACT:{act:+.2f} "
                    f"ERR:{err:+.2f} "
                    f"CMD:{cmd}"
                    f" AMPS:{motor_amps}"
                )

                time.sleep(self.dt)

        except KeyboardInterrupt:
            self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
            print("制御停止")

if __name__ == "__main__":
    KeyboardPControl().run()