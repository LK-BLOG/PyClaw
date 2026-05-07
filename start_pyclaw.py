import os
import sys
import subprocess
import time

os.chdir('/home/claw/.openclaw/workspace/pyclaw-public')
sys.path.insert(0, '/home/claw/.openclaw/workspace/pyclaw-public')

# 等待端口释放
time.sleep(2)

print("🚀 正在启动 PyClaw...")
subprocess.run(['python3', 'webapp.py', '--host', '0.0.0.0'])
