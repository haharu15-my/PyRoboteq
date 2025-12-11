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
    while True:
        #motor_rpm = controller.read_value(cmds.READ_BL_MOTOR_RPM) 速度取得
        current_speed_motor1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)  
        current_speed_motor2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

        if keyboard.is_pressed('d'):
            #print("S pressed")
            drive_speed_motor_one = -200
            drive_speed_motor_two  = -200

            if current_speed_motor1 == 0 and current_speed_motor2 == 0:

                drive_speed_motor_one = -300
                drive_speed_motor_two  = -300
                print("-300")
                print("-300")
            
        if keyboard.is_pressed('s'):
            #print("S pressed")
            drive_speed_motor_one = 0
            drive_speed_motor_two  = 0

        
        controller.send_command(cmds.DUAL_DRIVE,drive_speed_motor_one, drive_speed_motor_two)
#制作途中