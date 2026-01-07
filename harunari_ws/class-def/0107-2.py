from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time

# =========================
# パラメータ
# =========================
TORQUE_CURRENT = 5.0   # 指令トルク（＝電流[A]）
CHANNEL = 1

# =========================
# 接続
# =========================
controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")

if not connected:
    print("Connection failed")
    exit()

# 電子緊急停止解除
controller.send_command(cmds.REL_EM_STOP)

# =========================
# ① 現在の制御モード確認
# =========================
current_mode = controller.read_value(cmds.READ_OPERATING_MODE, CHANNEL)
print("Current Mode:", current_mode)

# =========================
# ② トルクモードへ切り替え
# MMOD = 5（Torque Mode）
# =========================
controller.send_command(cmds.SET_OPERATING_MODE, CHANNEL, 5)
time.sleep(0.1)

# EEPROM保存（任意）
# controller.send_command(cmds.SAVE_TO_EEPROM)

# =========================
# ③ 切り替え確認
# =========================
mode_after = controller.read_value(cmds.READ_OPERATING_MODE, CHANNEL)
print("Mode After Change:", mode_after)

if mode_after != 5:
    print("Torque mode NOT active")
    exit()

print("Torque mode ACTIVE")

# =========================
# ④ トルク指令を出す
# GIQ = Go to Torque (Amps)
# =========================
controller.send_command(cmds.GO_TORQUE, CHANNEL, TORQUE_CURRENT)
print(f"Torque command = {TORQUE_CURRENT} A")

# =========================
# ⑤ 電流・速度確認
# =========================
for _ in range(20):
    current = controller.read_value(cmds.READ_MOTOR_AMPS, CHANNEL)
    speed = controller.read_value(cmds.READ_BL_MOTOR_RPM, CHANNEL)

    print(f"Current={current:.2f} A, Speed={speed:.1f} RPM")
    time.sleep(0.1)

# 停止
controller.send_command(cmds.MOTOR_STOP, CHANNEL)
print("Stop")
