import platform
import subprocess
import shutil
import json
import os

def get_version(command):
    try:
        return subprocess.check_output([command, "--version"], stderr=subprocess.STDOUT).decode().split('\n')[0].strip()
    except:
        try:
            return subprocess.check_output([command, "version"], stderr=subprocess.STDOUT).decode().split('\n')[0].strip()
        except:
            return None

def run_ps(cmd):
    try:
        return subprocess.check_output(["powershell", "-Command", cmd], stderr=subprocess.STDOUT).decode('utf-8').strip()
    except:
        return ""

def get_hw_info():
    hw = {}
    if platform.system() == "Windows":
        # CPU
        cpu = run_ps("Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name")
        hw["cpu"] = cpu or "Unknown"
        
        # RAM
        mem = run_ps("(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum")
        if mem:
            try:
                hw["ram_gb"] = round(int(mem) / (1024**3), 2)
            except: pass
        
        # GPU
        gpu = run_ps("Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name")
        hw["gpus"] = [g.strip() for g in gpu.split('\n') if g.strip()]
    else:
        hw["cpu"] = platform.processor()
    
    try:
        usage = shutil.disk_usage("/")
        hw["disk_free_gb"] = round(usage.free / (1024**3), 2)
        hw["disk_total_gb"] = round(usage.total / (1024**3), 2)
    except:
        pass
    return hw

def main():
    info = {
        "os": f"{platform.system()} {platform.release()}",
        "shell": shutil.which("pwsh") or shutil.which("powershell") or shutil.which("bash"),
        "hardware": get_hw_info(),
        "runtimes": {},
        "tools": {}
    }

    # Проверка рантаймов
    for rt in ["go", "python", "node", "npm", "java", "docker"]:
        ver = get_version(rt)
        if ver:
            info["runtimes"][rt] = ver

    # Проверка инструментов
    for tool in ["git", "rg", "grep", "make", "kubectl"]:
        path = shutil.which(tool)
        if path:
            info["tools"][tool] = path

    print("=== System Environment Info ===")
    print(json.dumps(info, indent=4))

if __name__ == "__main__":
    main()
