from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

class StuckRecovery:
    def __init__(self, port="COM3"):
        # ===== パラメータ =====
        self.RPM_THRESHOLD = 5
        self.AMP_WINDOW_TIME = 0.1
        self.AMP_VARIATION = 3.0

        self.NORMAL_SPEED = -100
        self.RECOVERY_SPEED = -130
        self.STUCK_RECOVERY_BOOST = -130   # 片輪STUCK時に追加で加える速度
        self.RECOVERY_TIME = 8.0
        self.STUCK_CONFIRM_TIME = 8.0 # ８秒間スタック状態なら回復運動させるため

        # ===== 状態 =====
        self.state = "NORMAL"  # NORMAL, STUCK, RECOVERY, ERROR_STOP
        self.rpm_stop_start = None
        self.stuck_confirm_start = None
        self.recovery_start = None
        self.amp_buffer1 = []
        self.amp_buffer2 = []
        self.stuck_flag1 = False
        self.stuck_flag2 = False

        # ===== コントローラ =====
        self.controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
        self.connected = self.controller.connect(port)
        if self.connected:
            self.controller.send_command(cmds.REL_EM_STOP)

    def parse_sensor_value(self, val):
        try:
            if isinstance(val, str) and '=' in val:
                val = val.split('=')[-1]
            return abs(float(val))
        except:
            return 0.0

    def read_sensors(self):
        rpm1 = self.parse_sensor_value(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1))
        rpm2 = self.parse_sensor_value(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 2))
        amps1 = self.parse_sensor_value(self.controller.read_value(cmds.READ_MOTOR_AMPS, 1))
        amps2 = self.parse_sensor_value(self.controller.read_value(cmds.READ_MOTOR_AMPS, 2))
        return rpm1, rpm2, amps1, amps2

    def get_manual_drive(self):
        if keyboard.is_pressed('w'):
            return self.NORMAL_SPEED, self.NORMAL_SPEED, True
        elif keyboard.is_pressed('s'):
            return 200, 200, True
        else:
            return 0, 0, False

    def run(self):
        print("Starting loop...")
        while self.connected:
            try:
                rpm1, rpm2, amps1, amps2 = self.read_sensors()
                now = time.time()
                drive1 = drive2 = 0
                driving = False

                # ===== 手動走行入力取得 =====
                drive1, drive2, driving = self.get_manual_drive()

                # ===== STUCK判定（手動運転中のみ） =====
                if driving:
                    rpm_stuck1 = abs(rpm1) < self.RPM_THRESHOLD
                    rpm_stuck2 = abs(rpm2) < self.RPM_THRESHOLD

                    self.amp_buffer1.append((now, amps1))
                    self.amp_buffer2.append((now, amps2))
                    self.amp_buffer1 = [(t,a) for t,a in self.amp_buffer1 if now-t <= self.AMP_WINDOW_TIME]
                    self.amp_buffer2 = [(t,a) for t,a in self.amp_buffer2 if now-t <= self.AMP_WINDOW_TIME]
                    amp_stuck1 = max([a for t,a in self.amp_buffer1], default=0) - min([a for t,a in self.amp_buffer1], default=0) < self.AMP_VARIATION
                    amp_stuck2 = max([a for t,a in self.amp_buffer2], default=0) - min([a for t,a in self.amp_buffer2], default=0) < self.AMP_VARIATION

                    self.stuck_flag1 = rpm_stuck1 and amp_stuck1
                    self.stuck_flag2 = rpm_stuck2 and amp_stuck2
                else:
                    self.stuck_flag1 = False
                    self.stuck_flag2 = False
                    self.stuck_confirm_start = None
                    self.amp_buffer1.clear()
                    self.amp_buffer2.clear()

                # ===== 状態遷移 =====
                if self.state == "NORMAL":
                    if driving and (self.stuck_flag1 or self.stuck_flag2):
                        if self.stuck_confirm_start is None:
                            self.stuck_confirm_start = now
                            print("STUCK detected → confirming...")

                    if self.stuck_confirm_start and (now - self.stuck_confirm_start >= self.STUCK_CONFIRM_TIME):
                        print("STUCK confirmed → RECOVERY MODE")
                        self.state = "RECOVERY"
                        self.recovery_start = now
                        self.stuck_confirm_start = None

                elif self.state == "RECOVERY":
                    # 通常RECOVERY速度
                    drive1 = drive2 = self.RECOVERY_SPEED

                    # 片輪STUCK時はBOOST加算
                    if self.stuck_flag1:
                        drive1 += self.STUCK_RECOVERY_BOOST
                    if self.stuck_flag2:
                        drive2 += self.STUCK_RECOVERY_BOOST

                    # RECOVERY完了判定（時間経過のみ）
                    if now - self.recovery_start >= self.RECOVERY_TIME:
                        print("RECOVERY finished → NORMAL")
                        self.state = "NORMAL"
                        self.recovery_start = None

                elif self.state == "ERROR_STOP":
                    drive1 = drive2 = 0
                    print("SYSTEM HALTED (SAFE STOP)")

                # ===== 指令送信 =====
                self.controller.send_command(cmds.DUAL_DRIVE, drive1, drive2)

                # ===== デバッグ表示 =====
                print(f"STATE:{self.state}|RPM1:{rpm1:.1f} RPM2:{rpm2:.1f}|AMP1:{amps1:.1f} AMP2:{amps2:.1f}|STUCK1:{self.stuck_flag1} STUCK2:{self.stuck_flag2}|DRIVE1:{drive1} DRIVE2:{drive2}")

                time.sleep(0.05)

            except KeyboardInterrupt:
                self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                print("Interrupted, stopping...")
                break

if __name__ == "__main__":
    detector = StuckRecovery("COM3")
    print("Connected:", detector.connected)
    detector.run()


