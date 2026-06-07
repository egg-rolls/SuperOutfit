#!/usr/bin/env python3
"""
SuperOutfit Gateway — 统一服务管理

一键启动所有服务：
- FastAPI 后端 (API)
- Vue 前端 (Web UI)
- MCP Server (AI 工具)

用法：
  python gateway.py                    # 启动所有服务
  python gateway.py --port 32200       # 指定端口
  python gateway.py --no-frontend      # 不启动前端
  python gateway.py --no-mcp           # 不启动 MCP
  python gateway.py --dev              # 开发模式（前端热重载）
  python gateway.py --daemon           # 后台运行
"""

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# 项目根目录
ROOT_DIR = Path(__file__).parent

# PID 文件管理
PID_FILE = ROOT_DIR / ".superoutfit.pid"


def save_pid(api_port: int, frontend_port: int = None, mcp_port: int = None):
    """保存 Gateway PID 信息"""
    pid_data = {
        "pid": os.getpid(),
        "started_at": time.time(),
        "ports": {
            "api": api_port,
            "frontend": frontend_port,
            "mcp": mcp_port,
        },
        "services": {}
    }
    
    PID_FILE.write_text(json.dumps(pid_data, indent=2))


def update_service_pid(name: str, pid: int):
    """更新服务 PID"""
    if PID_FILE.exists():
        data = json.loads(PID_FILE.read_text())
        data["services"][name] = pid
        PID_FILE.write_text(json.dumps(data, indent=2))


def load_pid() -> dict:
    """读取 PID 文件"""
    if PID_FILE.exists():
        try:
            return json.loads(PID_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return None


def clear_pid():
    """清除 PID 文件"""
    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)


def is_process_running(pid: int) -> bool:
    """检查进程是否在运行"""
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x00100000
        handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            pass
    return False


def stop_gateway():
    """停止 Gateway 进程"""
    data = load_pid()
    if not data:
        return False, "Gateway 未运行"
    
    pid = data["pid"]
    if not is_process_running(pid):
        clear_pid()
        return False, "Gateway 进程已退出"
    
    try:
        if sys.platform == "win32":
            # Windows: 用 taskkill 杀进程树
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], 
                          capture_output=True)
        else:
            # Unix: 发送 SIGTERM
            os.kill(pid, signal.SIGTERM)
        
        clear_pid()
        return True, "Gateway 已停止"
    except Exception as e:
        return False, f"停止失败: {e}"


def get_gateway_status() -> dict:
    """获取 Gateway 状态"""
    data = load_pid()
    if not data:
        return {"running": False, "message": "Gateway 未运行"}
    
    pid = data["pid"]
    if not is_process_running(pid):
        clear_pid()
        return {"running": False, "message": "Gateway 进程已退出（PID 文件已清理）"}
    
    return {
        "running": True,
        "pid": pid,
        "started_at": data.get("started_at"),
        "ports": data.get("ports", {}),
        "services": data.get("services", {}),
    }


def get_venv_python():
    """获取 venv 中的 Python 路径"""
    # 检查当前目录是否有 .venv
    venv_paths = [
        Path.cwd() / ".venv" / "Scripts" / "python.exe",  # Windows
        Path.cwd() / ".venv" / "bin" / "python",  # Unix
    ]
    
    for p in venv_paths:
        if p.exists():
            return str(p)
    
    # 检查项目根目录
    project_root = Path(__file__).parent
    venv_paths = [
        project_root / ".venv" / "Scripts" / "python.exe",
        project_root / ".venv" / "bin" / "python",
    ]
    
    for p in venv_paths:
        if p.exists():
            return str(p)
    
    # 回退到当前 Python
    return sys.executable


# 子进程管理
class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.services: Dict[str, subprocess.Popen] = {}
        self._log_files: Dict[str, object] = {}
        self.running = True

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        print("\n\n收到停止信号，正在关闭服务...")
        self.stop_all()
        sys.exit(0)
    
    def start_service(self, name: str, cmd: list, cwd: str = None, env: dict = None) -> subprocess.Popen:
        """启动服务"""
        print(f"  启动 {name}...")

        # 合并环境变量
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # 将子进程输出重定向到日志文件，避免 PIPE 缓冲区满导致死锁
        log_dir = ROOT_DIR / ".logs"
        log_dir.mkdir(exist_ok=True)
        log_file = open(log_dir / f"{name}.log", "a", encoding="utf-8")

        process = subprocess.Popen(
            cmd,
            cwd=cwd or str(ROOT_DIR),
            env=process_env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

        self.services[name] = process
        self._log_files[name] = log_file
        update_service_pid(name, process.pid)
        return process
    
    def stop_service(self, name: str):
        """停止服务"""
        if name in self.services:
            process = self.services[name]

            if process.poll() is None:
                print(f"  停止 {name}...")
                process.terminate()

                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

            # 关闭日志文件句柄
            if name in self._log_files:
                try:
                    self._log_files[name].close()
                except Exception:
                    pass
                del self._log_files[name]

            del self.services[name]
    
    def stop_all(self):
        """停止所有服务"""
        self.running = False
        
        for name in list(self.services.keys()):
            self.stop_service(name)
        
        clear_pid()
        print("所有服务已停止")
    
    def get_status(self) -> Dict[str, dict]:
        """获取服务状态"""
        status = {}
        
        for name, process in self.services.items():
            status[name] = {
                "pid": process.pid,
                "running": process.poll() is None,
                "returncode": process.returncode,
            }
        
        return status
    
    def monitor(self):
        """监控服务"""
        reported_exit = set()

        while self.running:
            for name, process in list(self.services.items()):
                if process.poll() is not None:
                    # 服务已退出
                    if name not in reported_exit:
                        print(f"\n[WARN] {name} 服务已退出 (返回码: {process.returncode})")
                        # 从日志文件读取最后几行输出
                        log_path = ROOT_DIR / ".logs" / f"{name}.log"
                        if log_path.exists():
                            try:
                                lines = log_path.read_text(encoding="utf-8", errors="replace").strip().split("\n")
                                for line in lines[-10:]:
                                    print(f"  {line}")
                            except Exception:
                                pass

                        reported_exit.add(name)

                    # 如果是 API 服务退出，停止所有服务
                    if name == "api":
                        print("\nAPI 服务退出，停止所有服务...")
                        self.stop_all()
                        return

            time.sleep(1)


class Gateway:
    """服务网关"""
    
    def __init__(self, args):
        self.args = args
        self.manager = ServiceManager()
        self.python = get_venv_python()
        self._allocated_ports = set()  # 已分配的端口，防止竞态
        self.ports = {
            "api": args.port,
            "frontend": args.port,  # 生产模式与 API 同端口，dev 模式会覆盖
            "mcp": None,
        }
        # dev 模式下前端从 API 端口+1 开始查找，确保 Vite proxy 指向正确的 API 端口
        self._frontend_start_port = args.port + 1
    
    def find_free_port(self, start_port: int) -> int:
        """查找空闲端口（排除已分配的端口）"""
        import socket
        
        for port in range(start_port, start_port + 100):
            if port in self._allocated_ports:
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
                    s.bind(('', port))
                    # bind 成功，立刻关闭并记录为已分配
                    # 进程启动前不会再被其他服务抢占
                    return port
            except OSError:
                continue
        
        return start_port
    
    def start_api(self):
        """启动 FastAPI 后端"""
        # 查找空闲端口
        port = self.find_free_port(self.ports["api"])
        self.ports["api"] = port
        self._allocated_ports.add(port)
        
        cmd = [
            self.python, "-m", "uvicorn",
            "api.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
        ]
        
        if self.args.dev:
            cmd.append("--reload")
        
        self.manager.start_service("api", cmd)
        print(f"    http://localhost:{port}")
    
    def start_frontend(self):
        """启动 Vue 前端"""
        if self.args.no_frontend:
            print("  跳过前端服务")
            return
        
        frontend_dir = ROOT_DIR / "frontend"
        if not frontend_dir.exists():
            print("  [WARN] 前端目录不存在，跳过")
            return
        
        if self.args.dev:
            # 开发模式：使用 Vite 热重载（独立端口）
            # 从 API 端口+1 开始查找，确保 Vite proxy 指向正确的 API 端口
            port = self.find_free_port(self._frontend_start_port)
            self.ports["frontend"] = port
            self._allocated_ports.add(port)
            
            cmd = ["npm", "run", "dev", "--", "--port", str(port)]
            if sys.platform == "win32":
                cmd = " ".join(cmd)
            self.manager.start_service("frontend", cmd, cwd=str(frontend_dir))
            print(f"    http://localhost:{port}")
        else:
            # 生产模式：FastAPI 直接从 dist/ 提供前端，无需单独服务
            # 只确保 dist/ 存在
            dist_dir = frontend_dir / "dist"
            if not dist_dir.exists() or not (dist_dir / "index.html").exists():
                print("  构建前端...")
                try:
                    subprocess.run(
                        ["npm", "run", "build"],
                        cwd=str(frontend_dir),
                        shell=True,
                        check=True
                    )
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"    [WARN] 前端构建失败: {e}")
                    print("    如需前端，请确保 Node.js 和 npm 已安装并加入 PATH")
                    dist_dir.mkdir(exist_ok=True)
                    (dist_dir / "index.html").write_text("<h1>SuperOutfit</h1><p>前端未构建</p>")
            
            # 前端与 API 共享同一端口
            self.ports["frontend"] = self.ports["api"]
            print(f"    http://localhost:{self.ports['api']} (与 API 同端口)")
    
    def start_mcp(self):
        """启动 MCP Server"""
        if self.args.no_mcp:
            print("  跳过 MCP 服务 (stdio 服务需由 MCP 客户端启动)")
            return
        
        # MCP 是 stdio 服务，不适合由 gateway 启动
        # 由 MCP 客户端 (如 Claude Desktop) 直接启动
        print("  MCP 服务: 由 MCP 客户端启动 (stdio://)")
        print("    配置: .agent-configs/mcp.json")
    
    def wait_for_services(self, timeout: int = 30):
        """等待服务启动"""
        print("\n等待服务启动...")
        
        import urllib.request
        
        api_ok = False
        frontend_ok = False
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查 API 服务
            if not api_ok:
                try:
                    url = f"http://localhost:{self.ports['api']}/api/health"
                    response = urllib.request.urlopen(url, timeout=2)
                    if response.status == 200:
                        api_ok = True
                except Exception:
                    pass
            
            # 检查前端服务（仅在有独立前端端口时）
            frontend_port = self.ports.get("frontend")
            if not frontend_ok and frontend_port and frontend_port != self.ports["api"]:
                try:
                    url = f"http://localhost:{frontend_port}/"
                    response = urllib.request.urlopen(url, timeout=2)
                    if response.status == 200:
                        frontend_ok = True
                except Exception:
                    pass
            elif frontend_port == self.ports["api"]:
                # 前端和 API 同端口，API 就绪即前端就绪
                frontend_ok = api_ok
            
            if api_ok and frontend_ok:
                print("  [OK] 服务已就绪")
                return True
            
            time.sleep(1)
        
        # 超时后报告具体哪个没就绪
        if not api_ok:
            print("  [WARN] API 服务启动超时")
        if not frontend_ok:
            print("  [WARN] 前端服务启动超时")
        return False
    
    def print_status(self):
        """打印服务状态"""
        print("\n" + "="*60)
        print("  SuperOutfit Gateway 运行中")
        print("="*60)
        print()
        
        status = self.manager.get_status()
        
        for name, info in status.items():
            state = "[OK] 运行中" if info["running"] else "[X] 已停止"
            port = self.ports.get(name)
            url = f"http://localhost:{port}" if port else "stdio://"
            
            print(f"  {name.upper():<12} {state:<12} {url}")
        
        print()
        print("  按 Ctrl+C 停止所有服务")
        print("="*60)
        print()
    
    def run(self):
        """运行网关"""
        print("\n" + "="*60)
        print("  SuperOutfit Gateway 启动中...")
        print("="*60)
        print()
        
        # 启动服务
        print("启动服务：")
        self.start_api()
        self.start_frontend()
        self.start_mcp()
        
        # 保存 PID
        save_pid(
            self.ports["api"],
            self.ports.get("frontend"),
            self.ports.get("mcp")
        )
        
        # 等待服务启动
        self.wait_for_services()
        
        # 打印状态
        self.print_status()
        
        # 监控服务
        self.manager.monitor()


def main():
    parser = argparse.ArgumentParser(description="SuperOutfit Gateway")
    parser.add_argument("--port", type=int, default=32200, help="端口 (默认: 32200, API+前端同端口)")
    parser.add_argument("--no-frontend", action="store_true", help="不启动前端")
    parser.add_argument("--no-mcp", action="store_true", help="不启动 MCP")
    parser.add_argument("--dev", action="store_true", help="开发模式")
    parser.add_argument("--daemon", action="store_true", help="后台运行")
    
    args = parser.parse_args()
    
    gateway = Gateway(args)
    gateway.run()


if __name__ == "__main__":
    main()
