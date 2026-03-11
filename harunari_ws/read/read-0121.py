import time
from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds

class OpenLoopPI:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)  # 電子緊急停止解除

        # ===== PIパラメータ =====
        self.Kp = 0.5
        self.Ki = 0.05

        self.I = 0.0
        self.deadzone = 4       # ±4未満はCMD=0
        self.dt = 0.05          # 制御周期[s]

    def speed_ms_to_cmd(self, speed_ms):
        """
        m/s を Roboteq CMD パワー値に変換
        -1000 = 1m/s 最高速度
        """
        return int(-speed_ms * 1000)  # Roboteq仕様：負が前進

    def update(self, target_speed_ms, actual_speed_ms):
        # ----- 誤差計算 -----
        error = target_speed_ms - actual_speed_ms

        # ----- 積分更新 -----
        self.I += error * self.dt * self.Ki

        # ----- Iリセット条件 -----
        if abs(target_speed_ms) < 0.001 and abs(actual_speed_ms) < 0.005:
            self.I = 0.0

        # ----- PI制御計算 -----
        cmd = self.Kp * error + self.I

        # ----- CMDをRoboteqパワーに変換 -----
        cmd_val = self.speed_ms_to_cmd(cmd)

        # ----- デッドゾーン補正 -----
        if abs(cmd_val) < self.deadzone:
            cmd_val = 0

        # ----- 指令送信 -----
        self.controller.send_command(cmds.DUAL_DRIVE, cmd_val, cmd_val)

        # デバッグ出力
        print(f"TARGET:{target_speed_ms:+.3f} ACT:{actual_speed_ms:+.3f} ERR:{error:+.3f} I:{self.I:.3f} CMD:{cmd_val}")

        return cmd_val

# ===== 使用例 =====
if __name__ == "__main__":
    pi = OpenLoopPI(port="COM3")
    target_speed = 0.1  # m/s

    try:
        while True:
            # ここは実際にはセンサーから取得する速度に置き換え
            actual_speed = 0.0  # 仮の値
            pi.update(target_speed, actual_speed)
            time.sleep(pi.dt)

    except KeyboardInterrupt:
        # 停止
        pi.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
        print("制御停止")