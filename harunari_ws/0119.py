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

AMP_WINDOW_TIME = 2.0
AMP_VARIATION = 3.0

RECOVERY_TIME = 5.0
RECOVERY_SPEED = -120
NORMAL_SPEED = -100

# ===== 状態 =====
rpm_stop_start = None
amp_buffer1 = []
amp_buffer2 = []

stuck_flag1 = False
stuck_flag2 = False

mode = "MANUAL"      # MANUAL / RECOVERY / ERROR_STOP
recovery_start = 0

if __name__ == "__main__":
    while connected:
        try:
            # ===== センサ読み取り =====
            speed_motor1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
            speed_motor2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)
            motor_amps1 = controller.read_value(cmds.READ_MOTOR_AMPS, 1)
            motor_amps2 = controller.read_value(cmds.READ_MOTOR_AMPS, 2)

            # 文字列対策
            try:
                rpm1 = abs(float(str(speed_motor1).split('=')[-1]))
                rpm2 = abs(float(str(speed_motor2).split('=')[-1]))
                amps1 = abs(float(str(motor_amps1).split('=')[-1]))
                amps2 = abs(float(str(motor_amps2).split('=')[-1]))
            except:
                continue

            now = time.time()

            # ===== MANUAL =====
            if mode == "MANUAL":
                if keyboard.is_pressed('w'):
                    drive_m1 = NORMAL_SPEED
                    drive_m2 = NORMAL_SPEED
                    driving = True
                else:
                    drive_m1 = 0
                    drive_m2 = 0
                    driving = False

            # ===== RECOVERY =====
            elif mode == "RECOVERY":
                drive_m1 = RECOVERY_SPEED
                drive_m2 = RECOVERY_SPEED
                driving = True

                if now - recovery_start >= RECOVERY_TIME:
                    if rpm1 > RPM_THRESHOLD or rpm2 > RPM_THRESHOLD:
                        print("RECOVERY SUCCESS → MANUAL")
                        mode = "MANUAL"
                        rpm_stop_start = None
                        amp_buffer1.clear()
                        amp_buffer2.clear()
                    else:
                        print("ERROR: RECOVERY FAILED → STOP")
                        mode = "ERROR_STOP"

            # ===== ERROR_STOP =====
            else:
                drive_m1 = 0
                drive_m2 = 0
                controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                print("SYSTEM HALTED")
                break

            controller.send_command(cmds.DUAL_DRIVE, drive_m1, drive_m2)

            # ===== stuck_flag1（回転停止）=====
            if driving and rpm1 < RPM_THRESHOLD and rpm2 < RPM_THRESHOLD:
                if rpm_stop_start is None:
                    rpm_stop_start = now
                elif now - rpm_stop_start >= RPM_STUCK_TIME:
                    stuck_flag1 = True
            else:
                rpm_stop_start = None
                stuck_flag1 = False

            # ===== stuck_flag2（電流張り付き）=====
            if driving:
                amp_buffer1.append((now, amps1))
                amp_buffer2.append((now, amps2))

                amp_buffer1 = [(t, a) for t, a in amp_buffer1 if now - t <= AMP_WINDOW_TIME]
                amp_buffer2 = [(t, a) for t, a in amp_buffer2 if now - t <= AMP_WINDOW_TIME]

                amps1_list = [a for _, a in amp_buffer1]
                amps2_list = [a for _, a in amp_buffer2]

                amp_range1 = max(amps1_list) - min(amps1_list) if amps1_list else 0
                amp_range2 = max(amps2_list) - min(amps2_list) if amps2_list else 0

                stuck_flag2 = (amp_range1 < AMP_VARIATION) and (amp_range2 < AMP_VARIATION)
            else:
                amp_buffer1.clear()
                amp_buffer2.clear()
                stuck_flag2 = False

            # ===== スタック検知 → 回復開始 =====
            if mode == "MANUAL" and stuck_flag1 and stuck_flag2:
                print("STUCK DETECTED → RECOVERY MODE")
                mode = "RECOVERY"
                recovery_start = now

            print(
                f"MODE:{mode} "
                f"RPM1:{rpm1:.1f} RPM2:{rpm2:.1f} "
                f"AMP1:{amps1:.1f} AMP2:{amps2:.1f}"
            )

            time.sleep(0.05)

        except KeyboardInterrupt:
            controller.send_command(cmds.DUAL_DRIVE, 0, 0)
            break
