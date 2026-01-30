from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import math
import keyboard

class OpenLoopStuckKeyboardController:
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

        # ===== 速度指令 [m/s] =
        # ====
        self.NORMAL_SPEED = 0.03
        self.RECOVERY_SPEED = 0.13

        # ===== STUCK判定パラメータ =====
        self.RPM_THRESHOLD = 5
        self.RPM_STUCK_TIME = 1.0

        self.AMP_WINDOW_TIME = 0.1
        self.AMP_VARIATION = 3.0

        self.STUCK_CONFIRM_TIME = 2.0
        self.RECOVERY_TIME = 5.0

        # ===== 状態 =====
        self.state = "NORMAL"   # NORMAL / STUCK / RECOVERY / ERROR_STOP
        self.rpm_stop_start = None
        self.stuck_confirm_start = None
        self.recovery_start = None

        self.amp_buffer1 = []
        self.amp_buffer2 = []

        self.stuck_flag1 = False
        self.stuck_flag2 = False

    # --------------------------------------------------
    # 速度[m/s] → Roboteq CMD
    # --------------------------------------------------
    def speed_to_cmd(self, speed_mps):
        cmd = int(-speed_mps * 1000)
        return max(min(cmd, 1000), -1000)

    # --------------------------------------------------
    # 実速度取得
    # --------------------------------------------------
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

    # --------------------------------------------------
    # 電流値取得
    # --------------------------------------------------
    def read_amp(self, channel):
        val = self.controller.read_value(cmds.READ_MOTOR_AMPS, channel)
        if isinstance(val, str) and '=' in val:
            val = val.split('=')[-1]
        try:
            return abs(float(val))
        except:
            return 0.0

    # --------------------------------------------------
    # キーボード入力
    # --------------------------------------------------
    def get_keyboard_target(self):
        if keyboard.is_pressed('w'):
            return self.NORMAL_SPEED, True, "w"
        elif keyboard.is_pressed('s'):
            return -0.15, False, "s"
        elif keyboard.is_pressed('space'):
            return 0.0, False, "STOP"
        else:
            return 0.0, False, "-"

    # --------------------------------------------------
    # メインループ
    # --------------------------------------------------
    def run(self):
        print("OpenLoop + STUCK Detection + Keyboard Control Start")

        while self.connected:
            try:
                now = time.time()

                act_speed, rpm = self.read_actual_speed()
                amp1 = self.read_amp(1)
                amp2 = self.read_amp(2)

                # ===== 状態ごとの速度決定 =====
                if self.state == "NORMAL":
                    target_speed, allow_stuck, key = self.get_keyboard_target()

                elif self.state == "STUCK":
                    target_speed, allow_stuck, key = self.get_keyboard_target()

                elif self.state == "RECOVERY":
                    target_speed = self.RECOVERY_SPEED
                    allow_stuck = False
                    key = "RECOVERY"

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

                driving = allow_stuck and target_speed > 0.0

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

                    if len(self.amp_buffer1) > 1 and len(self.amp_buffer2) > 1:
                        a1 = [a for t,a in self.amp_buffer1]
                        a2 = [a for t,a in self.amp_buffer2]
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
                    f"{now:.2f},"
                    f"{self.state},"
                    f"{key},"
                    f"{target_speed:.2f},"
                    f"{act_speed:.3f},"
                    f"{cmd},"
                    f"{rpm:.1f},"
                    f"{amp1:.1f},"
                    f"{amp2:.1f}"
                )


                time.sleep(self.dt)

            except KeyboardInterrupt:
                self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                print("Control stopped")
                break


if __name__ == "__main__":
    OpenLoopStuckKeyboardController("COM3").run()
