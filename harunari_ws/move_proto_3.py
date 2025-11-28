from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time
import keyboard

controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)
connected = controller.connect("COM3")

print("Roboteq connected:", connected)

# --- 安全にRPMを整数化するための関数 ---
def parse_rpm(value) -> int:
    if not isinstance(value, str):
        value = str(value)
    try:
        return int(value.split('=')[1])
    except (IndexError, ValueError):
        return 0


stall_detected = False
stall_start_time = None
countdown_done = False

try:
    while True:

        # --- RPM 読み取り ---
        raw1 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 1)
        raw2 = controller.read_value(cmds.READ_BL_MOTOR_RPM, 2)

        speed1 = parse_rpm(raw1)
        speed2 = parse_rpm(raw2)

        avg_speed = (abs(speed1) + abs(speed2)) / 2

        # --- キー入力 ---
        w = keyboard.is_pressed("w")
        s = keyboard.is_pressed("s")
        y = keyboard.is_pressed("y")

        # --- ▶ スタック条件：W が押されていて S が押されていない かつ 速度0 ---
        current_stall_condition = (w and not s and avg_speed == 0)

        # --- スタック開始 ---
        if current_stall_condition:
            if not stall_detected:
                stall_detected = True
                stall_start_time = time.time()
                countdown_done = False
                print("\n=== スタック検知！停止後10秒カウント開始 ===")
        else:
            # 途中で速度が出たり、Wが離れたりしたらカウントダウン解除
            if stall_detected:
                print("\n--- カウントダウン解除（速度が回復 or 条件解除）---")
            stall_detected = False
            countdown_done = False

        # --- カウントダウン中 ---
        if stall_detected and not countdown_done:
            elapsed = time.time() - stall_start_time
            remaining = int(10 - elapsed)

            if remaining >= 0:
                print(f"復帰待ち：{remaining} 秒", end="\r")
            else:
                countdown_done = True
                print("\n--- 10秒経過。Yキーでトルク起動可能 ---")

        # --- Y でトルクコマンド 5秒発動 ---
        if countdown_done and y:
            print("\n*** トルクコマンド 5秒発動！段差突破モード！ ***")

            # 5秒トルク ON
            torque_end_time = time.time() + 5
            while time.time() < torque_end_time:
                controller.send_command(cmds.GO_TORQUE, 1, 124)
                controller.send_command(cmds.GO_TORQUE, 2, 124)
                time.sleep(0.05)

            # トルクOFF
            controller.send_command(cmds.GO_TORQUE, 1, 0)
            controller.send_command(cmds.GO_TORQUE, 2, 0)

            print("*** トルク終了 ***")

            # 状態リセット
            countdown_done = False
            stall_detected = False
            stall_start_time = None

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n終了します")
    controller.disconnect()
