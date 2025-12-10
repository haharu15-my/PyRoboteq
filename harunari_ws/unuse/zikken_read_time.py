from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds

controller = RoboteqHandler(debug_mode=True)
if controller.connect("COM3"):
    # 秒を読み取り
    seconds = controller.read_value(cmds.READ, 1)
    print(f"秒: {seconds}")
    
    # 分を読み取り  
    minutes = controller.read_value(cmds.READ, 2)
    print(f"分: {minutes}")
    
    # 時を読み取り
    hours = controller.read_value(cmds.READ, 3)
    print(f"時: {hours}")

    # 日を読み取り
    day = controller.read_value(cmds.READ, 4)
    print(f"日: {day}")
    
    # 月を読み取り  
    month = controller.read_value(cmds.READ,5)
    print(f"月: {month}")
    
    # 年を読み取り
    year = controller.read_value(cmds.READ,6)
    print(f"年: {year}")

    #print(f"{year}/{month}/{day} {hours}:{minutes}:{seconds}") 新しいモデル	個別日付要素（年月日時分秒）	用途：現在時刻の取得

    uptime_seconds = controller.read_value("?TM")  # パラメータなし  
    print(f"起動してからの秒数: {uptime_seconds}") #古いモデル	32ビット秒カウンタ（アップタイム）	用途：稼働時間の計測