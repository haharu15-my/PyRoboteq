from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

# ==========================
# Utility 関数
# ==========================
def parse_rpm(value) -> int:
    """Roboteqの 'BS=123' を整数に変換。失敗したら0。"""
    if not isinstance(value, str):
        value = str(value)
    try:
        return int(value.split("=")[1])
    except:
        return 0

# ==========================
# セットアップ
# ==========================
controller = RoboteqHandler()
connected = controller.connect("COM3")

controller.send_command(cmds.REL_EM_STOP)  # 電子緊急停止解除

drive_speed_motor_one = 0
drive_speed_motor_two = 0

stall_detected = False
stall_start_time = None
countdown_start_time = None
countdown_done = False

if __name__ == "__main__":
    print("W: 前進 / S: 停止")
    print("スタック時: 自動的に10秒カウントダウン → Yでトルク5秒 → 自動前進")

    while connected:

        # --- キー入力 ---------------------------
        w = keyboard.is_pressed("w")
        s = keyboard.is_pressed("s")
        y = keyboard.is_pressed("y")

        # --- RPM 読み取り -----------------------
        raw1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        raw2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)
        speed1 = parse_rpm(raw1)
        speed2 = parse_rpm(raw2)
        avg_speed = (abs(speed1) + abs(speed2)) / 2

        # ==========================================
        # 前進入力
        # ==========================================
        if w and not s:
            drive_speed_motor_one = 200
            drive_speed_motor_two = 200

            # 速度が復活したらカウントダウン解除
            if avg_speed > 30:
                stall_detected = False
                stall_start_time = None
                countdown_start_time = None
                countdown_done = False

        # ==========================================
        # 停止入力
        # ==========================================
        if s:
            drive_speed_motor_one = 0
            drive_speed_motor_two = 0
            stall_detected = False
            stall_start_time = None
            countdown_start_time = None
            countdown_done = False

        # ==========================================
        # スタック判定（速度ベース）
        # ==========================================
        if w and not s and avg_speed < 5:   # 速度がほぼ0
            if not stall_detected:
                stall_detected = True
                stall_start_time = time.time()
            else:
                # 1秒以上止まっていたらカウントダウン開始
                if time.time() - stall_start_time >= 1:
                    if countdown_start_time is None:
                        countdown_start_time = time.time()
                        print("\n--- スタック検出！10秒カウントダウン開始 ---")
        else:
            stall_detected = False
            stall_start_time = None
            # 速度復活 → カウントダウン解除
            if avg_speed > 20:
                countdown_start_time = None
                countdown_done = False

        # ==========================================
        # カウントダウン処理
        # ==========================================
        if countdown_start_time is not None and not countdown_done:
            elapsed = time.time() - countdown_start_time
            remaining = max(0, 10 - int(elapsed))
            print(f"カウントダウン: {remaining}秒   ", end="\r")

            if elapsed >= 10:
                countdown_done = True
                print("\n--- カウント終了！Yでトルクを有効化できます ---")

        # ==========================================
        # Yでトルク5秒（自動調整）
        # ==========================================
        if countdown_done and y:
            print("\n=== トルク自動調整5秒開始 ===")

            torque_end = time.time() + 5

            while time.time() < torque_end:
                # 最新速度を読む（調整用）
                r1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
                r2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)
                s1 = parse_rpm(r1)
                s2 = parse_rpm(r2)
                avg = (abs(s1) + abs(s2)) / 2

                # ---- トルク自動調整 ----
                max_speed_ref = 120
                torque_base = 40
                torque_gain = 1.0

                required_torque = torque_base + (max_speed_ref - min(avg, max_speed_ref)) * torque_gain
                required_torque = max(0, min(124, int(required_torque)))

                print(f"速度={avg:.1f} → トルク={required_torque}", end="\r")

                controller.send_command(cmds.GO_TORQUE, 1, required_torque)
                controller.send_command(cmds.GO_TORQUE, 2, required_torque)
                time.sleep(0.05)

            # トルクOFF
            controller.send_command(cmds.GO_TORQUE, 1, 0)
            controller.send_command(cmds.GO_TORQUE, 2, 0)
            print("\n=== トルク終了 ===")

            # ---- 自動前進（2秒） ----
            print("=== 自動前進2秒 ===")
            auto_end = time.time() + 2
            while time.time() < auto_end:
                controller.send_command(cmds.DUAL_DRIVE, 200, 200)
                time.sleep(0.05)

            print("=== 通常モードへ復帰 ===")

            # 状態リセット
            countdown_done = False
            countdown_start_time = None
            stall_detected = False
            stall_start_time = None

        # ==========================================
        # 通常の走行コマンドを送信
        # ==========================================
        controller.send_command(cmds.DUAL_DRIVE, drive_speed_motor_one, drive_speed_motor_two)
        time.sleep(0.05)
