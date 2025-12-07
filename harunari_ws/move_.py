import time
import keyboard # キーボード入力を扱うためのライブラリ

COUNTDOWN_SECONDS = 10

def countdown_and_print():
    """
    10秒のカウントダウンを行い、終了後に指定の文字列を出力します。
    カウントダウン中に 'y' キーが押された場合、処理を中断します。
    """
    print("🚀 10秒カウントダウン開始！")
    print("⚠️ 中止するには 'y' キーを押してください。")
    
    is_cancelled = False

    # 10秒から1秒までカウントダウン
    for i in range(COUNTDOWN_SECONDS, 0, -1):
        
        # 現在の残り時間を表示
        print(f"⏳ 残り {i} 秒...", end='\r')
        
        # --- キーボードチェック ---
        # 1秒の待ち時間を、細かく分割してキー入力をチェックします。
        # 1秒を100分割 (0.01秒間隔) してポーリングします。
        for _ in range(100):
            if keyboard.is_pressed('y'):
                print("\n\n❌ 'y' キーが押されました。カウントダウンを中止します。")
                is_cancelled = True
                break # 内部ループ (0.01秒間隔のポーリング) を抜ける
            time.sleep(0.01) # 短い時間待機
        
        if is_cancelled:
            break # 外部ループ (カウントダウン) を抜ける

    # 最終的な結果の出力
    print("          ") # 残り時間の表示を消すためスペースで上書き
    
    if not is_cancelled:
        # カウントダウンが完了した場合
        print("✨ カウントダウン終了！")
        # 要求された文字列を出力
        print("ああ")
    else:
        # 中止された場合、次の操作のためにプログラムをすぐに終了させたいので、
        # ここでは追加の出力をせず、コンソールをクリーンに保ちます。
        pass


if __name__ == "__main__":
    countdown_and_print()