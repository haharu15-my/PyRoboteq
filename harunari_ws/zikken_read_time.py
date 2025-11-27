from PyRoboteq import RoboteqHandler
from PyRoboteq import roboteq_commands as cmds

controller = RoboteqHandler(debug_mode=True)
if controller.connect("COM3"):
    # 秒を読み取り
    seconds = controller.read_value(cmds.READ_TIME, 1)
    print(f"秒: {seconds}")
    
    # 分を読み取り  
    minutes = controller.read_value(cmds.READ_TIME, 2)
    print(f"分: {minutes}")
    
    # 時を読み取り
    hours = controller.read_value(cmds.READ_TIME, 3)
    print(f"時: {hours}")

    # 日を読み取り
    day = controller.read_value(cmds.READ_TIME, 4)
    print(f"日: {day}")
    
    # 月を読み取り  
    month = controller.read_value(cmds.READ_TIME,5)
    print(f"月: {month}")
    
    # 年を読み取り
    year = controller.read_value(cmds.READ_TIME,6)
    print(f"年: {year}")

    #print(f"{year}/{month}/{day} {hours}:{minutes}:{seconds}") 

    uptime_seconds = controller.read_value("?TM")  # パラメータなし  
    print(f"起動してからの秒数: {uptime_seconds}")