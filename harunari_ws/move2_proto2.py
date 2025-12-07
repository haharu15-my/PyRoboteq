from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

controller = RoboteqHandler()
connected = controller.connect("COM3")

controller.send_command(cmds.REL_EM_STOP)# 電子緊急停止を解除

if __name__ == "__main__":
    print("Press D to drive")
    print("Press S to stop")
    while connected:
        speed1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)  
        speed2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

        if keyboard.is_pressed('d'):
            #print("S pressed")
            drive_speed_motor_one = -200
            drive_speed_motor_two  = -200
            current_speed_motor1 = -200
            current_speed_motor2 =- 200

            if current_speed_motor1 == 0 and current_speed_motor2 == 0:

                controller.send_command(cmds.GO_TORQUE, 1, 120)  # モーター1を12.4Aのトルクを設定  
                controller.send_command(cmds.GO_TORQUE, 2, 120)  # モーター2を12.4Aのトルクを設定
                print("Torque applied")
                time.sleep(0.05)  # 少し待つ
            
        if keyboard.is_pressed('s'):
            #print("S pressed")
            drive_speed_motor_one = 0
            drive_speed_motor_two  = 0

        
        controller.send_command(cmds.DUAL_DRIVE,drive_speed_motor_one, drive_speed_motor_two)
        #motor_rpm = controller.read_value(cmds.READ_BL_MOTOR_RPM)# RPMで速度を読み取る
        #motor_speed = controller.read_value(cmds.READ_BLRSPEED)# または最大RPMの相対値で読み取る

        #print(motor_rpm)
        #print(motor_speed)
#制作途中