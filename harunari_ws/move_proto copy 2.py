from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

class RobotController:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
        self.connected = self.controller.connect(port)

        if not self.connected:
            raise ConnectionError("Roboteq に接続できませんでした")

        # 電子緊急停止を解除
        self.controller.send_command(cmds.REL_EM_STOP)
        print("Roboteq connected:", self.connected)

    def get_speed(self, channel=0):#モーター速度取得
        return self.controller.read_value(cmds.READ_BL_MOTOR_RPM, channel)

    def drive(self, left_speed, right_speed): #モーター駆動
        self.controller.send_command(cmds.DUAL_DRIVE, left_speed, right_speed)

    def get_drive_speeds(self):
        if keyboard.is_pressed('d'):
            print("D pressed (right)")
            return -200, -200

        elif keyboard.is_pressed('s'):
            print("S pressed (stop)")
            return 0, 0

        else:
            return 0, 0
            
if __name__ == "__main__":
    robot = RobotController(port="COM3")
    robot.run()