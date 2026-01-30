import time
import csv
from datetime import datetime

from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds

class AutoRunScenario:
    """
    撮影向け：キーボード無しで
    カウントダウン → 前進RUN → 停止
    を自動実行し、ログも吐く。

    - detect_mode: "BOTH" (両輪AND) / "EITHER" (片輪OR)
    """

    def __init__(self, port="COM3"):
        # ===== 接続 =====
        self.controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
        self.connected = self.controller.connect(port)
        if not self.connected:
            raise RuntimeError(f"Roboteq に接続できません: {port}")

        # 安全のため、開始時は停止
        self.controller.send_command(cmds.REL_EM_STOP)

        # ===== 実行パラメータ（撮影用）=====
        self.COUNTDOWN_SEC = 10          # 撮影開始の余裕
        self.RUN_SEC = 8                 # 前進させる秒数
        self.POST_STOP_SEC = 3           # 停止後の余韻
        self.MAX_TOTAL_SEC = 30          # 念のため全体タイムアウト

        # ===== 指令値 =====
        self.NORMAL_CMD = -120           # 例：前進CMD（あなたの符号系に合わせて）
        self.RECOVERY_CMD = -130
        self.RECOVERY_SEC = 2.0

        # ===== スタック判定（例）=====
        self.RPM_TH = 5.0
        self.STUCK_CONFIRM_SEC = 2.0     # これが “発表で言える秒数” になる
        self.AMP_TH = 20.0               # 「上がった」と言える最低ライン（仮）
        self.detect_mode = "BOTH"        # "BOTH" or "EITHER"

        # ===== ログ =====
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = f"runlog_{ts}.csv"

        # 内部状態
        self.state = "IDLE"
        self.stuck_start = None

    # ======== ここはあなたの環境の “読み取りコマンド” に合わせて調整 ========
    def read_rpm_amps(self):
        """
        rpm1, rpm2, amp1, amp2 を返す。
        ここはあなたが以前使ってた read のやり方に合わせて差し替え。
        """
        # 例）実際のAPIに合わせて修正が必要
        rpm1 = float(self.controller.read_value(cmds.GET_RPM, 1))
        rpm2 = float(self.controller.read_value(cmds.GET_RPM, 2))
        amp1 = float(self.controller.read_value(cmds.GET_MOTOR_AMPS, 1))
        amp2 = float(self.controller.read_value(cmds.GET_MOTOR_AMPS, 2))
        return rpm1, rpm2, amp1, amp2

    def set_cmd(self, cmd):
        """
        前進/停止の指令。ここもあなたの送信コマンドに合わせて差し替え。
        """
        # 例）dual channel の場合
        self.controller.send_command(cmds.SET_COMMAND, 1, cmd)
        self.controller.send_command(cmds.SET_COMMAND, 2, cmd)

    def stop(self):
        self.set_cmd(0)

    # ======== スタック判定ロジック（撮影向け：説明しやすい） ========
    def is_stuck_now(self, rpm1, rpm2, amp1, amp2):
        # 「回ってない」判定
        s1 = abs(rpm1) < self.RPM_TH and amp1 > self.AMP_TH
        s2 = abs(rpm2) < self.RPM_TH and amp2 > self.AMP_TH

        if self.detect_mode == "BOTH":
            return (s1 and s2), s1, s2
        else:  # "EITHER"
            return (s1 or s2), s1, s2

    def run_once(self):
        start_t = time.time()

        with open(self.log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["t", "state", "cmd", "rpm1", "rpm2", "amp1", "amp2", "flag1", "flag2", "stuck_confirmed"])

            # 1) countdown
            self.state = "COUNTDOWN"
            for i in range(self.COUNTDOWN_SEC, 0, -1):
                print(f"[COUNTDOWN] {i}...")
                writer.writerow([time.time(), self.state, 0, "", "", "", "", "", "", ""])
                time.sleep(1.0)
                if time.time() - start_t > self.MAX_TOTAL_SEC:
                    print("[TIMEOUT] 強制停止")
                    self.stop()
                    return

            # 2) run
            self.state = "RUN"
            self.stuck_start = None
            run_start = time.time()
            self.set_cmd(self.NORMAL_CMD)

            while True:
                now = time.time()
                rpm1, rpm2, amp1, amp2 = self.read_rpm_amps()

                stuck_now, flag1, flag2 = self.is_stuck_now(rpm1, rpm2, amp1, amp2)

                stuck_confirmed = False
                if stuck_now:
                    if self.stuck_start is None:
                        self.stuck_start = now
                    elif (now - self.stuck_start) >= self.STUCK_CONFIRM_SEC:
                        stuck_confirmed = True
                else:
                    self.stuck_start = None

                writer.writerow([now, self.state, self.NORMAL_CMD, rpm1, rpm2, amp1, amp2, flag1, flag2, stuck_confirmed])

                # 終了条件：時間
                if (now - run_start) >= self.RUN_SEC:
                    print("[RUN] 規定時間終了 → STOP")
                    break

                # 終了条件：スタック確定（撮影的にはここで止めた方が綺麗）
                if stuck_confirmed:
                    print("[RUN] STUCK 確定 → STOP（必要ならRECOVERYへ）")
                    # 回復を見せたい場合だけONにする
                    # self.do_recovery(writer)
                    break

                if (now - start_t) > self.MAX_TOTAL_SEC:
                    print("[TIMEOUT] 強制停止")
                    break

                time.sleep(0.05)

            # 3) stop
            self.state = "STOP"
            self.stop()
            stop_t = time.time()
            while (time.time() - stop_t) < self.POST_STOP_SEC:
                writer.writerow([time.time(), self.state, 0, "", "", "", "", "", "", ""])
                time.sleep(0.2)

        print(f"[DONE] log saved: {self.log_path}")

    def do_recovery(self, writer):
        """
        発表で「回復動作」も撮りたい場合に使う。
        """
        self.state = "RECOVERY"
        rec_start = time.time()
        self.set_cmd(self.RECOVERY_CMD)
        while (time.time() - rec_start) < self.RECOVERY_SEC:
            rpm1, rpm2, amp1, amp2 = self.read_rpm_amps()
            stuck_now, flag1, flag2 = self.is_stuck_now(rpm1, rpm2, amp1, amp2)
            writer.writerow([time.time(), self.state, self.RECOVERY_CMD, rpm1, rpm2, amp1, amp2, flag1, flag2, False])
            time.sleep(0.05)
        self.stop()

if __name__ == "__main__":
    # モード切替：既存の限界を見るなら "BOTH"、片輪対応なら "EITHER"
    runner = AutoRunScenario(port="COM3")
    runner.detect_mode = "BOTH"
    runner.run_once()
