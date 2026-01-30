from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard  # このライブラリを使うには管理者権限が必要

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")  # 環境に合わせて変更

# 電子緊急停止を解除
controller.send_command(cmds.REL_EM_STOP)

def move():
    while connected:
        try:
            motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0)
            motor_rpm = controller.read_value(cmds.READ_BL_MOTOR_RPM, 0)  # RPMで速度を読み取る

            if keyboard.is_pressed('a'):#前進
                print("a pressed")
                drive_speed_motor_one = -100
                drive_speed_motor_two  = -100

            elif keyboard.is_pressed('s'):#後退
                print("S pressed")
                drive_speed_motor_one = -125
                drive_speed_motor_two  = -125

            elif keyboard.is_pressed('d'):#後退
                print("D pressed")
                drive_speed_motor_one = -150
                drive_speed_motor_two  = -150
            
            elif keyboard.is_pressed('f'):#後退
                print("F pressed")
                drive_speed_motor_one = -110
                drive_speed_motor_two  = -110

            elif keyboard.is_pressed('h'):#後退
                print("H pressed")
                drive_speed_motor_one = -90
                drive_speed_motor_two  = -90

            elif keyboard.is_pressed('g'):#左回転
                print("G pressed")
                drive_speed_motor_one = -200
                drive_speed_motor_two  = -200

            elif keyboard.is_pressed('z'):#右回転
                print("Z pressed")
                drive_speed_motor_one = 200
                drive_speed_motor_two  = 200

            else:
                drive_speed_motor_one = 0
                drive_speed_motor_two  = 0

            controller.send_command(cmds.DUAL_DRIVE, drive_speed_motor_one, drive_speed_motor_two)
            #print(motor_rpm)
            print(motor_amps)

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    move()