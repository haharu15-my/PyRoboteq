from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

if __name__ == "__main__":
    while connected:
        try:
            motor_rpm = controller.read_value(cmds.READ_BL_MOTOR_RPM)
            speed_motor1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
            speed_motor2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

            if keyboard.is_pressed('w'):#前進
                print("W pressed")
                drive_speed_motor_one = -100
                drive_speed_motor_two = -100
                print(motor_rpm)
                print(speed_motor1, speed_motor2)
            
            elif keyboard.is_pressed('s'):#後退
                print("S pressed")
                drive_speed_motor_one = 100
                drive_speed_motor_two = 100

            elif keyboard.is_pressed('x'):#左回転
                print("A is pressed")
                drive_speed_motor_one = 200
                drive_speed_motor_two = 200

            else:
                drive_speed_motor_one = 0
                drive_speed_motor_two = 0

            controller.send_command(cmds.DUAL_DRIVE, drive_speed_motor_one, drive_speed_motor_two)

        except KeyboardInterrupt:
            break