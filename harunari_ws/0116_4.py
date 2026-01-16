from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

# ===== パラメータ =====
RPM_THRESHOLD = 5        # これ以下なら「回っていない」
STUCK_TIME = 1.0         # 何秒続いたらスタックか

# ===== 状態変数 =====
stop_start_time = None   # 止まり始めた時刻
stuck_flag = False

if __name__ == "__main__":
    while connected:
        try:
            # --- RPM取得 ---
            speed_motor1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
            speed_motor2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

            # --- 文字列対策 ---
            try:
                if isinstance(speed_motor1, str):
                    speed_motor1 = speed_motor1.split('=')[-1]
                if isinstance(speed_motor2, str):
                    speed_motor2 = speed_motor2.split('=')[-1]

                rpm1 = float(speed_motor1)
                rpm2 = float(speed_motor2)
            except (TypeError, ValueError):
                continue

            # --- キー入力 ---
            if keyboard.is_pressed('w'):
                drive_speed_motor_one = -100
                drive_speed_motor_two = -100
                driving = True
            else:
                drive_speed_motor_one = 0
                drive_speed_motor_two = 0
                driving = False

            controller.send_command(
                cmds.DUAL_DRIVE,
                drive_speed_motor_one,
                drive_speed_motor_two
            )

            # --- 表示 ---
            print(f"driving:{driving} RPM1:{rpm1:.1f} RPM2:{rpm2:.1f}")

            # ===== スタック判定 =====
            if driving and abs(rpm1) < RPM_THRESHOLD and abs(rpm2) < RPM_THRESHOLD:
                if stop_start_time is None:
                    stop_start_time = time.time()
                elif time.time() - stop_start_time >= STUCK_TIME:
                    if not stuck_flag:
                        print("STUCK DETECTED")
                        stuck_flag = True
            else:
                stop_start_time = None
                stuck_flag = False

            time.sleep(0.05)  # ループ安定化

        except KeyboardInterrupt:
            break
 #成功一定時間継続版（defなし）をそのまま書く