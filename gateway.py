#!/usr/bin/env python3
"""
SuperOutfit Gateway — 统一服务管理

一键启动所有服务：
- FastAPI 后端 (API)
- Vue 前端 (Web UI)
- MCP Server (AI 工具)

用法：
  python gateway.py                    # 启动所有服务
  python gateway.py --port 8000        # 指定 API 端口
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
    import psutil
    
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
    try:
        import psutil
        return psutil.pid_exists(pid)
    except ImportError:
        # 备用方案：Windows
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
        else:
            # Unix: os.kill(pid, 0)
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
        import psutil
        parent = psutil.Process(pid)
        # 先杀子进程
        for child in parent.children(recursive=True):
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        
        # 再杀主进程
        parent.terminate()
        
        # 等待退出
        try:
            parent.wait(timeout=5)
        except psutil.TimeoutExpired:
            parent.kill()
        
        clear_pid()
        return True, "Gateway 已停止"
    except ImportError:
        # 没有 psutil，用系统命令
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                          capture_output=True)
        else:
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


# 子进程管理
class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.services: Dict[str, subprocess.Popen] = {}
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
        
        process = subprocess.Popen(
            cmd,
            cwd=cwd or str(ROOT_DIR),
            env=process_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        self.services[name] = process
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
        while self.running:
            for name, process in list(self.services.items()):
                if process.poll() is not None:
                    # 服务已退出
                    output = process.stdout.read() if process.stdout else ""
                    
                    print(f"\n⚠ {name} 服务已退出 (返回码: {process.returncode})")
                    if output:
                        # 只显示最后 10 行
                        lines = output.strip().split("\n")
                        for line in lines[-10:]:
                            print(f"  {line}")
                    
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
        self.ports = {
            "api": args.port,
            "frontend": args.port + 1,
            "mcp": None,
        }
    
    def find_free_port(self, start_port: int) -> int:
        """查找空闲端口"""
        import socket
        
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        
        return start_port
    
    def start_api(self):
        """启动 FastAPI 后端"""
        # 查找空闲端口
        port = self.find_free_port(self.ports["api"])
        self.ports["api"] = port
        
        cmd = [
            sys.executable, "-m", "uvicorn",
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
            print("  ⚠ 前端目录不存在，跳过")
            return
        
        # 查找空闲端口
        port = self.find_free_port(self.ports["frontend"])
        self.ports["frontend"] = port
        
        if self.args.dev:
            # 开发模式：使用 Vite 热重载
            cmd = ["npm", "run", "dev", "--", "--port", str(port)]
            # Windows 上需要用 shell=True
            if sys.platform == "win32":
                cmd = " ".join(cmd)
        else:
            # 生产模式：构建后使用静态文件
            dist_dir = frontend_dir / "dist"
            if not dist_dir.exists():
                print("  构建前端...")
                # Windows 上 npm 是 .cmd 文件，需要用 shell=True
                try:
                    subprocess.run(
                        ["npm", "run", "build"],
                        cwd=str(frontend_dir),
                        shell=True,
                        check=True
                    )
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"    ⚠ 前端构建失败: {e}")
                    print("    如需前端，请确保 Node.js 和 npm 已安装并加入 PATH")
                    # 创建空的 dist 目录避免后续错误
                    dist_dir.mkdir(exist_ok=True)
                    (dist_dir / "index.html").write_text("<h1>SuperOutfit</h1><p>前端未构建，请确保 Node.js 已安装</p>")
            
            cmd = [sys.executable, "-m", "http.server", str(port), "--directory", str(dist_dir)]
        
        self.manager.start_service("frontend", cmd, cwd=str(frontend_dir))
        print(f"    http://localhost:{port}")
    
    def start_mcp(self):
        """启动 MCP Server"""
        if self.args.no_mcp:
            print("  跳过 MCP 服务")
            return
        
        server_file = ROOT_DIR / "server.py"
        if not server_file.exists():
            print("  ⚠ MCP 服务文件不存在，跳过")
            return
        
        cmd = [sys.executable, "server.py"]
        self.manager.start_service("mcp", cmd)
        print("    stdio://")
    
    def wait_for_services(self, timeout: int = 30):
        """等待服务启动"""
        print("\n等待服务启动...")
        
        import urllib.request
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查 API 服务
            try:
                url = f"http://localhost:{self.ports['api']}/api/health"
                response = urllib.request.urlopen(url, timeout=2)
                if response.status == 200:
                    print("  ✓ 服务已就绪")
                    return True
            except:
                pass
            
            time.sleep(1)
        
        print("  ⚠ 服务启动超时")
        return False
    
    def print_status(self):
        """打印服务状态"""
        print("\n" + "="*60)
        print("  SuperOutfit Gateway 运行中")
        print("="*60)
        print()
        
        status = self.manager.get_status()
        
        for name, info in status.items():
            state = "✓ 运行中" if info["running"] else "✗ 已停止"
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
    parser.add_argument("--port", type=int, default=8001, help="API 端口 (默认: 8001)")
    parser.add_argument("--no-frontend", action="store_true", help="不启动前端")
    parser.add_argument("--no-mcp", action="store_true", help="不启动 MCP")
    parser.add_argument("--dev", action="store_true", help="开发模式")
    parser.add_argument("--daemon", action="store_true", help="后台运行")
    
    args = parser.parse_args()
    
    gateway = Gateway(args)
    gateway.run()


if __name__ == "__main__":
    main()
