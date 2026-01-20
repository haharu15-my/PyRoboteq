from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

class StuckDetector:
    def __init__(self, port="COM3"):
        # ===== パラメータ =====
        self.RPM_THRESHOLD = 5
        self.RPM_STUCK_TIME = 1.0
        self.AMP_WINDOW_TIME = 0.1 #元は2秒
        self.AMP_VARIATION = 3.0

        self.NORMAL_SPEED = -100
        self.RECOVERY_SPEED = -120
        self.RECOVERY_TIME = 5.0

        self.STUCK_CONFIRM_TIME = 1.0 #２秒間スタック状態なら回復運動させるため
        self.stuck_confirm_start = None
        self.recovery_start = None



        # ===== 状態 =====
        self.state = "NORMAL"   # NORMAL,STUCK, RECOVERY, ERROR_STOP
        self.rpm_stop_start = None
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
        if isinstance(val, str) and '=' in val:
            val = val.split('=')[-1]
        try:
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

                # ===== 状態ごとの駆動 =====
                if self.state == "NORMAL":
                    drive1, drive2, driving = self.get_manual_drive()

                elif self.state == "RECOVERY":
                    drive1 = self.RECOVERY_SPEED
                    drive2 = self.RECOVERY_SPEED
                    driving = True

                    # ----- 回復時間経過後に判定（RECOVERY中のみ） -----
                    if now - self.recovery_start >= self.RECOVERY_TIME:
                        if rpm1 > self.RPM_THRESHOLD or rpm2 > self.RPM_THRESHOLD:
                            print("RECOVERY SUCCESS → NORMAL")
                            self.state = "NORMAL"
                            self.recovery_start = None
                        else:
                            print("RECOVERY FAILED → SAFE STOP")
                            self.state = "ERROR_STOP"

                elif self.state == "ERROR_STOP":
                    self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                    print("SYSTEM HALTED (SAFE STOP)")
                    break

                self.controller.send_command(cmds.DUAL_DRIVE, drive1, drive2)

                # ===== RPM停止 =====
                if driving and rpm1 < self.RPM_THRESHOLD and rpm2 < self.RPM_THRESHOLD:
                    if self.rpm_stop_start is None:
                        self.rpm_stop_start = now
                    elif now - self.rpm_stop_start >= self.RPM_STUCK_TIME:
                        self.stuck_flag1 = True
                else:
                    self.rpm_stop_start = None
                    self.stuck_flag1 = False

                # ===== AMP張り付き =====
                if driving:
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

                # ===== STUCK 判定（確定待ち付き）=====
                if self.state == "NORMAL" and self.stuck_flag1 and self.stuck_flag2:
                    if self.stuck_confirm_start is None:
                        self.stuck_confirm_start = now
                        self.state = "STUCK"

                elif self.state == "STUCK":
                    if self.stuck_flag1 and self.stuck_flag2:
                        if now - self.stuck_confirm_start >= self.STUCK_CONFIRM_TIME:
                            print("STUCK confirmed → RECOVERY MODE")
                            self.state = "RECOVERY"
                            self.recovery_start = now
                            self.stuck_confirm_start = None
                    else:
                        print("STUCK released → NORMAL")
                        self.state = "NORMAL"
                        self.stuck_confirm_start = None

                print(f"STATE:{self.state} | "f"RPM1:{rpm1:.1f}RPM2:{rpm2:.1f}|"f"AMP1:{amps1:.1f}AMP2:{amps2:.1f}")

                self.prev_rpm1 = rpm1
                self.prev_rpm2 = rpm2
                time.sleep(0.05)

            except KeyboardInterrupt:
                self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                break

if __name__ == "__main__":
    detector = StuckDetector("COM3")
    print("Connected:", detector.connected)
    detector.run()

#失敗した時のプログラムの起動も確認した
#kaihuku OK