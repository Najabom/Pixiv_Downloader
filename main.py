import sys, traceback
from pathlib import Path
from src.cli import CLI


def _crash_log(exc_type, exc_value, exc_tb):
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "crash.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"崩溃时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"异常类型: {exc_type.__name__}\n")
        f.write(f"异常信息: {exc_value}\n")
        f.write("堆栈跟踪:\n")
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    print(f"\n[!] 程序崩溃! 错误详情已写入: {log_path}")
    print(f"[!] {exc_type.__name__}: {exc_value}")
    input("\n按 Enter 退出 ...")


def _main_wrapper():
    try:
        CLI().run()
    except Exception:
        _crash_log(*sys.exc_info())
    except KeyboardInterrupt:
        print("\n用户中断")
        input("\n按 Enter 退出 ...")
    except BaseException:
        _crash_log(*sys.exc_info())


if __name__ == "__main__":
    _main_wrapper()
