from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time

class MotorController:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)

    # ===== モード切替 =====
    def set_speed_mode(self):
        # Closed Loop Speed
        self.controller.send_command(cmds.SET_OPERATING_MODE, 1, 1)
        self.controller.send_command(cmds.SET_OPERATING_MODE, 2, 1)

    def set_torque_mode(self):
        # Closed Loop Torque
        self.controller.send_command(cmds.SET_OPERATING_MODE, 1, 3)
        self.controller.send_command(cmds.SET_OPERATING_MODE, 2, 3)

    # ===== 駆動 =====
    def drive_speed(self, rpm):
        self.controller.send_command(cmds.GO, 1, rpm)
        self.controller.send_command(cmds.GO, 2, rpm)

    def drive_torque(self, current):
        # current: mA（設定に依存）
        self.controller.send_command(cmds.TORQUE, 1, current)
        self.controller.send_command(cmds.TORQUE, 2, current)

    def stop(self):
        self.controller.send_command(cmds.GO, 1, 0)
        self.controller.send_command(cmds.GO, 2, 0)


if __name__ == "__main__":
    mc = MotorController()

    print("=== 速度制御で前進 ===")
    mc.set_speed_mode()
    mc.drive_speed(500)
    time.sleep(3)

    print("=== トルク制御へ切り替え ===")
    mc.stop()
    time.sleep(0.5)

    mc.set_torque_mode()
    mc.drive_torque(1500)  # 電流値を意図的に高めに
    time.sleep(3)

    print("=== 速度制御に復帰 ===")
    mc.stop()
    time.sleep(0.5)

    mc.set_speed_mode()
    mc.drive_speed(300)
    time.sleep(3)

    mc.stop()
