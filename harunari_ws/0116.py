from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

class MotorController:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)  # 電子緊急停止解除

    def drive(self, speed_motor_one, speed_motor_two):
        self.controller.send_command(
            cmds.DUAL_DRIVE,
            speed_motor_one,
            speed_motor_two
        )

    def read_motor_speeds(self):
        speed_motor1 = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        speed_motor2 = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)
        return speed_motor1, speed_motor2

    def move_loop(self):
        if not self.connected:
            print("Controller not connected.")
            return

        RPM_THRESHOLD = 5   # 回転していないとみなす閾値
        stuck = False

        print("Press D to drive")
        print("Press S to stop")

        try:
            while self.connected:
                speed1, speed2 = self.read_motor_speeds()

                # None対策
                if speed1 is None or speed2 is None:
                    time.sleep(0.05)
                    continue

                # ===== 文字列 → 数値変換（重要）=====
                try:
                    speed1 = float(speed1)
                    speed2 = float(speed2)
                except (TypeError, ValueError):
                    time.sleep(0.05)
                    continue

                drive_speed_1 = 0
                drive_speed_2 = 0

                if keyboard.is_pressed('w'):
                    drive_speed_1 = -200
                    drive_speed_2 = -200

                    # ===== スタック判定 =====
                    if abs(speed1) < RPM_THRESHOLD and abs(speed2) < RPM_THRESHOLD:
                        if not stuck:
                            print("STUCK DETECTED")
                        stuck = True
                    else:
                        stuck = False

                if keyboard.is_pressed('s'):
                    drive_speed_1 = 0
                    drive_speed_2 = 0
                    stuck = False

                self.drive(drive_speed_1, drive_speed_2)

                time.sleep(0.05)  # 20Hz（通信・CPU負荷対策）

        except KeyboardInterrupt:
            self.drive(0, 0)
            print("Program terminated safely.")

if __name__ == "__main__":
    mc = MotorController()
    mc.move_loop()
