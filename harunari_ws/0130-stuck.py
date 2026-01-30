from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")  # 環境に合わせて変更

# 電子緊急停止を解除
controller.send_command(cmds.REL_EM_STOP)

FORWARD_CMD = -100  # 前進コマンド（必要なら変更）

# 状態
state = "IDLE"          # IDLE, COUNTDOWN, RUN
countdown_start = None  # カウントダウン開始時刻

def set_drive(cmd):
    controller.send_command(cmds.DUAL_DRIVE, cmd, cmd)

def move():
    global state, countdown_start

    # 念のため最初は停止
    set_drive(0)

    while connected:
        try:
            # ---- 緊急停止（ソフト側） ----
            if keyboard.is_pressed('s'):
                if state != "IDLE":
                    print("STOP (S pressed)")
                state = "IDLE"
                countdown_start = None
                set_drive(0)
                time.sleep(0.3)  # チャタリング防止
                continue

            # ---- W 押下でカウントダウン開始 ----
            if keyboard.is_pressed('w') and state == "IDLE":
                state = "COUNTDOWN"
                countdown_start = time.time()
                print("W pressed -> Countdown 3s")
                time.sleep(0.3)  # チャタリング防止

            # ---- 状態処理 ----
            if state == "COUNTDOWN":
                elapsed = time.time() - countdown_start
                remaining = 3.0 - elapsed

                # カウント中は安全のため停止指令
                set_drive(0)

                if remaining > 0:
                    # 表示がうるさければ間引いてもOK
                    print(f"COUNTDOWN: {remaining:.1f}s")
                else:
                    state = "RUN"
                    print("GO! -> RUN")

            elif state == "RUN":
                set_drive(FORWARD_CMD)

            else:  # IDLE
                set_drive(0)

            # ---- ログ表示（必要なら） ----
            motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0)
            motor_rpm  = controller.read_value(cmds.READ_BL_MOTOR_RPM, 0)
            print(f"STATE={state} | RPM={motor_rpm} | AMPS={motor_amps}")

            time.sleep(0.05)

        except KeyboardInterrupt:
            break

    # 終了時は停止
    set_drive(0)

if __name__ == "__main__":
    move()
