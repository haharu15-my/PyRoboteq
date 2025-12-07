from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard # Siriusに入っているので接続しない時にエラーが出るのは当たり前

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False) 
connected = controller.connect("/dev/roboteq") # Insert your COM port (for windows) or /dev/tty{your_port} (Commonly /dev/ttyACM0) for linux.
controller.send_command(cmds.REL_EM_STOP) # 電子緊急停止を強制的に解除

if __name__ == "__main__":
    while connected:
        try:
            motor_rpm = controller.read_value(cmds.READ_BL_MOTOR_RPM)# RPMで速度を読み取る
            motor_speed = controller.read_value(cmds.READ_BLRSPEED)# または最大RPMの相対値で読み取る

            print(motor_rpm)
            print(motor_speed)

        except KeyboardInterrupt:
            break