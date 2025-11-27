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
