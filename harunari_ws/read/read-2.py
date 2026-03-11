from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time
import math

# ===== 定数定義 =====
MAX_SPEED_MS = 1.0        # [m/s] 想定最大速度（Nav2基準）
MAX_CMD = -1000           # Roboteq速度指令（符号注意）
WHEEL_RADIUS = 0.13       # [m] 車輪半径
GEAR_RATIO = 25.0         # ★減速比（要：実機に合わせて調整）

CONTROL_HZ = 25
DT = 1.0 / CONTROL_HZ

# ===== 変換関数 =====
def speed_ms_to_cmd(speed_ms):
    """
    [m/s] → Roboteq速度指令値
    """
    speed_ms = max(min(speed_ms, MAX_SPEED_MS), -MAX_SPEED_MS)
    return int(speed_ms / MAX_SPEED_MS * MAX_CMD)

def rpm_to_speed_ms(motor_rpm):
    """
    モータRPM → 実速度[m/s]
    ※ ギア比考慮
    """
    wheel_rpm = motor_rpm / GEAR_RATIO
    return (2.0 * math.pi * WHEEL_RADIUS * wheel_rpm) / 60.0

def normalize_rpm(value):
    """
    RoboteqのRPM返り値対策
    数値 / list / 'BS=0:0' 等を吸収
    """
    if isinstance(value, (list, tuple)):
        return float(value[0])
    if isinstance(value, str):
        if ':' in value:
            try:
                return float(value.split(':')[-1])
            except ValueError:
                return 0.0
        return 0.0
    return float(value)

# ===== Roboteq初期化 =====
controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")

# 電子非常停止解除
controller.send_command(cmds.REL_EM_STOP)

def move():
    print("=== START ===  W: forward / S: backward / Ctrl+C: exit")
    while connected:
        try:
            # --- キー入力（指令速度）---
            if keyboard.is_pressed('w'):
                cmd_speed_ms = 0.1
            elif keyboard.is_pressed('s'):
                cmd_speed_ms = -0.1
            else:
                cmd_speed_ms = 0.0

            # --- Roboteq指令送信 ---
            cmd_val = speed_ms_to_cmd(cmd_speed_ms)
            controller.send_command(cmds.DUAL_DRIVE, cmd_val, cmd_val)

            # --- RPM取得 ---
            raw_rpm = controller.read_value(cmds.READ_BL_MOTOR_RPM, 0)
            motor_rpm = normalize_rpm(raw_rpm)

            # --- 実速度計算 ---
            act_speed_ms = rpm_to_speed_ms(motor_rpm)

            # --- 表示 ---
            print(
                f"CMD:{cmd_speed_ms:+.3f} m/s | "
                f"RPM:{motor_rpm:7.2f} | "
                f"ACT:{act_speed_ms:+.3f} m/s"
            )

            time.sleep(DT)

        except KeyboardInterrupt:
            print("\n=== STOP ===")
            break

if __name__ == "__main__":
    move()
