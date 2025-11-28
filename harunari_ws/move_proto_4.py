from PyRoboteq import RoboteqHandler, roboteq_commands as cmds
import time

controller = RoboteqHandler(debug_mode=True)  # デバッグONで通信確認
controller.connect("COM3")

# トルク指令
controller.send_command(cmds.GO_TORQUE, 1, 90)
time.sleep(0.5)

# 電流読み取り
response = controller.send_command(cmds.READ_MOTOR_AMPS, 1)
print("Raw response:", response)

