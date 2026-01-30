from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import math

# ==============================
# パラメータ
# ==============================
PORT = "COM3"
MOTOR_CMD = -100          # 調べたいモータコマンド
MEASURE_TIME = 5.0       # 計測時間 [s]
DT = 0.1                 # サンプリング周期 [s]

WHEEL_RADIUS = 0.13      # [m]
GEAR_RATIO = 25          # 減速比

# ==============================
# 初期化
# ==============================
controller = RoboteqHandler()
controller.connect(PORT)
controller.send_command(cmds.REL_EM_STOP)

# ==============================
# 計測開始
# ==============================
print("Motor command =", MOTOR_CMD)

# 両輪同時に駆動
controller.send_command(cmds.GO, 1, MOTOR_CMD)
controller.send_command(cmds.GO, 2, MOTOR_CMD)

rpm_log_1 = []
rpm_log_2 = []

start_time = time.time()

while time.time() - start_time < MEASURE_TIME:
    raw1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
    raw2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

    if isinstance(raw1, str) and '=' in raw1:
        rpm1 = float(raw1.split('=')[-1])
        rpm_log_1.append(rpm1)

    if isinstance(raw2, str) and '=' in raw2:
        rpm2 = float(raw2.split('=')[-1])
        rpm_log_2.append(rpm2)

    print(f"RPM1: {rpm1:.2f} , RPM2: {rpm2:.2f}")
    time.sleep(DT)

# ==============================
# 停止
# ==============================
controller.send_command(cmds.GO, 1, 0)
controller.send_command(cmds.GO, 2, 0)

# ==============================
# 結果計算
# ==============================
if len(rpm_log_1) > 0 and len(rpm_log_2) > 0:
    avg_motor_rpm_1 = sum(rpm_log_1) / len(rpm_log_1)
    avg_motor_rpm_2 = sum(rpm_log_2) / len(rpm_log_2)
    avg_motor_rpm = (avg_motor_rpm_1 + avg_motor_rpm_2) / 2

    # モータRPM → 車輪RPM
    wheel_rpm = avg_motor_rpm / GEAR_RATIO

    # 車輪RPM → 実速度 [m/s]
    wheel_rad_s = wheel_rpm * 2 * math.pi / 60
    linear_speed = wheel_rad_s * WHEEL_RADIUS

    print("\n===== RESULT =====")
    print(f"Motor RPM (L)     : {avg_motor_rpm_1:.2f} rpm")
    print(f"Motor RPM (R)     : {avg_motor_rpm_2:.2f} rpm")
    print(f"Motor RPM (avg)   : {avg_motor_rpm:.2f} rpm")
    print(f"Wheel RPM         : {wheel_rpm:.2f} rpm")
    print(f"Linear speed      : {linear_speed:.3f} m/s")
else:
    print("RPMデータが取得できませんでした")