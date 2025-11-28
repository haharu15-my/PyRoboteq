from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

controller = RoboteqHandler()
connected = controller.connect("COM3")

controller.send_command(cmds.REL_EM_STOP)  # 電子緊急停止を解除

drive_speed_motor_one = 0
drive_speed_motor_two = 0

# 停止したタイミングを記録するための変数
stop_time = None
torque_ready = False

if __name__ == "__main__":
    print("Press D to drive")
    print("Press S to stop")
    print("After stopping: wait 10 seconds and press 'y' to enable torque")

    while connected:

        speed1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        speed2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

        # ---- D key → run ---------------------------------------------------
        if keyboard.is_pressed('d'):
            drive_speed_motor_one = -200
            drive_speed_motor_two  = -200
            stop_time = None            # 動き出したら停止タイマーはリセット
            torque_ready = False

        # ---- S key → stop --------------------------------------------------
        if keyboard.is_pressed('s'):
            drive_speed_motor_one = 0
            drive_speed_motor_two = 0

            # 停止した瞬間に時間記録（stop_time が未設定なら記録）
            if stop_time is None:
                stop_time = time.time()
                print("Stopped. Starting 10 sec timer...")

        # ---- 停止後10秒経った？ --------------------------------------------------
        if stop_time is not None:
            if time.time() - stop_time >= 10:
                torque_ready = True   # 10秒経過フラグ
                # print("10 seconds passed. Press y to enable torque.")

        # ---- y を押したらトルクコマンド -----------------------------------
        if torque_ready and keyboard.is_pressed('y'):
            print("Torque enabled!")
            controller.send_command(cmds.GO_TORQUE, 1, 124)
            controller.send_command(cmds.GO_TORQUE, 2, 124)
            torque_ready = False   # 再実行防止
            stop_time = None       # 状態リセット

        # ---- モーターへコマンド送信 -----------------------------------------
        controller.send_command(cmds.DUAL_DRIVE, drive_speed_motor_one, drive_speed_motor_two)

        time.sleep(0.05)
