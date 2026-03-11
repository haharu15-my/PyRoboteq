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
        else:
            raise RuntimeError(f"Roboteq connect failed: {port}")

        # ===== 機体パラメータ =====
        self.WHEEL_RADIUS = 0.13   # [m]
        self.GEAR_RATIO = 25
        self.dt = 0.05

        # ===== 手動走行の速度指令 [m/s] =====
        self.NORMAL_SPEED = 0.1     # w：前進
        self.MANUAL_REVERSE = -0.15  # s：後退（手動）
        self.STOP_SPEED = 0.0        # space：停止

        # ===== 回復動作（片輪だけ前進させる）=====
        self.RECOVERY_BACK_SPEED = 0.2  # スタック側だけ前進
        self.RECOVERY_OTHER_SPEED = 0.1   # 反対側は停止（ピボットしすぎ防止）
        self.RECOVERY_TIME = 1.5          # 片輪回復は短めがおすすめ（撮影向け）

        # ===== STUCK判定パラメータ =====
        self.RPM_THRESHOLD = 5.0
        self.RPM_STUCK_TIME = 1.0

        self.AMP_WINDOW_TIME = 0.1
        self.AMP_VARIATION = 3.0

        self.STUCK_CONFIRM_TIME = 2.0

        # ===== 状態 =====
        # IDLE/NORMAL/STUCK_L/STUCK_R/STUCK_BOTH/RECOVERY_L/RECOVERY_R/RECOVERY_BOTH/ERROR_STOP
        self.state = "NORMAL"

        # RPM停止判定開始時刻（左右別）
        self.rpm_stop_start_L = None
        self.rpm_stop_start_R = None

        # STUCK確定のための開始時刻（左右別）
        self.stuck_confirm_start_L = None
        self.stuck_confirm_start_R = None

        # 回復開始時刻
        self.recovery_start = None

        # 電流バッファ（左右別）
        self.amp_buffer_L = []
        self.amp_buffer_R = []

        # 判定フラグ（左右別）
        self.stuck_rpm_L = False
        self.stuck_rpm_R = False
        self.stuck_amp_L = False
        self.stuck_amp_R = False

    # --------------------------------------------------
    # 速度[m/s] → Roboteq CMD
    # --------------------------------------------------
    def speed_to_cmd(self, speed_mps):
        cmd = int(-speed_mps * 1000)
        return max(min(cmd, 1000), -1000)

    # --------------------------------------------------
    # RPM読み取り（ch=1/2）
    # --------------------------------------------------
    def read_motor_rpm(self, ch):
        raw = self.controller.read_value(cmds.READ_BL_MOTOR_RPM, ch)
        if isinstance(raw, str) and '=' in raw:
            val = raw.split('=')[-1]
        else:
            val = raw
        try:
            motor_rpm = float(val)
        except:
            motor_rpm = 0.0

        # あなたの既存コードに合わせて符号反転（向き合わせ）
        motor_rpm = -motor_rpm
        return motor_rpm

    # --------------------------------------------------
    # 実速度（左右の平均）と左右RPM(abs)を返す
    # --------------------------------------------------
    def read_actual(self):
        motor_rpm_L = self.read_motor_rpm(1)
        motor_rpm_R = self.read_motor_rpm(2)

        wheel_rpm_L = motor_rpm_L / self.GEAR_RATIO
        wheel_rpm_R = motor_rpm_R / self.GEAR_RATIO

        speed_L = (2 * math.pi * self.WHEEL_RADIUS * wheel_rpm_L) / 60.0
        speed_R = (2 * math.pi * self.WHEEL_RADIUS * wheel_rpm_R) / 60.0

        act_speed_avg = (speed_L + speed_R) / 2.0
        rpm_abs_L = abs(motor_rpm_L)
        rpm_abs_R = abs(motor_rpm_R)
        return act_speed_avg, speed_L, speed_R, rpm_abs_L, rpm_abs_R

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
        # w: 前進（スタック判定する）
        if keyboard.is_pressed('w'):
            return self.NORMAL_SPEED, True, "w"
        # s: 後退（手動で抜く用。スタック判定しない）
        elif keyboard.is_pressed('s'):
            return self.MANUAL_REVERSE, False, "s"
        # space: 停止
        elif keyboard.is_pressed('space'):
            return self.STOP_SPEED, False, "STOP"
        else:
            return 0.0, False, "-"

    # --------------------------------------------------
    # 電流張り付き判定（左右別）
    # --------------------------------------------------
    def update_amp_stuck(self, now, amp_L, amp_R, driving):
        if not driving:
            self.amp_buffer_L.clear()
            self.amp_buffer_R.clear()
            self.stuck_amp_L = False
            self.stuck_amp_R = False
            return

        self.amp_buffer_L.append((now, amp_L))
        self.amp_buffer_R.append((now, amp_R))

        self.amp_buffer_L = [(t,a) for t,a in self.amp_buffer_L if now - t <= self.AMP_WINDOW_TIME]
        self.amp_buffer_R = [(t,a) for t,a in self.amp_buffer_R if now - t <= self.AMP_WINDOW_TIME]

        def calc_stuck_amp(buf):
            if len(buf) <= 1:
                return False
            arr = [a for _, a in buf]
            return (max(arr) - min(arr)) < self.AMP_VARIATION

        self.stuck_amp_L = calc_stuck_amp(self.amp_buffer_L)
        self.stuck_amp_R = calc_stuck_amp(self.amp_buffer_R)

    # --------------------------------------------------
    # RPM停止判定（左右別）
    # --------------------------------------------------
    def update_rpm_stuck(self, now, rpm_abs_L, rpm_abs_R, driving):
        if not driving:
            self.rpm_stop_start_L = None
            self.rpm_stop_start_R = None
            self.stuck_rpm_L = False
            self.stuck_rpm_R = False
            return

        # Left
        if rpm_abs_L < self.RPM_THRESHOLD:
            if self.rpm_stop_start_L is None:
                self.rpm_stop_start_L = now
            elif now - self.rpm_stop_start_L >= self.RPM_STUCK_TIME:
                self.stuck_rpm_L = True
        else:
            self.rpm_stop_start_L = None
            self.stuck_rpm_L = False

        # Right
        if rpm_abs_R < self.RPM_THRESHOLD:
            if self.rpm_stop_start_R is None:
                self.rpm_stop_start_R = now
            elif now - self.rpm_stop_start_R >= self.RPM_STUCK_TIME:
                self.stuck_rpm_R = True
        else:
            self.rpm_stop_start_R = None
            self.stuck_rpm_R = False

    # --------------------------------------------------
    # STUCK確定処理（左右別）
    # --------------------------------------------------
    def update_stuck_state(self, now, driving):
        stuck_L = self.stuck_rpm_L and self.stuck_amp_L
        stuck_R = self.stuck_rpm_R and self.stuck_amp_R

        if not driving:
            self.stuck_confirm_start_L = None
            self.stuck_confirm_start_R = None
            # 走行してないなら STUCK 系に留まらない
            if self.state.startswith("STUCK"):
                self.state = "NORMAL"
            return

        # まず確定タイマ更新
        if stuck_L:
            if self.stuck_confirm_start_L is None:
                self.stuck_confirm_start_L = now
        else:
            self.stuck_confirm_start_L = None

        if stuck_R:
            if self.stuck_confirm_start_R is None:
                self.stuck_confirm_start_R = now
        else:
            self.stuck_confirm_start_R = None

        # どっちが確定したか判定
        confirm_L = (self.stuck_confirm_start_L is not None) and ((now - self.stuck_confirm_start_L) >= self.STUCK_CONFIRM_TIME)
        confirm_R = (self.stuck_confirm_start_R is not None) and ((now - self.stuck_confirm_start_R) >= self.STUCK_CONFIRM_TIME)

        # STUCK → RECOVERY へ
        if self.state in ["NORMAL", "STUCK_L", "STUCK_R", "STUCK_BOTH"]:
            # 状態表示（確定前）
            if stuck_L and stuck_R:
                self.state = "STUCK_BOTH"
            elif stuck_L:
                self.state = "STUCK_L"
            elif stuck_R:
                self.state = "STUCK_R"
            else:
                self.state = "NORMAL"

            # 確定したら回復へ
            if confirm_L and confirm_R:
                print("STUCK BOTH confirmed → RECOVERY_BOTH")
                self.state = "RECOVERY_BOTH"
                self.recovery_start = now
            elif confirm_L:
                print("STUCK LEFT confirmed → RECOVERY_L")
                self.state = "RECOVERY_L"
                self.recovery_start = now
            elif confirm_R:
                print("STUCK RIGHT confirmed → RECOVERY_R")
                self.state = "RECOVERY_R"
                self.recovery_start = now

    # --------------------------------------------------
    # メインループ
    # --------------------------------------------------
    def run(self):
        print("OpenLoop + STUCK Detection (per-wheel) + Keyboard Control Start")

        while self.connected:
            try:
                now = time.time()

                act_avg, act_L, act_R, rpm_L, rpm_R = self.read_actual()
                amp_L = self.read_amp(1)
                amp_R = self.read_amp(2)

                # ===== NORMAL系ではキーボードで目標速度 =====
                if self.state in ["NORMAL", "STUCK_L", "STUCK_R", "STUCK_BOTH"]:
                    target_speed, allow_stuck, key = self.get_keyboard_target()

                    # 通常は両輪同じ指令（手動）
                    left_speed_cmd = target_speed
                    right_speed_cmd = target_speed

                    driving = allow_stuck and (target_speed > 0.0)

                    # スタック判定更新
                    self.update_rpm_stuck(now, rpm_L, rpm_R, driving)
                    self.update_amp_stuck(now, amp_L, amp_R, driving)
                    self.update_stuck_state(now, driving)

                # ===== 回復（片輪だけ後退）=====
                elif self.state in ["RECOVERY_L", "RECOVERY_R", "RECOVERY_BOTH"]:
                    key = self.state
                    driving = False  # 回復中はスタック判定しない

                    # 回復動作の速度指令を左右別で作る
                    if self.state == "RECOVERY_L":
                        left_speed_cmd = self.RECOVERY_BACK_SPEED
                        right_speed_cmd = self.RECOVERY_OTHER_SPEED
                    elif self.state == "RECOVERY_R":
                        left_speed_cmd = self.RECOVERY_OTHER_SPEED
                        right_speed_cmd = self.RECOVERY_BACK_SPEED
                    else:  # BOTH
                        left_speed_cmd = self.RECOVERY_BACK_SPEED
                        right_speed_cmd = self.RECOVERY_BACK_SPEED

                    # 回復時間が終わったら通常へ
                    if (now - self.recovery_start) >= self.RECOVERY_TIME:
                        print("RECOVERY done → NORMAL")
                        self.state = "NORMAL"
                        self.recovery_start = None
                        # タイマ類をリセット（次の判定を素直にする）
                        self.stuck_confirm_start_L = None
                        self.stuck_confirm_start_R = None
                        self.rpm_stop_start_L = None
                        self.rpm_stop_start_R = None
                        self.amp_buffer_L.clear()
                        self.amp_buffer_R.clear()

                elif self.state == "ERROR_STOP":
                    self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                    print("SYSTEM HALTED")
                    break

                # ===== Roboteqへ左右別CMDを送る =====
                left_cmd = self.speed_to_cmd(left_speed_cmd)
                right_cmd = self.speed_to_cmd(right_speed_cmd)
                self.controller.send_command(cmds.DUAL_DRIVE, left_cmd, right_cmd)

                # ===== ログ =====
                print(
                    f"STATE:{self.state} | KEY:{key} | "
                    f"CMD(L,R):{left_cmd},{right_cmd} | "
                    f"ACTavg:{act_avg:.3f} m/s | ACT(L,R):{act_L:.3f},{act_R:.3f} | "
                    f"RPM(L,R):{rpm_L:.1f},{rpm_R:.1f} | "
                    f"AMP(L,R):{amp_L:.1f},{amp_R:.1f} | "
                    f"STUCK_RPM(L,R):{int(self.stuck_rpm_L)},{int(self.stuck_rpm_R)} | "
                    f"STUCK_AMP(L,R):{int(self.stuck_amp_L)},{int(self.stuck_amp_R)}"
                )

                time.sleep(self.dt)

            except KeyboardInterrupt:
                self.controller.send_command(cmds.DUAL_DRIVE, 0, 0)
                print("Control stopped")
                break


if __name__ == "__main__":
    OpenLoopStuckKeyboardController("COM3").run()

#片輪ずつスタック判定するバージョン