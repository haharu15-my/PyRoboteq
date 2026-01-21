from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

class PIController:
    def __init__(self, Kp=0.5, Ki=0.2, I_max=100, I_min=-100):
        self.Kp = Kp
        self.Ki = Ki
        self.I_max = I_max
        self.I_min = I_min
        self.integral = 0.0

    def reset_integral(self):
        self.integral = 0.0

    def update(self, target, actual, dt):
        error = target - actual
        self.integral += error * dt
        # 積分制限
        self.integral = max(self.I_min, min(self.integral, self.I_max))
        cmd = self.Kp * error + self.Ki * self.integral
        return cmd

class MotorController:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)  # 緊急停止解除

    def drive(self, cmd_motor_one, cmd_motor_two):
        # CMDを送信（ここではオープンループ制御）
        self.controller.send_command(cmds.SET_MOTOR_1_SPEED, int(cmd_motor_one))
        self.controller.send_command(cmds.SET_MOTOR_2_SPEED, int(cmd_motor_two))

def get_keyboard_offset(step=0.01):
    """w/sで速度上げ下げ"""
    offset = 0.0
    if keyboard.is_pressed('w'):
        offset += step
    if keyboard.is_pressed('s'):
        offset -= step
    return offset

def main():
    motor = MotorController()
    pi = PIController(Kp=0.5, Ki=0.2)
    target_speed_auto = 0.1   # 自律走行の目標速度
    actual_speed = 0.0        # モータから取得する速度（ここではダミー）
    dt = 0.1                  # 制御周期 0.1秒

    try:
        while True:
            # キーボード操作による補正
            keyboard_offset = get_keyboard_offset()
            target_speed = target_speed_auto + keyboard_offset

            # PI制御でモータ指令を計算
            cmd = pi.update(target_speed, actual_speed, dt)

            # モータに指令送信（左右同じCMD）
            motor.drive(cmd, cmd)

            # デバッグ出力
            print(f"TARGET:{target_speed:+.3f} ACT:{actual_speed:+.3f} CMD:{cmd:+.1f}")

            time.sleep(dt)

    except KeyboardInterrupt:
        print("制御停止")
        motor.drive(0, 0)

if __name__ == "__main__":
    main()
#キーボード操作+自律TARGET まだ動かしていない