import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'D:\pyclaw')
sys.path.insert(0, r'D:\pyclaw')

import subprocess
proc = subprocess.Popen(
    [r'D:\pyclaw\python_portable\python.exe', r'D:\pyclaw\webapp.py'],
    cwd=r'D:\pyclaw',
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)
for line in iter(proc.stdout.readline, b''):
    print(line.decode('utf-8', errors='replace').strip())
proc.wait()
