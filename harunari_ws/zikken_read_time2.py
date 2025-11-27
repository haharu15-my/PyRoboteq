from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds
import time 
controller = RoboteqHandler(debug_mode=True)
if controller.connect("COM3"):# 1回目の読み取り
    uptime1 = controller.read_value("?TM")  
    print(f"初回読み取り: {uptime1}")  
  
    # 5秒待機  
    time.sleep(5)  
  
    # 2回目の読み取り（約5秒増加しているはず）  
    uptime2 = controller.read_value("?TM")  
    print(f"5秒後: {uptime2}")  
  
    # 差分を計算して確認  
    seconds1 = int(uptime1.split('=')[1])  
    seconds2 = int(uptime2.split('=')[1])  
    print(f"経過秒数: {seconds2 - seconds1}")