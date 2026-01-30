from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import keyboard
import time
import math


class KeyboardOpenLoopControlAvg:
    def __init__(self, port="COM3"):
        self.controller = RoboteqHandler()
        self.connected = self.controller.connect(port)
        self.controller.send_command(cmds.REL_EM_STOP)

        # ===== パラメータ =====
        self.WHEEL_RADIUS = 0.11   # [m]
        self.GEAR_RATIO = 25
        self.dt = 0.05

        # 目標速度（表示用）
        self.target_speed = 0.0

        # CMD!=0 の走行中だけ入れるログ
        self.vL_log = []
        self.vR_log = []
        self.vAvg_log = []

    def _parse_value(self, raw):
        """Roboteqの返り値が 'XXX=123' でも数値でも対応"""
        if isinstance(raw, str) and '=' in raw:
            return float(raw.split('=')[-1])
        return float(raw)

    def rpm_to_speed(self, motor_rpm):
        """motor_rpm -> 車輪線速度[m/s]（符号合わせ込み）"""
        motor_rpm = -motor_rpm  # あなたの環境の符号に合わせる
        wheel_rpm = motor_rpm / self.GEAR_RATIO
        speed = (2 * math.pi * self.WHEEL_RADIUS * wheel_rpm) / 60.0
        return speed

    def read_actual_speeds(self):
        """CH1/CH2を読んで、左右速度と平均速度を返す"""
        raw1 = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        raw2 = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

        rpm1 = self._parse_value(raw1)
        rpm2 = self._parse_value(raw2)

        vL = self.rpm_to_speed(rpm1)  # CH1
        vR = self.rpm_to_speed(rpm2)  # CH2
        vAvg = (vL + vR) / 2.0
        return vL, vR, vAvg

    def update_target(self):
        # キー入力で目標速度（表示用）を更新
        if keyboard.is_pressed("w"):
            self.target_speed = 0.13   # 今の実験条件に合わせてOK（例）
        elif keyboard.is_pressed("s"):
            self.target_speed = -0.20
        else:
            self.target_speed = 0.0

    def run(self):
        try:
            while True:
                self.update_target()

                vL, vR, vAvg = self.read_actual_speeds()
                motor_amps = self.controller.read_value(cmds.READ_MOTOR_AMPS, 0)

                # ---- Open Loop（P制御なし）----
                cmd_speed = self.target_speed

                # m/s → Roboteq CMD（暫定：1.0 m/s -> 1000）
                cmd = int(-cmd_speed * 1000)
                cmd = max(min(cmd, 1000), -1000)

                # 指令
                self.controller.send_command(cmds.DUAL_DRIVE, cmd, cmd)

                # ★重要：走行中（CMD!=0）のみログに入れる（停止後の減速を平均に混ぜない）
                if cmd != 0:
                    self.vL_log.append(vL)
                    self.vR_log.append(vR)
                    self.vAvg_log.append(vAvg)

                # 表示
                print(
                    f"TARGET:{self.target_speed:+.2f}m/s "
                    f"ACT_L:{vL:+.2f}m/s ACT_R:{vR:+.2f}m/s ACT_AVG:{vAvg:+.2f}m/s "
                    f"CMD:{cmd} AMPS:{motor_amps}"
                )

                time.sleep(self.dt)

        except KeyboardInterrupt:
            # 停止
            self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)

            # ===== 集計：立ち上がり1秒分を除外（CMD!=0区間のみが入っている前提）=====
            skip = int(1.0 / self.dt)
            steady = self.vAvg_log[skip:] if len(self.vAvg_log) > skip else self.vAvg_log

            if steady:
                avg = sum(steady) / len(steady)
                med = sorted(steady)[len(steady)//2]
                vmin, vmax = min(steady), max(steady)

                print("\n===== SUMMARY (ACT_AVG, CMD!=0 only) =====")
                print(f"avg   : {avg:.3f} m/s")
                print(f"median: {med:.3f} m/s")
                print(f"min~max: {vmin:.3f} ~ {vmax:.3f} m/s")
                print(f"samples: {len(steady)}")
            else:
                print("\n===== SUMMARY =====")
                print("データがありません（CMD!=0区間が記録されていません）")

            print("制御停止")


if __name__ == "__main__":
    KeyboardOpenLoopControlAvg().run()