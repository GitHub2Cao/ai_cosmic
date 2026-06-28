# COSMIC 智能文档转换平台 — 启动入口
# Phase 1: 统一启动前后端

import os
import sys
import subprocess
import time
import signal

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

backend_proc = None
frontend_proc = None


def cleanup(signum=None, frame=None):
    print("\n[Shutdown] 正在关闭服务...")
    if backend_proc:
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            backend_proc.kill()
    if frontend_proc:
        frontend_proc.terminate()
        try:
            frontend_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            frontend_proc.kill()
    print("[Shutdown] 服务已关闭")
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)

    # 启动后端
    print("[Backend] 安装依赖...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        cwd=BACKEND_DIR,
    )
    print("[Backend] 启动 FastAPI...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd=BACKEND_DIR,
        env={**os.environ, "COSMIC_ENV": "dev"},
    )

    # 等待后端就绪
    for i in range(30):
        time.sleep(0.5)
        try:
            import urllib.request

            urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1)
            print("[Backend] 已就绪 🟢")
            break
        except Exception:
            if i == 29:
                print("[Backend] 启动超时，请检查日志")
            pass

    # 启动前端
    if os.path.exists(os.path.join(FRONTEND_DIR, "node_modules", ".package-lock.json")):
        print("[Frontend] 已安装 node_modules，跳过 install")
    else:
        print("[Frontend] 安装依赖...")
        subprocess.check_call(["npm", "install"], cwd=FRONTEND_DIR)
    print("[Frontend] 启动 Vite...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", "--port", "5173"],
        cwd=FRONTEND_DIR,
    )

    print("\n========================================")
    print(" COSMIC 平台已启动")
    print("")
    print(" 前端: http://localhost:5173")
    print(" 后端: http://localhost:8000")
    print(" API文档: http://localhost:8000/docs")
    print("========================================\n")
    print("按 Ctrl+C 关闭服务")

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
