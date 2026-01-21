from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import math

# ===== ロボット定数 =====
WHEEL_RADIUS = 0.13   # [m]
GEAR_RATIO = 25

CMD_TEST = -100       # ← これが 0.1 m/s かを確認したい
DT = 0.1

def rpm_to_speed_ms(motor_rpm):
    wheel_rpm = motor_rpm / GEAR_RATIO
    return (2 * math.pi * WHEEL_RADIUS * wheel_rpm) / 60.0

def parse(val):
    if isinstance(val, str) and '=' in val:
        val = val.split('=')[-1]
    try:
        return float(val)
    except:
        return 0.0

# ===== 接続 =====
controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
controller.connect("COM3")
controller.send_command(cmds.REL_EM_STOP)

print("CMD = -100 を送信中（5秒）")

try:
    for _ in range(50):  # 約5秒
        controller.send_command(cmds.DUAL_DRIVE, CMD_TEST, CMD_TEST)

        rpm1 = parse(controller.read_value(cmds.READ_BL_MOTOR_RPM, 1))
        rpm2 = parse(controller.read_value(cmds.READ_BL_MOTOR_RPM, 2))

        avg_rpm = (rpm1 + rpm2) / 2
        speed_ms = rpm_to_speed_ms(-avg_rpm)  # 符号調整

        print(
            f"CMD:{CMD_TEST} | "
            f"RPM:{avg_rpm:.1f} | "
            f"SPEED:{speed_ms:.3f} m/s"
        )

        time.sleep(DT)

except KeyboardInterrupt:
    pass

finally:
    controller.send_command(cmds.DUAL_DRIVE, 0, 0)
    print("停止")
# CMD = -100 を送信して速度を確認 P制御無し