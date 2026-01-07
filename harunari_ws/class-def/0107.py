from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time

# =========================
# パラメータ（卒論で説明）
# =========================
TARGET_RPM = 500              # 目標速度 [RPM]
SPEED_THRESHOLD = 50          # これ以下なら「動いていない」
CURRENT_THRESHOLD = 10.0      # [A] スタックとみなす電流
STUCK_TIME = 2.0              # [s] 継続時間

LOOP_DT = 0.05                # 制御周期 [s]

# =========================
# 状態定義
# =========================
STATE_NORMAL = 0
STATE_STUCK = 1

state = STATE_NORMAL
stuck_timer = 0.0

# =========================
# Roboteq 接続
# =========================
controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")

if not connected:
    print("Roboteq not connected")
    exit()

# 電子緊急停止解除
controller.send_command(cmds.REL_EM_STOP)

print("Start control loop")

# =========================
# メインループ
# =========================
while True:
    # --- センサ取得 ---
    speed = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)   # BS
    current = controller.read_value(cmds.READ_MOTOR_AMPS, 1)  # A

    if speed is None or current is None:
        continue

    speed = abs(speed)

    # =========================
    # 状態：通常走行
    # =========================
    if state == STATE_NORMAL:
        # 速度指令（Closed Loop Speed）
        controller.send_command(cmds.GO, 1, TARGET_RPM)

        # --- スタック監視 ---
        if speed < SPEED_THRESHOLD and current > CURRENT_THRESHOLD:
            stuck_timer += LOOP_DT
        else:
            stuck_timer = 0.0

        if stuck_timer >= STUCK_TIME:
            print("STUCK DETECTED")
            state = STATE_STUCK

    # =========================
    # 状態：スタック
    # =========================
    elif state == STATE_STUCK:
        # 安全のため停止
        controller.send_command(cmds.MOTOR_STOP, 1)
        print("Motor stopped due to stuck")

        # 本来はここで回復動作を書く
        # （例：逆転 → 再前進）

        break

    # --- ログ表示（卒論の実験結果用） ---
    print(f"speed={speed:.1f} rpm, current={current:.1f} A, state={state}")

    time.sleep(LOOP_DT)
