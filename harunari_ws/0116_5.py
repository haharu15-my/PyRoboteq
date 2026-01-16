from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

# ===== パラメータ =====
RPM_THRESHOLD = 5            # これ以下なら回っていない
AMP_THRESHOLD = 5.0          # 平均電流がこれ以上
AMP_STABLE_WIDTH = 1.0       # 電流の変動幅（±1A）
STUCK_TIME = 1.0             # 秒

# ===== 状態変数 =====
stuck_start_time = None
stuck_flag = False
amp_buffer = []

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

            # --- ログ表示 ---
            print(f"drive:{driving} RPM1:{rpm1:.1f} RPM2:{rpm2:.1f} AMP:{amps:.1f}")

            # ===== 電流バッファ更新 =====
            if driving:
                amp_buffer.append(amps)
                if len(amp_buffer) > 20:   # 約1秒分（0.05s × 20）
                    amp_buffer.pop(0)
            else:
                amp_buffer.clear()

            # ===== スタック複合判定 =====
            if (driving and abs(rpm1) < RPM_THRESHOLD and abs(rpm2) < RPM_THRESHOLD and len(amp_buffer) >= 10):
                amp_max = max(amp_buffer)
                amp_min = min(amp_buffer)
                amp_avg = sum(amp_buffer) / len(amp_buffer)

                if amp_avg > AMP_THRESHOLD and (amp_max - amp_min) < AMP_STABLE_WIDTH:
                    if stuck_start_time is None:
                        stuck_start_time = time.time()
                    elif time.time() - stuck_start_time >= STUCK_TIME:
                        stuck_flag = True
                else:
                    stuck_start_time = None
                    stuck_flag = False
            else:
                stuck_start_time = None
                stuck_flag = False

            # --- スタック表示（解消まで出し続ける） ---
            if stuck_flag:
                print("STUCK DETECTED")

            time.sleep(0.05)

        except KeyboardInterrupt:
            break