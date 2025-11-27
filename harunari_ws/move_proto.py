from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

controller = RoboteqHandler()
connected = controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

if __name__ == "__main__":
    print("Press D to drive")
    print("Press S to stop")
    while connected:
        speed1 = controller.read_value(cmds.READ_SPEED, 1)  
        speed2 = controller.read_value(cmds.READ_SPEED, 2)

        if keyboard.is_pressed('d'):
            #print("S pressed")
            drive_speed_motor_one = -200
            drive_speed_motor_two  = -200
            current_speed_motor1 = -200
            current_speed_motor2 =- 200

            if current_speed_motor1 == 0 and current_speed_motor2 == 0:

                controller.send_command(cmds.GO_TORQUE, 1, 1240)  # モーター1を12.4Aのトルクを設定  
                controller.send_command(cmds.GO_TORQUE, 2, 1240)  # モーター2を12.4Aのトルクを設定 
            
        if keyboard.is_pressed('s'):
            #print("S pressed")
            drive_speed_motor_one = 0
            drive_speed_motor_two  = 0

        
        controller.send_command(cmds.DUAL_DRIVE,drive_speed_motor_one, drive_speed_motor_two)
        motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0)
        print(motor_amps)
#制作途中            

        
        

