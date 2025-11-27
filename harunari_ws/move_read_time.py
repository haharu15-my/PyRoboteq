from PyRoboteq import RoboteqHandler  
from PyRoboteq import roboteq_commands as cmds  
import time  
import json  
from datetime import datetime  

#調整中
  
class UnifiedTimeTracker:  
    def __init__(self, controller, current_threshold=0.1):  
        self.controller = controller  
        self.current_threshold = current_threshold  
        self.start_time = None  
        self.total_operating_time = 0  
        self.driving_time = 0  
        self.last_counter = None  
        self.is_driving = False  
        self.is_operating = False  
        self.session_start = None  
          
    def start_tracking(self):  
        """時間追跡を開始"""  
        self.session_start = time.time()  
        current_time = self._get_current_time()  
        if current_time:  
            self.start_time = current_time  
            print(f"時間追跡開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")  
            return True  
        return False  
          
    def update_status(self):  
        """ステータスを更新"""  
        if not self.start_time:  
            return  
              
        # モーター稼働状態をチェック  
        motor_running = self._is_motor_running()  
        if motor_running and not self.is_operating:  
            self.is_operating = True  
            print("モーター稼働開始")  
        elif not motor_running and self.is_operating:  
            self.is_operating = False  
            print("モーター稼働停止")  
              
        # 走行状態をチェック  
        driving_status = self._update_driving_status()  
          
        # 時間を更新  
        if self.is_operating:  
            self.total_operating_time += 1  
        if self.is_driving:  
            self.driving_time += 1  
              
    def _is_motor_running(self):  
        """モーターが稼働中か判定"""  
        try:  
            amps_response = self.controller.read_value(cmds.READ_MOTOR_AMPS, 1)  
            if amps_response.startswith("A="):  
                amps = float(amps_response.split("=")[1].strip())  
                return amps > self.current_threshold  
        except:  
            pass  
        return False  
          
    def _update_driving_status(self):  
        """走行状態を更新"""  
        try:  
            current_counter = self._read_encoder_counter()  
            if self.last_counter is not None:  
                if current_counter != self.last_counter:  
                    if not self.is_driving:  
                        self.is_driving = True  
                        print("走行開始")  
                    return True  
                else:  
                    if self.is_driving:  
                        self.is_driving = False  
                        print("走行停止")  
                    return False  
            self.last_counter = current_counter  
        except Exception as e:  
            print(f"エンコーダ読み取りエラー: {e}")  
        return False  
          
    def _read_encoder_counter(self):  
        """エンコーダカウンタ値を読み取り"""  
        response = self.controller.read_value(cmds.READ_ABSCNTR, 1)  
        if response.startswith("C="):  
            return int(response.split("=")[1].strip())  
        return 0  
          
    def _get_current_time(self):  
        """現在時刻を取得"""  
        try:  
            response = self.controller.read_value(cmds.READ_TIME, 1)  
            if response.startswith("TM ="):  
                return int(response.split("=")[1].strip())  
        except:  
            pass  
        return None  
          
    def get_status_report(self):  
        """ステータスレポートを取得"""  
        session_time = int(time.time() - self.session_start) if self.session_start else 0  
          
        return {  
            "session_time": session_time,  
            "total_operating_time": self.total_operating_time,  
            "driving_time": self.driving_time,  
            "is_operating": self.is_operating,  
            "is_driving": self.is_driving,  
            "operating_ratio": (self.total_operating_time / session_time * 100) if session_time > 0 else 0,  
            "driving_ratio": (self.driving_time / session_time * 100) if session_time > 0 else 0  
        }  
          
    def save_data(self, filename="time_tracker_data.json"):  
        """データを保存"""  
        data = self.get_status_report()  
        data["timestamp"] = datetime.now().isoformat()  
          
        try:  
            with open(filename, 'w') as f:  
                json.dump(data, f, indent=2)  
            print(f"データを保存しました: {filename}")  
        except Exception as e:  
            print(f"保存エラー: {e}")  
  
def main():  
    controller = RoboteqHandler(debug_mode=True, exit_on_interrupt=False)  
      
    if controller.connect("COM3"):  
        print("コントローラに接続しました")  
          
        # 統合トラッカーを作成  
        tracker = UnifiedTimeTracker(controller, current_threshold=0.1)  
          
        if tracker.start_tracking():  
            try:  
                while True:  
                    # ステータスを更新  
                    tracker.update_status()  
                      
                    # レポートを表示  
                    report = tracker.get_status_report()  
                    print(f"\n=== 時間追跡レポート ===")  
                    print(f"セッション時間: {report['session_time']}秒")  
                    print(f"総稼働時間: {report['total_operating_time']}秒 ({report['operating_ratio']:.1f}%)")  
                    print(f"走行時間: {report['driving_time']}秒 ({report['driving_ratio']:.1f}%)")  
                    print(f"モーター稼働中: {'はい' if report['is_operating'] else 'いいえ'}")  
                    print(f"走行中: {'はい' if report['is_driving'] else 'いいえ'}")  
                      
                    time.sleep(1)  # 1秒ごとに更新  
                      
            except KeyboardInterrupt:  
                print("\n計測を終了します")  
                final_report = tracker.get_status_report()  
                tracker.save_data()  
                print(f"最終レポート: 稼働時間 {final_report['total_operating_time']}秒, 走行時間 {final_report['driving_time']}秒")  
        else:  
            print("時間追跡の開始に失敗しました")  
    else:  
        print("コントローラへの接続に失敗しました")  
  
if __name__ == "__main__":  
    main()