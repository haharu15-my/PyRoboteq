from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import math

class OpenLoopStuckController:
    def __init__(self, port="COM3"):
        # ===== コントローラ =====
        self.controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
        self.connected = self.controller.connect(port)
        if self.connected:
            self.controller.send_command(cmds.REL_EM_STOP)

        # ===== 機体パラメータ =====
        self.WHEEL_RADIUS = 0.13   # [m]
        self.GEAR_RATIO = 25
        self.dt = 0.05

        # ===== 速度指令（m/s）=====
        self.NORMAL_SPEED = 0.1     # 通常走行
        self.RECOVERY_SPEED = 0.13   # ★ 回復走行（-130 相当）

        # ===== STUCK 判定パラメータ =====
        self.RPM_THRESHOLD = 5    # RPM停止閾値
        self.RPM_STUCK_TIME = 1.0 # RPM停止判定時間

        self.AMP_WINDOW_TIME = 0.1  # 電流張り付き観測時間
        self.AMP_VARIATION = 3.0       # 電流張り付き変化量

        self.STUCK_CONFIRM_TIME = 2.0 # STUCK確定時間
        self.RECOVERY_TIME = 5.0      # 回復動作時間

        # ===== 状態 =====
        self.state = "NORMAL"   # NORMAL, STUCK, RECOVERY, ERROR_STOP
        self.rpm_stop_start = None
        self.stuck_confirm_start = None
        self.recovery_start = None

        self.amp_buffer1 = []
        self.amp_buffer2 = []

        self.stuck_flag1 = False
        self.stuck_flag2 = False

    # -------------------------------------------------

    def speed_to_cmd(self, speed_mps):
        """
        0.1 m/s → -100
        0.13 m/s → -130
        """
        cmd = int(-speed_mps * 1000)
        return max(min(cmd, 1000), -1000)

    def read_actual_speed(self):
        raw = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        if isinstance(raw, str) and '=' in raw:
            motor_rpm = float(raw.split('=')[-1])
        else:
            motor_rpm = float(raw)

        motor_rpm = -motor_rpm
        wheel_rpm = motor_rpm / self.GEAR_RATIO
        speed = (2 * math.pi * self.WHEEL_RADIUS * wheel_rpm) / 60.0
        return speed, abs(motor_rpm)

    def parse_amp(self, val):
        if isinstance(val, str) and '=' in val:
            val = val.split('=')[-1]
        try:
            return abs(float(val))
        except:
            return 0.0

    # -------------------------------------------------

    def run(self):
        print("OpenLoop + STUCK Detection Start")

        while self.connected:
            try:
                now = time.time()

                act_speed, rpm = self.read_actual_speed()
                amp1 = self.parse_amp(self.controller.read_value(cmds.READ_MOTOR_AMPS, 1))
                amp2 = self.parse_amp(self.controller.read_value(cmds.READ_MOTOR_AMPS, 2))

                # ===== 状態ごとの速度指令 =====
                if self.state == "NORMAL":
                    target_speed = self.NORMAL_SPEED

                elif self.state == "RECOVERY":
                    target_speed = self.RECOVERY_SPEED
                    if now - self.recovery_start >= self.RECOVERY_TIME:
                        if rpm > self.RPM_THRESHOLD:
                            print("RECOVERY SUCCESS → NORMAL")
                            self.state = "NORMAL"
                        else:
                            print("RECOVERY FAILED → SAFE STOP")
                            self.state = "ERROR_STOP"

                elif self.state == "ERROR_STOP":
                    self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                    print("SYSTEM HALTED")
                    break

                cmd = self.speed_to_cmd(target_speed)
                self.controller.send_command(cmds.DUAL_DRIVE, cmd, cmd)

                driving = target_speed > 0.0

                # ===== STUCK判定① RPM停止 =====
                if driving and rpm < self.RPM_THRESHOLD:
                    if self.rpm_stop_start is None:
                        self.rpm_stop_start = now
                    elif now - self.rpm_stop_start >= self.RPM_STUCK_TIME:
                        self.stuck_flag1 = True
                else:
                    self.rpm_stop_start = None
                    self.stuck_flag1 = False

                # ===== STUCK判定② 電流張り付き =====
                if driving:
                    self.amp_buffer1.append((now, amp1))
                    self.amp_buffer2.append((now, amp2))
                    self.amp_buffer1 = [(t,a) for t,a in self.amp_buffer1 if now-t <= self.AMP_WINDOW_TIME]
                    self.amp_buffer2 = [(t,a) for t,a in self.amp_buffer2 if now-t <= self.AMP_WINDOW_TIME]

                    a1 = [a for t,a in self.amp_buffer1]
                    a2 = [a for t,a in self.amp_buffer2]

                    if len(a1) > 1 and len(a2) > 1:
                        self.stuck_flag2 = (max(a1)-min(a1) < self.AMP_VARIATION) and \
                                           (max(a2)-min(a2) < self.AMP_VARIATION)
                    else:
                        self.stuck_flag2 = False
                else:
                    self.amp_buffer1.clear()
                    self.amp_buffer2.clear()
                    self.stuck_flag2 = False

                # ===== STUCK確定 =====
                if self.state == "NORMAL" and self.stuck_flag1 and self.stuck_flag2:
                    if self.stuck_confirm_start is None:
                        self.stuck_confirm_start = now
                        self.state = "STUCK"

                elif self.state == "STUCK":
                    if self.stuck_flag1 and self.stuck_flag2:
                        if now - self.stuck_confirm_start >= self.STUCK_CONFIRM_TIME:
                            print("STUCK confirmed → RECOVERY")
                            self.state = "RECOVERY"
                            self.recovery_start = now
                            self.stuck_confirm_start = None
                    else:
                        self.state = "NORMAL"
                        self.stuck_confirm_start = None

                print(
                    f"STATE:{self.state} | "
                    f"TGT:{target_speed:.2f} m/s | "
                    f"ACT:{act_speed:.3f} m/s | "
                    f"CMD:{cmd} | "
                    f"RPM:{rpm:.1f} | "
                    f"AMP:{amp1:.1f},{amp2:.1f}"
                )

                time.sleep(self.dt)

            except KeyboardInterrupt:
                self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                print("Control stopped")
                break


if __name__ == "__main__":
    OpenLoopStuckController("COM3").run()


#入力値-100と-130を0.1m/sと0.13m/sに変更した
#キーボード操作無しで動作確認した
#動作確認時にスタック検出も確認した