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
            try:
                if isinstance(speed_motor1, str):
                    speed_motor1 = speed_motor1.split('=')[-1]
                if isinstance(speed_motor2, str):
                    speed_motor2 = speed_motor2.split('=')[-1]

                rpm1 = float(speed_motor1)
                rpm2 = float(speed_motor2)
            except (TypeError, ValueError):
                continue

            if keyboard.is_pressed('w'):#前進
                print("W pressed")
                drive_speed_motor_one = -100
                drive_speed_motor_two = -100
                print(f"RPM1:{rpm1} RPM2:{rpm2}")

                # --- スタック判定（簡易） ---
                if abs(rpm1) < 5 and abs(rpm2) < 5:
                    print("STUCK DETECTED")
            
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

    #成功