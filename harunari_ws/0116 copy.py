from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

# ===== Roboteq 接続 =====
controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

# ===== パラメータ =====
RPM_THRESHOLD = 5
STUCK_TIME = 1.0

# ===== 状態変数 =====
driving = False
stuck_start_time = None
stuck = False

print("W: forward / S: stop")

while connected:
    try:
        # ===== キー入力（イベント的に扱う）=====
        if keyboard.is_pressed('w'):
            driving = True
        if keyboard.is_pressed('s'):
            driving = False
            stuck_start_time = None
            stuck = False

        # ===== モータ指令 =====
        if driving:
            drive_speed_motor_one = -200
            drive_speed_motor_two = -200
        else:
            drive_speed_motor_one = 0
            drive_speed_motor_two = 0

        controller.send_command(
            cmds.DUAL_DRIVE,
            drive_speed_motor_one,
            drive_speed_motor_two
        )

        # ===== 回転数取得 =====
        rpm1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        rpm2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

        try:
            rpm1 = float(rpm1)
            rpm2 = float(rpm2)
        except (TypeError, ValueError):
            continue

        # ===== スタック判定 =====
        if driving:
            if abs(rpm1) < RPM_THRESHOLD and abs(rpm2) < RPM_THRESHOLD:
                if stuck_start_time is None:
                    stuck_start_time = time.time()
                elif time.time() - stuck_start_time >= STUCK_TIME:
                    if not stuck:
                        print("STUCK DETECTED")
                        stuck = True
            else:
                stuck_start_time = None
                stuck = False

        # ===== 表示 =====
        print(f"driving:{driving} RPM1:{rpm1:.1f} RPM2:{rpm2:.1f}")

    except KeyboardInterrupt:
        controller.send_command(cmds.DUAL_DRIVE, 0, 0)
        print("Program stopped")
        break
