from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time

class MotorController:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        if self.connected:
            print("Connected:", self.connected)
            self.controller.send_command(cmds.REL_EM_STOP)  # 緊急停止解除
        else:
            print("Controller not connected.")
        
        # スタック判定フラグ
        self.stuck = False

        # 閾値設定（必要に応じて調整）
        self.RPM_STUCK = 10      # これ以下で止まっているとみなす
        self.AMP_STUCK = 50      # これ以上でスタックと判定
        self.RPM_RECOVER = 30    # 回復とみなすRPM
        self.AMP_RECOVER = 40    # 回復とみなすAMP
    def parse_sensor_value(self, val):
        """Roboteqの文字列 'BS=-xxx' に対応して float に変換"""
        if isinstance(val, str) and '=' in val:
            val = val.split('=')[-1]
        try:
            return abs(float(val))
        except Exception:
            return 0.0
    
    def read_sensors(self):
        try:
            rpm1 = self.parse_sensor_value(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1))
            rpm2 = self.parse_sensor_value(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 2))
            amp1 = self.parse_sensor_value(self.controller.read_value(cmds.READ_MOTOR_AMPS, 1))
            amp2 = self.parse_sensor_value(self.controller.read_value(cmds.READ_MOTOR_AMPS, 2))
            return rpm1, rpm2, amp1, amp2
        except Exception as e:
            print("Sensor read error:", e)
            return 0.0, 0.0, 0.0, 0.0

    def check_stuck(self, rpm1, rpm2, amp1, amp2):
        # スタック判定
        if self.stuck:
            # 既にスタック中 → 回復条件を満たすまで保持
            if rpm1 > self.RPM_RECOVER and rpm2 > self.RPM_RECOVER and \
               amp1 < self.AMP_RECOVER and amp2 < self.AMP_RECOVER:
                self.stuck = False
                print("RECOVERED")
        else:
            # 新たにスタック判定
            if (rpm1 < self.RPM_STUCK or rpm2 < self.RPM_STUCK) and \
               (amp1 > self.AMP_STUCK or amp2 > self.AMP_STUCK):
                self.stuck = True
                print("STUCK DETECTED")

    def drive(self, speed_motor_one, speed_motor_two):
        self.controller.send_command(cmds.DUAL_DRIVE, speed_motor_one, speed_motor_two)

    def loop(self):
        print("Starting loop...")
        try:
            while True:
                rpm1, rpm2, amp1, amp2 = self.read_sensors()
                self.check_stuck(rpm1, rpm2, amp1, amp2)
                print(f"RPM1:{rpm1} RPM2:{rpm2} AMP1:{amp1} AMP2:{amp2} STUCK:{self.stuck}")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Program stopped by user.")
            self.drive(0,0)

if __name__ == "__main__":
    mc = MotorController("COM3")
    mc.loop()

