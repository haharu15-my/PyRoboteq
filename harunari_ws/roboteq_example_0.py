from PyRoboteq import RoboteqHandler  
from PyRoboteq import roboteq_commands as cmds  
  
# デバッグモードとexit_on_interruptを有効化  
controller = RoboteqHandler(debug_mode=True, exit_on_interrupt=True)  
  
# 接続を確認  
if controller.connect("COM3"):  # ポート名を適切に設定  
    print("接続成功")  
      
    # モーター電流値を読み取る  
    result = controller.read_value(cmds.READ_MOTOR_AMPS,1)  
    print(f"返された値: {result}")  
    print(f"値の型: {type(result)}")  
else:  
    print("接続に失敗しました")