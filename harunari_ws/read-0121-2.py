from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

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
        self.I_max = 50   # 積分上限
        self.I_min = -50  # 積分下限

        # 速度制御
        self.target_speed = 0.0  # m/s
        self.speed_step = 0.01   # キーボード1押しでの変化量
        self.actual_speed = 0.0  # モータからの速度読み取り（仮）

        self.cmd = 0

    def read_actual_speed(self):
        # ここにモータからの実速度読み取りを入れる
        # 今は仮に0としておく
        return self.actual_speed

    def update_target_speed(self):
        if keyboard.is_pressed("w"):
            self.target_speed += self.speed_step
        elif keyboard.is_pressed("s"):
            self.target_speed -= self.speed_step

        # TARGET制限
        self.target_speed = max(min(self.target_speed, 1.0), -1.0)

    def compute_cmd(self):
        act = self.read_actual_speed()
        err = self.target_speed - act

        # 積分計算
        self.I += err
        self.I = max(min(self.I, self.I_max), self.I_min)

        # PI制御
        self.cmd = int(self.Kp * err + self.Ki * self.I)

        # CMD制限
        self.cmd = max(min(self.cmd, 100), -100)

    def send_cmd(self):
        # モータ1,2に同じCMD送る
        self.controller.send_command(cmds.SET_SPEED, 1, self.cmd)
        self.controller.send_command(cmds.SET_SPEED, 2, self.cmd)

    def run(self):
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
