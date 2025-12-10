from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

controller = RoboteqHandler()
connected = controller.connect("COM3")

controller.send_command(cmds.REL_EM_STOP)


drive_speed_motor_one = 0
drive_speed_motor_two = 0

def read_rpm(ch, retry=3):
    """BS=0:0 を安定して取得するための読み取り関数"""
    for _ in range(retry):
        raw = controller.read_value(cmds.READ_BL_MOTOR_RPM, ch)
        if raw is None:
            continue
        try:
            raw = raw.replace("BS=", "")
            left, right = raw.split(":")
            return int(right)
        except:
            continue
    return 0   # ← Noneなら停止扱いにする！


RPM_DEAD_ZONE = 5

if __name__ == "__main__":
    print("Press D to drive")
    print("Press S to stop")

    while connected:
        speed1 = read_rpm(1)
        speed2 = read_rpm(2)

        print(speed1, speed2)

        if keyboard.is_pressed('d'):
            drive_speed_motor_one = -100
            drive_speed_motor_two = -100

            # ★ None ではなく 0 に変換されるので確実に判定できる
            if abs(speed1) < RPM_DEAD_ZONE and abs(speed2) < RPM_DEAD_ZONE:
                controller.send_command(cmds.GO_TORQUE, 1, 120)
                controller.send_command(cmds.GO_TORQUE, 2, 120)
                print("Torque applied")

        if keyboard.is_pressed('s'):
            drive_speed_motor_one = 0
            drive_speed_motor_two = 0

        controller.send_command(cmds.DUAL_DRIVE,drive_speed_motor_one,drive_speed_motor_two)
        motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0) 
        print(motor_amps)

