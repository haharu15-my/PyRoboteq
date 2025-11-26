from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard # to run this library you need to be on root (run this python script as sudo)

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False) 
connected = controller.connect("COM3") # Insert your COM port (for windows) or /dev/tty{your_port} (Commonly /dev/ttyACM0) for linux.
controller.send_command(cmds.REL_EM_STOP) # 電子緊急停止を強制的に解除

if __name__ == "__main__":
    while connected:
        try:
            motor_rpm = controller.read_value(cmds.READ_BL_MOTOR_RPM)# RPMで速度を読み取る
            motor_speed = controller.read_value(cmds.READ_BLRSPEED)# または最大RPMの相対値で読み取る

            if keyboard.is_pressed('w'):
                print("W pressed")
                drive_speed_motor_one = -200
                drive_speed_motor_two = -200

            elif keyboard.is_pressed('s'):
                print("S pressed")
                drive_speed_motor_one = 200
                drive_speed_motor_two = 200

            elif keyboard.is_pressed('a'):
                print("A is pressed")
                drive_speed_motor_one = -200
                drive_speed_motor_two = 200

            elif keyboard.is_pressed('d'):
                print("D is pressed")
                drive_speed_motor_one = 200
                drive_speed_motor_two = -200

            # Motor will automatically stop if no command is sent.
            else:
                drive_speed_motor_one = 0
                drive_speed_motor_two = 0

            controller.send_command(cmds.DUAL_DRIVE, drive_speed_motor_one, drive_speed_motor_two)
            print(motor_rpm)
            print(motor_speed)

        except KeyboardInterrupt:
            break