from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")

# 電子緊急停止解除
controller.send_command(cmds.REL_EM_STOP)

TARGET_CURRENT = 12.4   # 目標電流[A]
Kp = 8                  # 調整用（高いほど反応が速い）
MAX_TORQUE = 400        # 安全上限（環境に合わせて変更）

# トルク指令（GO_TORQUEへ渡す値）
torque_left = 0
torque_right = 0

if __name__ == "__main__":
    while connected:
        try:
            # --- 現在の総電流を取得（0番は全体） ---
            motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0)
            try:
                motor_amps = float(motor_amps)
            except:
                motor_amps = 0.0

            # --- 現在のキー状態による方向制御（符号のみ使う） ---
            forward = 0     # +1 or -1
            turn = 0        # +1 or -1

            if keyboard.is_pressed('w'):
                forward = -1   # Roboteqは負で前進
                print("W pressed")

            elif keyboard.is_pressed('s'):
                forward = 1
                print("S pressed")

            if keyboard.is_pressed('a'):
                turn = 1
                print("A pressed")

            elif keyboard.is_pressed('d'):
                turn = -1
                print("D pressed")

            # --- 目標電流との差（偏差） ---
            error = TARGET_CURRENT - motor_amps

            # --- P制御でトルクを調整 ---
            torque_adjust = Kp * error

            # --- 左右のトルクの方向を決定 ---
            # 前進/後退トルク + 回転トルク
            torque_left  += torque_adjust * forward + (turn * torque_adjust)
            torque_right += torque_adjust * forward - (turn * torque_adjust)

            # --- リミット ---
            torque_left  = max(-MAX_TORQUE, min(MAX_TORQUE, torque_left))
            torque_right = max(-MAX_TORQUE, min(MAX_TORQUE, torque_right))

            # --- トルクコマンド送信 ---
            controller.send_command(cmds.GO_TORQUE, 1, int(torque_left))
            controller.send_command(cmds.GO_TORQUE, 2, int(torque_right))

            print(f"Current: {motor_amps:.2f} A | TL: {int(torque_left)}  TR: {int(torque_right)}")

        except KeyboardInterrupt:
            break

