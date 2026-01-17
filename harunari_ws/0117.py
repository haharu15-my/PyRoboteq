from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

class StuckDetector:
    def __init__(self, port="COM3"):
        # ===== パラメータ =====
        self.RPM_THRESHOLD = 5
        self.RPM_STUCK_TIME = 1.0
        self.AMP_WINDOW_TIME = 10.0      # 電流を見る時間[s]
        self.AMP_VARIATION = 3.0         # 平均偏差判定[A]

        # ===== 状態変数 =====
        self.rpm_stop_start = None
        self.amp_window_start = None
        self.amp_buffer1 = []
        self.amp_buffer2 = []
        self.stuck_flag1 = False
        self.stuck_flag2 = False

        # ===== モータ接続 =====
        self.controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
        self.connected = self.controller.connect(port)
        if self.connected:
            self.controller.send_command(cmds.REL_EM_STOP)

    def read_sensors(self):
        """RPMと電流を取得し、floatに変換"""
        try:
            rpm1 = float(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1))
            rpm2 = float(self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 2))
            amps1 = float(self.controller.read_value(cmds.READ_MOTOR_AMPS, 1))
            amps2 = float(self.controller.read_value(cmds.READ_MOTOR_AMPS, 2))
            return abs(rpm1), abs(rpm2), abs(amps1), abs(amps2)
        except (TypeError, ValueError):
            return None, None, None, None

    def update_drive(self):
        """キーボード入力に応じて速度指令"""
        if keyboard.is_pressed('w'):
            return -100, -100, True
        if keyboard.is_pressed('s'):
            return 100, 100, True
        return 0, 0, False

    def update_rpm_flag(self, rpm1, rpm2, driving):
        """回転停止検知 flag1"""
        if driving and rpm1 < self.RPM_THRESHOLD and rpm2 < self.RPM_THRESHOLD:
            if self.rpm_stop_start is None:
                self.rpm_stop_start = time.time()
            elif time.time() - self.rpm_stop_start >= self.RPM_STUCK_TIME:
                self.stuck_flag1 = True
        else:
            self.rpm_stop_start = None
            self.stuck_flag1 = False

    def update_amp_flag(self, amps1, amps2, driving):
        """電流張り付き検知 flag2（平均偏差方式）"""
        if driving:
            if self.amp_window_start is None:
                self.amp_window_start = time.time()
                self.amp_buffer1 = []
                self.amp_buffer2 = []

            self.amp_buffer1.append(amps1)
            self.amp_buffer2.append(amps2)

            if time.time() - self.amp_window_start >= self.AMP_WINDOW_TIME:
                mean1 = sum(self.amp_buffer1)/len(self.amp_buffer1)
                mean2 = sum(self.amp_buffer2)/len(self.amp_buffer2)
                deviation1 = max(abs(a - mean1) for a in self.amp_buffer1)
                deviation2 = max(abs(a - mean2) for a in self.amp_buffer2)
                self.stuck_flag2 = deviation1 < self.AMP_VARIATION and deviation2 < self.AMP_VARIATION

                # バッファ初期化
                self.amp_window_start = None
                self.amp_buffer1 = []
                self.amp_buffer2 = []
        else:
            self.amp_window_start = None
            self.amp_buffer1 = []
            self.amp_buffer2 = []
            self.stuck_flag2 = False

    def run(self):
        """メインループ"""
        if not self.connected:
            print("Controller not connected.")
            return

        while True:
            try:
                rpm1, rpm2, amps1, amps2 = self.read_sensors()
                if rpm1 is None:
                    continue

                drive1, drive2, driving = self.update_drive()
                self.controller.send_command(cmds.DUAL_DRIVE, drive1, drive2)

                self.update_rpm_flag(rpm1, rpm2, driving)
                self.update_amp_flag(amps1, amps2, driving)

                print(f"RPM1:{rpm1:.1f} RPM2:{rpm2:.1f} "
                      f"AMP1:{amps1:.1f} AMP2:{amps2:.1f} "
                      f"flag1:{self.stuck_flag1} flag2:{self.stuck_flag2}")

                if self.stuck_flag1 and self.stuck_flag2:
                    print("STUCK DETECTED")

                time.sleep(0.05)

            except KeyboardInterrupt:
                print("Program stopped by user.")
                break

if __name__ == "__main__":
    detector = StuckDetector(port="COM3")
    detector.run()
