from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

controller = RoboteqHandler()
connected = controller.connect("COM3")

controller.send_command(cmds.REL_EM_STOP)# 電子緊急停止を解除

if __name__ == "__main__":
    while connected:
        speed1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)  
        speed2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

        

        if speed1 == 0 and speed2 == 0:

            controller.send_command(cmds.GO_TORQUE, 1, 124)  # モーター1を12.4Aのトルクを設定  
            controller.send_command(cmds.GO_TORQUE, 2, 124)  # モーター2を12.4Aのトルクを設定
            time.sleep(0.05) 
            
        controller.send_command(cmds.DUAL_DRIVE,speed1, speed2)
        
#制作途中