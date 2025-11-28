from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

controller = RoboteqHandler()
connected = controller.connect("COM3")

controller.send_command(cmds.REL_EM_STOP)  # 電子緊急停止を解除

drive_speed_motor_one = 0
drive_speed_motor_two = 0

stop_time = None
torque_ready = False
last_remaining = None

if __name__ == "__main__":
    print("Press W to drive forward")
    print("Press S to stop manually")
    print("If stuck: wait 10 seconds and press 'Y' to enable torque")

    while connected:
        # モーター速度を取得
        speed1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        speed2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)
        avg_speed = (abs(speed1) + abs(speed2)) / 2

        # ---- W key → forward ---------------------------------------------
        if keyboard.is_pressed('w'):
            drive_speed_motor_one = -100
            drive_speed_motor_two  = -100
            if stop_time is not None:
                stop_time = None
                last_remaining = None
                torque_ready = False

        # ---- S key → manual stop -----------------------------------------
        if keyboard.is_pressed('s'):
            drive_speed_motor_one = 0
            drive_speed_motor_two = 0
            stop_time = None
            last_remaining = None
            torque_ready = False

        # ---- 自動停止検知（W押し中で速度が0かつS押していない） ----
        if keyboard.is_pressed('w') and avg_speed < 1 and not keyboard.is_pressed('s'):
            if stop_time is None:
                stop_time = time.time()
                print("Stuck detected. Starting 10 sec timer...")

        # ---- 停止後10秒経過チェック ----------------------------------------
        if stop_time is not None:
            elapsed = time.time() - stop_time
            remaining = max(0, 10 - int(elapsed))
            if remaining != last_remaining:
                print(f"\rWaiting: {remaining} sec", end="")
                last_remaining = remaining
            if elapsed >= 10 and not torque_ready:
                torque_ready = True
                print("\n10 seconds passed. Press 'Y' to enable torque.")

        # ---- Y key → torque command ---------------------------------------
        if torque_ready and keyboard.is_pressed('y'):
            print("Torque enabled!")
            controller.send_command(cmds.GO_TORQUE, 1, 12.4)
            controller.send_command(cmds.GO_TORQUE, 2, 12.4)
            torque_ready = False
            stop_time = None
            last_remaining = None

        # ---- モーターに速度送信 -------------------------------------------
        controller.send_command(cmds.DUAL_DRIVE, drive_speed_motor_one, drive_speed_motor_two)

        time.sleep(0.05)
