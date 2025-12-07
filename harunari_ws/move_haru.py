from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

controller = RoboteqHandler()
connected = controller.connect("COM3")

controller.send_command(cmds.REL_EM_STOP)  # 電子緊急停止を解除

stop_start_time = None  # 速度 0 になった時刻

if __name__ == "__main__":
    while connected:

        speed1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        speed2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

        if speed1 == 0 and speed2 == 0: # 速度が両方 0 の場合

            if stop_start_time is None: # 停止し始めた瞬間の時間を記録
                stop_start_time = time.time()

            if time.time() - stop_start_time >= 10: # 停止し続けて10秒経過したらトルク発射
                controller.send_command(cmds.GO_TORQUE, 1, 120)
                controller.send_command(cmds.GO_TORQUE, 2, 120)
                time.sleep(0.05)

        else:
            stop_start_time = None  # 動き出したらカウントリセット

        controller.send_command(cmds.DUAL_DRIVE, speed1, speed2)    # DUAL_DRIVE に現在速度を送信（速度フィードバック制御）
