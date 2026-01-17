from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

# ===== パラメータ =====
RPM_THRESHOLD = 5
RPM_STUCK_TIME = 1.0

AMP_WINDOW_TIME = 2.0        # 電流を見る時間[s] （短めに設定してリアルタイム判定）
AMP_VARIATION = 3.0          # 変動幅[A]

# ===== 状態変数 =====
rpm_stop_start = None

amp_buffer1 = []
amp_buffer2 = []

stuck_flag1 = False   # 回転停止
stuck_flag2 = False   # 電流張り付き

if __name__ == "__main__":
    while connected:
        try:
            # --- RPM ---
            speed_motor1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
            speed_motor2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

            # --- 電流（左右別） ---
            motor_amps1 = controller.read_value(cmds.READ_MOTOR_AMPS, 1)
            motor_amps2 = controller.read_value(cmds.READ_MOTOR_AMPS, 2)

            # --- 文字列対策 ---
            try:
                if isinstance(speed_motor1, str):
                    speed_motor1 = speed_motor1.split('=')[-1]
                if isinstance(speed_motor2, str):
                    speed_motor2 = speed_motor2.split('=')[-1]
                if isinstance(motor_amps1, str):
                    motor_amps1 = motor_amps1.split('=')[-1]
                if isinstance(motor_amps2, str):
                    motor_amps2 = motor_amps2.split('=')[-1]

                rpm1 = abs(float(speed_motor1))
                rpm2 = abs(float(speed_motor2))
                amps1 = abs(float(motor_amps1))
                amps2 = abs(float(motor_amps2))
            except (TypeError, ValueError):
                continue

            # --- 走行指令 ---
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

            # ===== stuck_flag1：回転停止 =====
            if driving and rpm1 < RPM_THRESHOLD and rpm2 < RPM_THRESHOLD:
                if rpm_stop_start is None:
                    rpm_stop_start = time.time()
                elif time.time() - rpm_stop_start >= RPM_STUCK_TIME:
                    stuck_flag1 = True
            else:
                rpm_stop_start = None
                stuck_flag1 = False

            # ===== stuck_flag2：電流張り付き（移動ウィンドウ判定） =====
            if driving:
                now = time.time()
                # バッファに追加
                amp_buffer1.append((now, amps1))
                amp_buffer2.append((now, amps2))

                # 古いデータを削除
                amp_buffer1 = [(t, a) for t, a in amp_buffer1 if now - t <= AMP_WINDOW_TIME]
                amp_buffer2 = [(t, a) for t, a in amp_buffer2 if now - t <= AMP_WINDOW_TIME]

                # 変動幅を計算
                amps1_list = [a for t, a in amp_buffer1]
                amps2_list = [a for t, a in amp_buffer2]

                amp_range1 = max(amps1_list) - min(amps1_list) if amps1_list else 0
                amp_range2 = max(amps2_list) - min(amps2_list) if amps2_list else 0

                stuck_flag2 = (amp_range1 < AMP_VARIATION) and (amp_range2 < AMP_VARIATION)
            else:
                amp_buffer1 = []
                amp_buffer2 = []
                stuck_flag2 = False

            # --- 状態表示 ---
            print(
                f"RPM1:{rpm1:.1f} RPM2:{rpm2:.1f} "
                f"AMP1:{amps1:.1f} AMP2:{amps2:.1f} "
                f"flag1:{stuck_flag1} flag2:{stuck_flag2}"
            )

            # ===== 最終判定 =====
            if stuck_flag1 and stuck_flag2:
                print("STUCK DETECTED")

            time.sleep(0.05)

        except KeyboardInterrupt:
            break
