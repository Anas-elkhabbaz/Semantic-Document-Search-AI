"""
Semantic Document Search - Startup Script
Runs both backend and frontend servers
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def kill_process_on_port(port: int):
    """Kill any process using the specified port (Windows)"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, capture_output=True, text=True
        )
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            pids_killed = set()
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit() and pid not in pids_killed:
                        try:
                            subprocess.run(
                                f'taskkill /F /PID {pid}',
                                shell=True, capture_output=True
                            )
                            pids_killed.add(pid)
                        except:
                            pass
            
            if pids_killed:
                time.sleep(1)
                return True
    except:
        pass
    return False


def main():
    root_dir = Path(__file__).parent.absolute()
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"
    
    print("🔍 Starting Semantic Document Search...")
    print("=" * 50)
    
    # Cleanup ports
    print("🧹 Checking ports...")
    kill_process_on_port(8000)
    kill_process_on_port(8501)
    
    # Create data directories
    data_dirs = [
        backend_dir / "data" / "uploads",
        backend_dir / "data" / "chroma",
    ]
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Start backend
    print("📦 Starting Backend on http://localhost:8000")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    
    time.sleep(8)  # Wait longer for embedding model to load
    
    # Start frontend
    print("🖥️  Starting Frontend on http://localhost:8501")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"],
        cwd=frontend_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    
    print("=" * 50)
    print("✅ Ready!")
    print("   🔍 App: http://localhost:8501")
    print("   📡 API: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        backend_process.terminate()
        frontend_process.terminate()
        kill_process_on_port(8000)
        kill_process_on_port(8501)
        print("👋 Done!")


if __name__ == "__main__":
    main()
