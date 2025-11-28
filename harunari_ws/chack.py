from PyRoboteq import RoboteqHandler, roboteq_commands as cmds
import time

controller = RoboteqHandler(debug_mode=True)
controller.connect("COM3")

# トルクを与える
controller.send_command(cmds.GO_TORQUE, 1, 10)
time.sleep(0.5)

# BL 電流チェック
print("Current (AM):", controller.send_command("?AM 1"))#Tx:?AM 1 + Rx:b'AM=xxx\r'なら成功

# BL 回転数チェック
print("RPM:", controller.send_command(cmds.READ_BL_MOTOR_RPM, 1))#RPM が数値を返せば GO_TORQUE が確実に動作しています。

""""
from PyRoboteq import RoboteqHandler, roboteq_commands as cmds
import time

# ==========================
# 初期設定
# ==========================
controller = RoboteqHandler(debug_mode=True)  # デバッグONで通信確認
connected = controller.connect("COM3")        # 接続ポートを確認

if not connected:
    print("Controller not connected. Check COM port.")
    exit()

# ==========================
# 安全パラメータ
# ==========================
motor_channel = 1   # モーター番号
safe_torque = 5     # 低トルクで安全確認
test_duration = 2   # 秒

# ==========================
# モーター指令
# ==========================
print(f"Sending low torque ({safe_torque}) to motor {motor_channel} for {test_duration}s")
controller.send_command(cmds.GO_TORQUE, motor_channel, safe_torque)

# 指令後のモーター反応確認
start_time = time.time()
while time.time() - start_time < test_duration:
    rpm = controller.send_command(cmds.READ_BL_MOTOR_RPM, motor_channel)
    current = controller.send_command("?AM 1")  # ブラシレス用モーター電流
    print(f"Motor {motor_channel} RPM: {rpm}, Current: {current}")
    time.sleep(0.5)

# ==========================
# モーター停止
# ==========================
controller.send_command(cmds.REL_EM_STOP)  # トルク解除
print("Test completed, motor stopped.")

"""
