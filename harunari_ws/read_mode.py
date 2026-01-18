from PyRoboteq import RoboteqHandler
import time

controller = RoboteqHandler(debug_mode=True, exit_on_interrupt=True)

if controller.connect("COM3"):
    print("接続成功")

    cc = 1
    controller.send_raw_command(f"~MMOD {cc}")
    aom = controller.send_raw_command("?AOM 1")
    print("AOM:", aom)

    time.sleep(0.1)  # 応答待ち

    # Roboteqは応答をシリアルで返すが、PyRoboteqは保持しない
    print("※ debug log に返答が表示されていればOK")

#本研究では，Roboteqコントローラに対する設定クエリおよび動作状態クエリをPythonから送信したが，使用したPyRoboteqライブラリの仕様上，返答値を直接取得することができなかった。
#そのため，Roborun Utilityによる実機モニタリングおよびモータ挙動の観察を併用し，制御モードの切り替えを確認した。