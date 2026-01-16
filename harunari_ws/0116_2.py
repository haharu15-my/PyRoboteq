from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

AMP_THRESHOLD = 10.0     # 要調整
STUCK_TIME = 1.0

driving = False
stuck_start_time = None
stuck = False

print("W: forward / S: stop")

while connected:
    try:
        # --- キー入力 ---
        if keyboard.is_pressed('w'):
            driving = True
        if keyboard.is_pressed('s'):
            driving = False
            stuck_start_time = None
            stuck = False

        # --- モータ指令 ---
        if driving:
            controller.send_command(cmds.DUAL_DRIVE, -100, -100)
        else:
            controller.send_command(cmds.DUAL_DRIVE, 0, 0)

        # --- 電流値取得（安定） ---
        motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0)
        try:
            motor_amps = float(motor_amps)
        except (TypeError, ValueError):
            continue

        print(f"driving:{driving} AMP:{motor_amps}")

        # --- スタック判定 ---
        if driving and motor_amps > AMP_THRESHOLD:
            if stuck_start_time is None:
                stuck_start_time = time.time()
            elif time.time() - stuck_start_time >= STUCK_TIME:
                if not stuck:
                    print("STUCK DETECTED")
                    stuck = True
        else:
            stuck_start_time = None
            stuck = False

    except KeyboardInterrupt:
        controller.send_command(cmds.DUAL_DRIVE, 0, 0)
        print("Program stopped")
        break
