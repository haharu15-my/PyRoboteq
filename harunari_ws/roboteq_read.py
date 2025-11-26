from PyRoboteq import RoboteqHandler  
from PyRoboteq import roboteq_commands as cmds  
  
# デバッグモードとexit_on_interruptを有効化  
controller = RoboteqHandler(debug_mode=True, exit_on_interrupt=True)  
  
# 接続を確認  
if controller.connect("COM3"):  # ポート名を適切に設定  
    print("接続成功")
    user_input = input("コマンド名を入力 (例: READ_MOTOR_AMPS): ")
    command = getattr(cmds, user_input)
    result = controller.read_value(cmds.READ,1)  
    print(f"測定結果: {result}")
else:  
    print("接続に失敗しました")