# elapsed_simple.py
import time

start = time.perf_counter()
print("実行開始。Ctrl+C で終了します。")

try:
    while True:
        # 何もしないで待つ（必要ならここに処理を入れる）
        time.sleep(1)
except KeyboardInterrupt:
    elapsed = time.perf_counter() - start
    print(f"\n終了検知: 経過秒 = {elapsed:.6f} 秒")

# countdown_and_print.py
