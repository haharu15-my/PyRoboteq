from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")  # 環境に合わせて変更

# 電子緊急停止を解除
controller.send_command(cmds.REL_EM_STOP)

# ===== 指令値 =====
FORWARD_CMD = -100   # 前進
REVERSE_CMD =  200   # 後退（強めに戻したい想定）

# ===== 状態 =====
state = "IDLE"            # IDLE, COUNTDOWN_FWD, RUN_FWD, RUN_REV
countdown_start = None

def set_drive(cmd):
    controller.send_command(cmds.DUAL_DRIVE, cmd, cmd)

def stop_all():
    global state, countdown_start
    state = "IDLE"
    countdown_start = None
    set_drive(0)

def move():
    global state, countdown_start

    stop_all()  # 念のため最初は停止

    while connected:
        try:
            # ---- 最優先：停止 ----
            if keyboard.is_pressed('s'):
                print("STOP (S pressed)")
                stop_all()
                time.sleep(0.3)  # チャタリング防止
                continue

            # ---- x：即後退（カウントダウン無し） ----
            if keyboard.is_pressed('x'):
                if state != "RUN_REV":
                    print("REVERSE START (X pressed) -> RUN_REV (no countdown)")
                state = "RUN_REV"
                countdown_start = None
                time.sleep(0.3)
                # continue しない（この周回でRUN_REVを実行させる）

            # ---- w：前進は3秒カウントダウン ----
            if keyboard.is_pressed('w') and state == "IDLE":
                state = "COUNTDOWN_FWD"
                countdown_start = time.time()
                print("FORWARD START (W pressed) -> Countdown 3s")
                time.sleep(0.3)

            # ---- 状態処理 ----
            if state == "COUNTDOWN_FWD":
                elapsed = time.time() - countdown_start
                remaining = 3.0 - elapsed

                # カウント中は停止指令（安全）
                set_drive(0)

                if remaining > 0:
                    print(f"COUNTDOWN: {remaining:.1f}s")
                else:
                    state = "RUN_FWD"
                    print("GO! -> RUN_FWD")

            elif state == "RUN_FWD":
                set_drive(FORWARD_CMD)

            elif state == "RUN_REV":
                set_drive(REVERSE_CMD)

            else:  # IDLE
                set_drive(0)

            # ---- ログ表示（必要なら） ----
            motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0)
            motor_rpm  = controller.read_value(cmds.READ_BL_MOTOR_RPM, 0)
            print(f"STATE={state} | RPM={motor_rpm} | AMPS={motor_amps}")

            time.sleep(0.05)

        except KeyboardInterrupt:
            break

    stop_all()

if __name__ == "__main__":
    move()