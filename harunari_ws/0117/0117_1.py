from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time

class StuckDetector:
    def __init__(self, port="COM3"):
        # ===== パラメータ =====
        self.RPM_THRESHOLD = 5
        self.RPM_STUCK_TIME = 1.0
        self.AMP_WINDOW_TIME = 2.0   # 秒
        self.AMP_VARIATION = 3.0     # A

        # ===== 状態変数 =====
        self.rpm_stop_start = None
        self.amp_buffer1 = []
        self.amp_buffer2 = []
        self.stuck_flag1 = False
        self.stuck_flag2 = False

        # ===== コントローラ初期化 =====
        self.controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
        self.connected = self.controller.connect(port)
        if self.connected:
            self.controller.send_command(cmds.REL_EM_STOP)

    def parse_sensor_value(self, val):
        """Roboteqの文字列 'BS=-xxx' に対応して float に変換"""
        if isinstance(val, str) and '=' in val:
            val = val.split('=')[-1]
        try:
            return abs(float(val))
        except Exception:
            return 0.0

    def read_sensors(self):
        """RPMとAMPを読み取る"""
        rpm1_raw = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        rpm2_raw = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)
        amps1_raw = self.controller.read_value(cmds.READ_MOTOR_AMPS, 1)
        amps2_raw = self.controller.read_value(cmds.READ_MOTOR_AMPS, 2)

        rpm1 = self.parse_sensor_value(rpm1_raw)
        rpm2 = self.parse_sensor_value(rpm2_raw)
        amps1 = self.parse_sensor_value(amps1_raw)
        amps2 = self.parse_sensor_value(amps2_raw)

        return rpm1, rpm2, amps1, amps2

    def get_drive_command(self):
        """w/sキーによる前進・停止制御"""
        if keyboard.is_pressed('w'):
            return -100, -100, True  # 前進
        elif keyboard.is_pressed('s'):
            return 100, 100, True    # 後退
        else:
            return 0, 0, False       # 停止

    def run(self):
        if not self.connected:
            print("Controller not connected.")
            return

        print("Starting loop...")

        while True:
            try:
                # ===== センサ値取得 =====
                rpm1, rpm2, amps1, amps2 = self.read_sensors()

                # ===== 走行指令 =====
                drive1, drive2, driving = self.get_drive_command()
                self.controller.send_command(cmds.DUAL_DRIVE, drive1, drive2)

                # ===== stuck_flag1: RPM停止 =====
                if driving and rpm1 < self.RPM_THRESHOLD and rpm2 < self.RPM_THRESHOLD:
                    if self.rpm_stop_start is None:
                        self.rpm_stop_start = time.time()
                    elif time.time() - self.rpm_stop_start >= self.RPM_STUCK_TIME:
                        self.stuck_flag1 = True
                else:
                    self.rpm_stop_start = None
                    self.stuck_flag1 = False

                # ===== stuck_flag2: AMP張り付き（移動ウィンドウ判定） =====
                now = time.time()
                if driving:
                    self.amp_buffer1.append((now, amps1))
                    self.amp_buffer2.append((now, amps2))

                    # 古いデータを削除
                    self.amp_buffer1 = [(t,a) for t,a in self.amp_buffer1 if now - t <= self.AMP_WINDOW_TIME]
                    self.amp_buffer2 = [(t,a) for t,a in self.amp_buffer2 if now - t <= self.AMP_WINDOW_TIME]

                    amps1_list = [a for t,a in self.amp_buffer1]
                    amps2_list = [a for t,a in self.amp_buffer2]
                    self.stuck_flag2 = (max(amps1_list)-min(amps1_list) < self.AMP_VARIATION) and \
                                       (max(amps2_list)-min(amps2_list) < self.AMP_VARIATION)
                else:
                    self.amp_buffer1 = []
                    self.amp_buffer2 = []
                    self.stuck_flag2 = False

                # ===== 状態表示 =====
                print(f"RPM1:{rpm1:.1f} RPM2:{rpm2:.1f} "
                      f"AMP1:{amps1:.1f} AMP2:{amps2:.1f} "
                      f"flag1:{self.stuck_flag1} flag2:{self.stuck_flag2}")

                # ===== 最終判定 =====
                if self.stuck_flag1 and self.stuck_flag2:
                    print("STUCK DETECTED")

                time.sleep(0.05)

            except KeyboardInterrupt:
                print("Program stopped by user.")
                break

if __name__ == "__main__":
    detector = StuckDetector(port="COM3")
    print("Connected:", detector.connected)
    detector.run()
# 動作は成功　スタックの検知が遅い  スタックしているのに電流が1A変わるだけで解除されてしまう  