from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time
import math

class KeyboardPControlWithStuck:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        if self.connected:
            self.controller.send_command(cmds.REL_EM_STOP)

        # ===== P制御パラメータ =====
        self.Kp_normal = 0.5
        self.Kp_stuck = 1.0
        self.Kp = self.Kp_normal

        self.WHEEL_RADIUS = 0.13  # m
        self.GEAR_RATIO = 25
        self.dt = 0.05

        self.target_speed = 0.0  # m/s

        # ===== スタック判定パラメータ =====
        self.RPM_THRESHOLD = 5
        self.RPM_STUCK_TIME = 1.0
        self.AMP_WINDOW_TIME = 0.1
        self.AMP_VARIATION = 3.0
        self.STUCK_CONFIRM_TIME = 2.0

        self.recovery_start = None
        self.stuck_confirm_start = None

        self.amp_buffer1 = []
        self.amp_buffer2 = []
        self.rpm_stop_start = None
        self.stuck_flag1 = False
        self.stuck_flag2 = False

        self.state = "NORMAL"

    # ===== センサ値取得 =====
    def parse_sensor_value(self, val):
        if isinstance(val, str) and '=' in val:
            val = val.split('=')[-1]
        try:
            return float(val)
        except:
            return 0.0

    def read_sensors(self):
        rpm1 = self.parse_sensor_value(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1))
        rpm2 = self.parse_sensor_value(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 2))
        amps1 = self.parse_sensor_value(self.controller.read_value(cmds.READ_MOTOR_AMPS, 1))
        amps2 = self.parse_sensor_value(self.controller.read_value(cmds.READ_MOTOR_AMPS, 2))
        return rpm1, rpm2, amps1, amps2

    def read_actual_speed(self, rpm_motor):
        # モータRPM → ホイール回転速度 → m/s
        wheel_rpm = rpm_motor / self.GEAR_RATIO
        speed = (2 * math.pi * self.WHEEL_RADIUS * wheel_rpm) / 60.0
        return speed  # 正負そのまま

    # ===== キーボード指令 =====
    def update_target(self):
        if keyboard.is_pressed("w"):
            self.target_speed = -0.1
        elif keyboard.is_pressed("s"):
            self.target_speed = 0.2
        else:
            self.target_speed = 0.0

    # ===== スタック判定 =====
    def check_stuck(self, rpm1, rpm2, amps1, amps2):
        now = time.time()

        # RPM停止判定
        if rpm1 < self.RPM_THRESHOLD and rpm2 < self.RPM_THRESHOLD and self.target_speed != 0.0:
            if self.rpm_stop_start is None:
                self.rpm_stop_start = now
            elif now - self.rpm_stop_start >= self.RPM_STUCK_TIME:
                self.stuck_flag1 = True
        else:
            self.rpm_stop_start = None
            self.stuck_flag1 = False

        # 電流張り付き判定
        if self.target_speed != 0.0:
            self.amp_buffer1.append((now, amps1))
            self.amp_buffer2.append((now, amps2))
            self.amp_buffer1 = [(t,a) for t,a in self.amp_buffer1 if now-t <= self.AMP_WINDOW_TIME]
            self.amp_buffer2 = [(t,a) for t,a in self.amp_buffer2 if now-t <= self.AMP_WINDOW_TIME]
            a1 = [a for t,a in self.amp_buffer1]
            a2 = [a for t,a in self.amp_buffer2]
            self.stuck_flag2 = (max(a1)-min(a1) < self.AMP_VARIATION) and \
                               (max(a2)-min(a2) < self.AMP_VARIATION)
        else:
            self.amp_buffer1.clear()
            self.amp_buffer2.clear()
            self.stuck_flag2 = False

        # スタック確定
        if self.state == "NORMAL" and self.stuck_flag1 and self.stuck_flag2:
            if self.stuck_confirm_start is None:
                self.stuck_confirm_start = now
                self.state = "STUCK"
        elif self.state == "STUCK":
            if self.stuck_flag1 and self.stuck_flag2:
                if now - self.stuck_confirm_start >= self.STUCK_CONFIRM_TIME:
                    self.state = "RECOVERY"
                    self.Kp = self.Kp_stuck
                    self.recovery_start = now
                    self.stuck_confirm_start = None
                    print("STUCK confirmed → Kp increased")
            else:
                self.state = "NORMAL"
                self.stuck_confirm_start = None
                self.Kp = self.Kp_normal

        # 回復後にKp元に戻す
        if self.state == "RECOVERY" and now - self.recovery_start >= 3.0:
            self.Kp = self.Kp_normal
            self.state = "NORMAL"

    # ===== メインループ =====
    def run(self):
        try:
            while self.connected:
                self.update_target()
                rpm1, rpm2, amps1, amps2 = self.read_sensors()

                # 実速度計算（平均でP制御）
                act_speed1 = self.read_actual_speed(rpm1)
                act_speed2 = self.read_actual_speed(rpm2)
                act_speed = (act_speed1 + act_speed2) / 2.0

                # ===== P制御（m/s単位）=====
                err = self.target_speed - act_speed
                cmd_speed_m_s = self.target_speed + self.Kp * err  # ← m/s単位のまま

                # ===== CMD変換（前進は負、後退は正）=====
                cmd = int(cmd_speed_m_s * 1000)
                cmd = max(min(cmd, 1000), -1000)

                # スタック判定
                self.check_stuck(rpm1, rpm2, amps1, amps2)

                # CMD送信
                self.controller.send_command(cmds.DUAL_DRIVE, cmd, cmd)

                print(f"STATE:{self.state} | TARGET:{self.target_speed:+.2f} "
                      f"ACT:{act_speed:+.2f} ERR:{err:+.2f} CMD:{cmd} "
                      f"RPM1:{rpm1:.1f} RPM2:{rpm2:.1f} AMP1:{amps1:.1f} AMP2:{amps2:.1f}")

                time.sleep(self.dt)

        except KeyboardInterrupt:
            self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
            print("制御停止")

if __name__ == "__main__":
    ctrl = KeyboardPControlWithStuck("COM3")
    print("Connected:", ctrl.connected)
    ctrl.run()
