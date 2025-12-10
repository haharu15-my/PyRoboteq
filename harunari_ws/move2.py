from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time


class RobotController:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
        self.connected = self.controller.connect(port)

        if not self.connected:
            raise ConnectionError("Roboteq に接続できませんでした")

        # 電子緊急停止を解除
        self.controller.send_command(cmds.REL_EM_STOP)
        print("Roboteq connected:", self.connected)

    # --- モーター電流取得 ---
    def get_motor_current(self, channel=0):
        return self.controller.read_value(cmds.READ_MOTOR_AMPS, channel)

    # --- モーター駆動 ---
    def drive(self, left_speed, right_speed):
        self.controller.send_command(cmds.DUAL_DRIVE, left_speed, right_speed)

    # --- キー入力から速度計算 ---
    def get_drive_speeds(self):
        if keyboard.is_pressed('w'):
            print("W pressed (forward)")
            return -200, -200

        elif keyboard.is_pressed('s'):
            print("S pressed (backward)")
            return 200, 200

        elif keyboard.is_pressed('a'):
            print("A pressed (turn left)")
            return -200, 200

        elif keyboard.is_pressed('d'):
            print("D pressed (turn right)")
            return 200, -200

        else:
            return 0, 0

    # --- メイン制御ループ ---
    def run(self):
        try:
            while True:
                motor_amps = self.get_motor_current(0)
                print("Motor Amps:", motor_amps)

                left_speed, right_speed = self.get_drive_speeds()
                self.drive(left_speed, right_speed)

                time.sleep(0.02)  # 負荷軽減

        except KeyboardInterrupt:
            print("停止します。")
            self.drive(0, 0)


# --- 実行 ---
if __name__ == "__main__":
    robot = RobotController("COM3")
    robot.run()