from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

# ===== パラメータ =====
RPM_THRESHOLD = 5          # 回っていないとみなすRPM
AMP_THRESHOLD = 5.0        # 負荷がかかっているとみなす電流[A]
STUCK_TIME = 5.0           # 何秒続いたらスタックか

# ===== 状態変数 =====
stuck_start_time = None
stuck_flag = False

if __name__ == "__main__":
    while connected:
        try:
            # --- RPM取得 ---
            speed_motor1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
            speed_motor2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

            # --- 電流取得 ---
            motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0)

            # --- 文字列対策 ---
            try:
                if isinstance(speed_motor1, str):
                    speed_motor1 = speed_motor1.split('=')[-1]
                if isinstance(speed_motor2, str):
                    speed_motor2 = speed_motor2.split('=')[-1]
                if isinstance(motor_amps, str):
                    motor_amps = motor_amps.split('=')[-1]

                rpm1 = float(speed_motor1)
                rpm2 = float(speed_motor2)
                amps = abs(float(motor_amps))
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

            # --- 状態表示 ---
            print(f"drive:{driving}"f"RPM1:{rpm1:.1f} RPM2:{rpm2:.1f} "f"AMP:{amps:.1f}")

            # ===== スタック複合判定 =====
            if (driving and abs(rpm1) < RPM_THRESHOLD and abs(rpm2) < RPM_THRESHOLD and amps > AMP_THRESHOLD):
                if stuck_start_time is None:
                    stuck_start_time = time.time()
                elif time.time() - stuck_start_time >= STUCK_TIME:
                    stuck_flag = True
            else:
                stuck_start_time = None
                stuck_flag = False

            # --- スタック表示（解消まで出し続ける） ---
            if stuck_flag:
                print("STUCK DETECTED")

            time.sleep(0.05)

        except KeyboardInterrupt:
            break
