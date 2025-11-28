from PyRoboteq import RoboteqHandler  
from PyRoboteq import roboteq_commands as cmds  
import keyboard  
import time  
  
controller = RoboteqHandler(debug_mode=False, exit_on_interrupt=False)  
connected = controller.connect("COM3")  
  
controller.send_command(cmds.REL_EM_STOP)  
  
# 時間測定用変数  
start_time = None  
running_time = 0  
last_active_time = time.time()  
  
# バッテリー測定用変数  
total_current_consumed = 0  # 総消費電流（積算値）  
last_battery_read_time = time.time()  
  
if __name__ == "__main__":  
    while connected:  
        try:  
            # 稼働時間を読み取り（?TMコマンドを追加する必要あり）  
            operating_time = controller.read_value(cmds.READ_TIMES)  
              
            # バッテリー情報を読み取り  
            battery_amps = controller.read_value(cmds.READ_BATTERY_AMPS)  
            battery_volts = controller.read_value(cmds.READ_VOLTS, 2)  # チャンネル2 = バッテリー電圧  
              
            motor_amps = controller.read_value(cmds.READ_MOTOR_AMPS, 0)  
              
            is_moving = False  
              
            if keyboard.is_pressed('w'):#前進  
                print("W pressed - 前進")  
                drive_speed_motor_one = -200  
                drive_speed_motor_two = -200  
                is_moving = True  
  
            elif keyboard.is_pressed('s'):#後退  
                print("S pressed - 後退")  
                drive_speed_motor_one = 200  
                drive_speed_motor_two = 200  
                is_moving = True  
  
            elif keyboard.is_pressed('a'):#左回転  
                print("A pressed - 左回転")  
                drive_speed_motor_one = -200  
                drive_speed_motor_two = 200  
                is_moving = True  
  
            elif keyboard.is_pressed('d'):#右回転  
                print("D pressed - 右回転")  
                drive_speed_motor_one = 200  
                drive_speed_motor_two = -200  
                is_moving = True  
  
            else:  
                drive_speed_motor_one = 0  
                drive_speed_motor_two = 0  
  
            # 走行時間の計算  
            current_time = time.time()  
            if is_moving:  
                if start_time is None:  
                    start_time = current_time  
                running_time += current_time - last_active_time  
            last_active_time = current_time  
  
            # バッテリー消費量の積算  
            time_delta = current_time - last_battery_read_time  
            if battery_amps.startswith("BA="):  
                current_draw = float(battery_amps.split("=")[1])  
                total_current_consumed += current_draw * time_delta / 3600  # Ah単位で積算  
            last_battery_read_time = current_time  
  
            controller.send_command(cmds.DUAL_DRIVE, drive_speed_motor_one, drive_speed_motor_two)  
              
            # 情報を表示  
            print(f"走行時間: {running_time:.2f}秒")  
            print(f"バッテリー電流: {battery_amps}")  
            print(f"バッテリー電圧: {battery_volts}")  
            print(f"総消費電流: {total_current_consumed:.4f} Ah")  
            print(f"モーター電流: {motor_amps}")  
            print("---")  
  
        except KeyboardInterrupt:  
            break