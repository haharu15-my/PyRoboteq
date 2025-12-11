from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

class MotorController:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)  # 電子緊急停止を解除

    def drive(self, speed_motor_one, speed_motor_two):
        self.controller.send_command(cmds.DUAL_DRIVE, speed_motor_one, speed_motor_two)

    def read_motor_speeds(self):
        speed_motor1 = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        speed_motor2 = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)
        return speed_motor1, speed_motor2
    
    def move_loop(self):
        if not self.connected:
            print("Controller not connected.")
            return
        
        print("Press D to drive")
        print("Press S to stop")
        
        while self.connected:
            current_speed_motor1, current_speed_motor2 = self.read_motor_speeds()
            drive_speed_motor_one = 0
            drive_speed_motor_two = 0

            if keyboard.is_pressed('d'):
                drive_speed_motor_one = -200
                drive_speed_motor_two = -200

                if current_speed_motor1 == 0 and current_speed_motor2 == 0:
                    drive_speed_motor_one = -300
                    drive_speed_motor_two = -300
                    print("-300")
                    print("-300")
                
            if keyboard.is_pressed('s'):
                drive_speed_motor_one = 0
                drive_speed_motor_two = 0

            self.drive(drive_speed_motor_one, drive_speed_motor_two)