from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time
import math

# ================= パラメータ =================
CONTROL_DT = 0.05

# --- 速度とパワーの対応（実測ベース） ---
BASE_CMD_01 = -100      # 0.1 m/s
MAX_CMD = 1000

# --- P制御 ---
Kp = 300                # m/s → CMD 変換込み
P_LIMIT = 300           # 補正上限

# --- スタック検知 ---
RPM_THRESHOLD = 5
RPM_STUCK_TIME = 1.0

AMP_WINDOW = 0.1
AMP_VARIATION = 3.0

STUCK_CONFIRM_TIME = 2.0

# --- 回復行動 ---
RECOVERY_CMD = -160
RECOVERY_TIME = 5.0


# ================= クラス =================
class PControlWithStuck:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)

        self.state = "NORMAL"
        self.rpm_stop_start = None
        self.stuck_confirm_start = None
        self.recovery_start = None

        self.amp_buf1 = []
        self.amp_buf2 = []

    # ---------- センサ ----------
    def parse(self, v):
        if isinstance(v, str) and '=' in v:
            v = v.split('=')[-1]
        try:
            return abs(float(v))
        except:
            return 0.0

    def read_sensors(self):
        rpm1 = self.parse(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1))
        rpm2 = self.parse(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 2))
        amp1 = self.parse(self.controller.read_value(cmds.READ_MOTOR_AMPS, 1))
        amp2 = self.parse(self.controller.read_value(cmds.READ_MOTOR_AMPS, 2))
        return rpm1, rpm2, amp1, amp2

    def rpm_to_speed(self, rpm):
        WHEEL_RADIUS = 0.13
        GEAR_RATIO = 25
        wheel_rpm = rpm / GEAR_RATIO
        return (2 * math.pi * WHEEL_RADIUS * wheel_rpm) / 60.0

    # ---------- キーボード ----------
    def get_target_speed(self):
        if keyboard.is_pressed('w'):
            return 0.1
        elif keyboard.is_pressed('s'):
            return -0.1
        else:
            return 0.0

    # ---------- メイン ----------
    def run(self):
        print("=== START P + STUCK CONTROL ===")

        while self.connected:
            try:
                now = time.time()
                rpm1, rpm2, amp1, amp2 = self.read_sensors()

                act_speed = self.rpm_to_speed(-(rpm1 + rpm2) / 2)
                target_speed = self.get_target_speed()

                # ================= 状態処理 =================
                if self.state == "NORMAL":
                    if abs(target_speed) < 0.001:
                        cmd = 0
                    else:
                        base_cmd = BASE_CMD_01 if target_speed > 0 else -BASE_CMD_01
                        error = target_speed - act_speed
                        p = int(Kp * error)
                        p = max(min(p, P_LIMIT), -P_LIMIT)
                        cmd = base_cmd + p

                elif self.state == "RECOVERY":
                    cmd = RECOVERY_CMD
                    if now - self.recovery_start >= RECOVERY_TIME:
                        if rpm1 > RPM_THRESHOLD or rpm2 > RPM_THRESHOLD:
                            print("RECOVERY SUCCESS → NORMAL")
                            self.state = "NORMAL"
                        else:
                            print("RECOVERY FAILED → STOP")
                            self.state = "ERROR_STOP"

                elif self.state == "ERROR_STOP":
                    self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                    print("SYSTEM HALTED")
                    break

                self.controller.send_command(cmds.DUAL_DRIVE, cmd, cmd)

                # ================= スタック検知 =================
                driving = abs(cmd) > 0

                # --- RPM停止 ---
                if driving and rpm1 < RPM_THRESHOLD and rpm2 < RPM_THRESHOLD:
                    if self.rpm_stop_start is None:
                        self.rpm_stop_start = now
                    elif now - self.rpm_stop_start >= RPM_STUCK_TIME:
                        rpm_stuck = True
                else:
                    self.rpm_stop_start = None
                    rpm_stuck = False

                # --- AMP張り付き ---
                if driving:
                    self.amp_buf1.append((now, amp1))
                    self.amp_buf2.append((now, amp2))
                    self.amp_buf1 = [(t,a) for t,a in self.amp_buf1 if now-t <= AMP_WINDOW]
                    self.amp_buf2 = [(t,a) for t,a in self.amp_buf2 if now-t <= AMP_WINDOW]
                    a1 = [a for t,a in self.amp_buf1]
                    a2 = [a for t,a in self.amp_buf2]
                    amp_stuck = (max(a1)-min(a1) < AMP_VARIATION) and \
                                (max(a2)-min(a2) < AMP_VARIATION)
                else:
                    self.amp_buf1.clear()
                    self.amp_buf2.clear()
                    amp_stuck = False

                # --- STUCK確定 ---
                if self.state == "NORMAL" and rpm_stuck and amp_stuck:
                    if self.stuck_confirm_start is None:
                        self.stuck_confirm_start = now
                    elif now - self.stuck_confirm_start >= STUCK_CONFIRM_TIME:
                        print("STUCK → RECOVERY")
                        self.state = "RECOVERY"
                        self.recovery_start = now
                        self.stuck_confirm_start = None
                else:
                    self.stuck_confirm_start = None

                print(
                    f"STATE:{self.state} "
                    f"TGT:{target_speed:+.2f} "
                    f"ACT:{act_speed:+.2f} "
                    f"CMD:{cmd} "
                    f"RPM:{rpm1:.0f}/{rpm2:.0f}"
                )

                time.sleep(CONTROL_DT)

            except KeyboardInterrupt:
                self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                print("STOP")
                break


# ================= 実行 =================
if __name__ == "__main__":
    ctrl = PControlWithStuck("COM3")
    ctrl.run()
