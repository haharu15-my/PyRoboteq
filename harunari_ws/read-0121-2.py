from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time
import math

class KeyboardPIControl:
    def __init__(self, port="COM3"):
        # モータ接続
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)  # 緊急停止解除

        # PI制御パラメータ
        self.Kp = 0.5
        self.Ki = 0.2
        self.I = 0.0
        self.I_max = 50
        self.I_min = -50

        # 速度制御
        self.target_speed = 0.0      # 目標速度
        self.actual_speed = 0.0      # 実際はモータから取得
        self.cmd = 0                 # 指令値
        self.WHEEL_RADIUS = 0.13     # タイヤの半径[m]
        self.GEAR_RATIO = 25         # ギヤ比

    def motor_rpm_to_speed_ms(self, motor_rpm): # モータRPM → 実速度[m/s]3
        wheel_rpm = motor_rpm / self.GEAR_RATIO
        return (2.0 * math.pi * self.WHEEL_RADIUS * wheel_rpm) / 60.0
    def normalize_rpm(self, value): # RPM値正規化
        if isinstance(value, (list, tuple)):
            return float(value[0])
        if isinstance(value, str):
            if ':' in value:
                return float(value.split(':')[-1])
            return 0.0
        return float(value)

    def read_actual_speed(self):# モータから実速度取得
        raw_rpm = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 0)
        motor_rpm = -self.normalize_rpm(raw_rpm)
        act_speed_ms = self.motor_rpm_to_speed_ms(motor_rpm)
        return act_speed_ms

    def update_target_speed(self): # キーボード入力で目標速度更新
        if keyboard.is_pressed("w"):
            self.target_speed = 0.1
        elif keyboard.is_pressed("s"):
            self.target_speed = -0.1
        else:
            self.target_speed = 0.0

    def compute_cmd(self): # PI制御でcmd計算
        act = self.read_actual_speed()
        err = self.target_speed - act

        # 積分計算
        self.I += err
        self.I = max(min(self.I, self.I_max), self.I_min)

        # PI制御
        self.cmd = int(self.Kp * err + self.Ki * self.I)
        self.cmd = max(min(self.cmd, 100), -100)

    def send_cmd(self): # 指令送信
        self.controller.send_command(cmds.SET_SPEED, 1, self.cmd)
        self.controller.send_command(cmds.SET_SPEED, 2, self.cmd)

    def run(self):# メインループ
        try:
            while True:
                self.update_target_speed()
                self.compute_cmd()
                self.send_cmd()

                print(f"TARGET:{self.target_speed:+.3f} ACT:{self.actual_speed:+.3f} CMD:{self.cmd:+d}")
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("制御停止")
            self.controller.send_command(cmds.SET_SPEED, 1, 0)
            self.controller.send_command(cmds.SET_SPEED, 2, 0)

if __name__ == "__main__":
    controller = KeyboardPIControl()
    controller.run()
#キーボード操作のみ