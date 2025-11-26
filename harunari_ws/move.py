from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard  # このライブラリを使うには管理者権限が必要

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")  # 環境に合わせて変更  

# 電子緊急停止を解除
controller.send_command(cmds.REL_EM_STOP)

if __name__ == "__main__":
    while connected:
        try:
            motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0)  # チャンネル1
            if keyboard.is_pressed('w'):#前進
                print("W pressed")
                drive_speed_motor_one = -200
                drive_speed_motor_two  = -200
                print(motor_amps)

            elif keyboard.is_pressed('s'):#後退
                print("S pressed")
                drive_speed_motor_one = 200
                drive_speed_motor_two  = 200
                print(motor_amps)

            elif keyboard.is_pressed('a'):#左回転
                print("A pressed")
                drive_speed_motor_one = -200
                drive_speed_motor_two  = 200
                print(motor_amps)

            elif keyboard.is_pressed('d'):#右回転
                print("D pressed")
                drive_speed_motor_one = 200
                drive_speed_motor_two  = -200
                print(motor_amps)

            else:
                drive_speed_motor_one = 0
                drive_speed_motor_two  = 0

            controller.send_command(cmds.DUAL_DRIVE, drive_speed_motor_one, drive_speed_motor_two)

        except KeyboardInterrupt:
            break