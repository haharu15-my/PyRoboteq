from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time
import math

# ================= 定数 =================
WHEEL_RADIUS = 0.13      # [m]
GEAR_RATIO = 25
MAX_SPEED_MS = 0.5
MAX_CMD = -1000

CONTROL_HZ = 25
DT = 1.0 / CONTROL_HZ

# ===== PIゲイン =====
Kp = 0.3
Ki = 0.01      # ← 最初は小さめ！

# ================= 変換関数 =================
def speed_ms_to_cmd(speed_ms):
    speed_ms = max(min(speed_ms, MAX_SPEED_MS), -MAX_SPEED_MS)
    return int(speed_ms / MAX_SPEED_MS * MAX_CMD)

def motor_rpm_to_speed_ms(motor_rpm):
    wheel_rpm = motor_rpm / GEAR_RATIO
    return (2.0 * math.pi * WHEEL_RADIUS * wheel_rpm) / 60.0

def normalize_rpm(value):
    if isinstance(value, (list, tuple)):
        return float(value[0])
    if isinstance(value, str):
        if ':' in value:
            return float(value.split(':')[-1])
        return 0.0
    return float(value)

# ================= Roboteq初期化 =================
controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

# ================= メイン制御 =================
def move():
    print("=== START PI CONTROL ===")

    integral_error = 0.0

    while connected:
        try:
            # -------- 目標速度 --------
            if keyboard.is_pressed('w'):
                target_speed_ms = 0.1
            elif keyboard.is_pressed('s'):
                target_speed_ms = -0.1
            else:
                target_speed_ms = 0.0
                integral_error = 0.0  # ← 停止時はリセット（重要）

            # -------- 実速度 --------
            raw_rpm = controller.read_value(cmds.READ_BL_MOTOR_RPM, 0)
            motor_rpm = -normalize_rpm(raw_rpm)
            act_speed_ms = motor_rpm_to_speed_ms(motor_rpm)

            # -------- PI制御 --------
            error = target_speed_ms - act_speed_ms
            integral_error += error * DT

            cmd_speed_ms = target_speed_ms + Kp * error + Ki * integral_error

            # -------- 指令送信 --------
            cmd_val = speed_ms_to_cmd(cmd_speed_ms)
            controller.send_command(cmds.DUAL_DRIVE, cmd_val, cmd_val)

            # -------- 表示 --------
            print(
                f"CMD:{target_speed_ms:+.3f} "
                f"ACT:{act_speed_ms:+.3f} "
                f"ERR:{error:+.3f} "
                f"I:{integral_error:+.3f}"
            )

            time.sleep(DT)

        except KeyboardInterrupt:
            print("\n=== STOP ===")
            controller.send_command(cmds.DUAL_DRIVE, 0, 0)
            break

if __name__ == "__main__":
    move()
