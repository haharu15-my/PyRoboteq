from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

class StuckPIController:
    def __init__(self, port="COM3"):
        # ===== PI制御パラメータ =====
        self.Kp_normal = 400.0
        self.Ki_normal = 50.0

        self.Kp_recovery = 700.0
        self.Ki_recovery = 120.0

        self.integral_error = 0.0
        self.dt = 0.05

        self.CMD_MAX_NORMAL = 300
        self.CMD_MAX_RECOVERY = 800

        # ===== 速度系 =====
        self.MAX_SPEED_MS = 1.0          # -1000 = 1.0 m/s
        self.target_speed_ms = 0.0

        # ===== スタック検知 =====
        self.RPM_THRESHOLD = 5
        self.RPM_STUCK_TIME = 1.0
        self.AMP_WINDOW_TIME = 0.1
        self.AMP_VARIATION = 3.0
        self.STUCK_CONFIRM_TIME = 2.0
        self.RECOVERY_TIME = 5.0

        self.state = "NORMAL"
        self.rpm_stop_start = None
        self.stuck_confirm_start = None
        self.recovery_start = None

        self.amp_buffer1 = []
        self.amp_buffer2 = []

        # ===== Roboteq =====
        self.controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
        self.connected = self.controller.connect(port)
        if self.connected:
            self.controller.send_command(cmds.REL_EM_STOP)

    # --------------------------
    def parse_val(self, v):
        if isinstance(v, str) and '=' in v:
            v = v.split('=')[-1]
        try:
            return float(v)
        except:
            return 0.0

    def read_sensors(self):
        rpm = abs(self.parse_val(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)))
        amps1 = abs(self.parse_val(self.controller.read_value(cmds.READ_MOTOR_AMPS, 1)))
        amps2 = abs(self.parse_val(self.controller.read_value(cmds.READ_MOTOR_AMPS, 2)))
        speed_ms = rpm / 3000.0  # ★要実機キャリブレーション
        return rpm, speed_ms, amps1, amps2

    # --------------------------
    def keyboard_target(self):
        if keyboard.is_pressed("w"):
            return 0.1
        elif keyboard.is_pressed("s"):
            return -0.1
        else:
            return 0.0

    # --------------------------
    def speed_to_cmd(self, speed_ms):
        return int(speed_ms / self.MAX_SPEED_MS * 1000)

    # --------------------------
    def run(self):
        print("=== START PI + STUCK CONTROL ===")

        while self.connected:
            now = time.time()

            rpm, actual_speed, amp1, amp2 = self.read_sensors()
            self.target_speed_ms = self.keyboard_target()

            # ===== スタック検知 =====
            driving = abs(self.target_speed_ms) > 0.01

            if driving and rpm < self.RPM_THRESHOLD:
                if self.rpm_stop_start is None:
                    self.rpm_stop_start = now
                elif now - self.rpm_stop_start > self.RPM_STUCK_TIME:
                    rpm_stuck = True
                else:
                    rpm_stuck = False
            else:
                rpm_stuck = False
                self.rpm_stop_start = None

            if driving:
                self.amp_buffer1.append((now, amp1))
                self.amp_buffer2.append((now, amp2))
                self.amp_buffer1 = [(t,a) for t,a in self.amp_buffer1 if now-t <= self.AMP_WINDOW_TIME]
                self.amp_buffer2 = [(t,a) for t,a in self.amp_buffer2 if now-t <= self.AMP_WINDOW_TIME]

                a1 = [a for t,a in self.amp_buffer1]
                a2 = [a for t,a in self.amp_buffer2]

                amp_stuck = (max(a1)-min(a1) < self.AMP_VARIATION) and \
                            (max(a2)-min(a2) < self.AMP_VARIATION)
            else:
                amp_stuck = False
                self.amp_buffer1.clear()
                self.amp_buffer2.clear()

            # ===== 状態遷移 =====
            if self.state == "NORMAL" and rpm_stuck and amp_stuck:
                self.state = "STUCK"
                self.stuck_confirm_start = now

            elif self.state == "STUCK":
                if rpm_stuck and amp_stuck:
                    if now - self.stuck_confirm_start > self.STUCK_CONFIRM_TIME:
                        self.state = "RECOVERY"
                        self.recovery_start = now
                else:
                    self.state = "NORMAL"

            elif self.state == "RECOVERY":
                if now - self.recovery_start > self.RECOVERY_TIME:
                    self.state = "ERROR_STOP"

            # ===== PI制御 =====
            if self.state == "RECOVERY":
                Kp = self.Kp_recovery
                Ki = self.Ki_recovery
                CMD_MAX = self.CMD_MAX_RECOVERY
            else:
                Kp = self.Kp_normal
                Ki = self.Ki_normal
                CMD_MAX = self.CMD_MAX_NORMAL

            error = self.target_speed_ms - actual_speed
            self.integral_error += error * self.dt

            cmd = Kp * error + Ki * self.integral_error
            cmd = max(min(cmd, CMD_MAX), -CMD_MAX)

            self.controller.send_command(cmds.DUAL_DRIVE, int(cmd), int(cmd))

            print(
                f"STATE:{self.state} "
                f"TARGET:{self.target_speed_ms:.2f} "
                f"ACT:{actual_speed:.2f} "
                f"ERR:{error:.2f} "
                f"CMD:{int(cmd)}"
            )

            time.sleep(self.dt)

if __name__ == "__main__":
    ctrl = StuckPIController("COM3")
    print("Connected:", ctrl.connected)
    ctrl.run()
# PI制御＋スタック検知・回避制御