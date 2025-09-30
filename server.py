# -*- coding: utf-8 -*-
# Server API untuk XipserCloud Dashboard
# Dijalankan di Termux (membutuhkan 'pkg install python procps-ng util-linux')

import http.server
import socketserver
import json
import os
import socket
import subprocess
import time

PORT = 8080
CONFIG_FILE = 'config.json'
DASHBOARD_FILE = 'dashboard.html'
USERS = {}
DASHBOARD_CONTENT = ""

# --- Fungsi Utility ---
def load_config():
    """Memuat kredensial dari config.json."""
    global USERS
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            USERS[data.get('username')] = data.get('password')
            print(f"[*] Config dimuat: User '{data.get('username')}' siap.")
    except Exception as e:
        print(f"[ERROR] Gagal memuat config atau file tidak ada: {e}")
        exit(1)

def load_dashboard_content():
    """Memuat konten HTML dashboard."""
    global DASHBOARD_CONTENT
    try:
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            DASHBOARD_CONTENT = f.read()
            print(f"[*] Konten '{DASHBOARD_FILE}' dimuat.")
    except Exception as e:
        print(f"[ERROR] Gagal memuat dashboard HTML: {e}")
        exit(1)

def execute_command(command):
    """Menjalankan perintah shell di Termux."""
    print(f"[*] Menjalankan perintah: {command}")
    try:
        # Menggunakan shell=True karena ini dijalankan di Termux
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        output = result.stdout + result.stderr
        status = "SUCCESS" if result.returncode == 0 else "ERROR"
        return status, output
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "Perintah melebihi batas waktu (15 detik)."
    except Exception as e:
        return "CRITICAL_ERROR", str(e)

def get_system_status():
    """Mendapatkan data status sistem REAL-TIME di Termux."""
    status = {}
    
    # Uptime
    try:
        status["uptime"] = execute_command("uptime -p")[1].strip() or "N/A"
    except:
        status["uptime"] = "N/A"

    # RAM (Parsing /proc/meminfo)
    try:
        meminfo = execute_command("cat /proc/meminfo")[1]
        mem_total_kb = 0
        mem_available_kb = 0
        for line in meminfo.split('\n'):
            if "MemTotal:" in line:
                mem_total_kb = int(line.split()[1]) # in KB
            if "MemAvailable:" in line:
                mem_available_kb = int(line.split()[1]) # in KB
        
        if mem_total_kb > 0:
            mem_used_kb = mem_total_kb - mem_available_kb
            # Convert to GB for dashboard display
            status["ram_total_gb"] = round(mem_total_kb / (1024*1024), 2)
            status["ram_used_gb"] = round(mem_used_kb / (1024*1024), 2)
        else:
             raise Exception("MemTotal 0")
            
    except Exception as e:
        status["ram_total_gb"] = 0.0
        status["ram_used_gb"] = 0.0

    # CPU Usage (Parsing 'top' output, membutuhkan procps-ng)
    try:
        # top -n 1 -b: snapshot 1 iterasi, output batch
        top_output = execute_command("top -n 1 -b")[1]
        # Cari baris yang mengandung "%Cpu"
        cpu_line = [line for line in top_output.split('\n') if '%Cpu' in line][0]
        
        # Cari idle percentage (id) - format mungkin bervariasi
        # Contoh: 99.3 id
        idle_str = [part for part in cpu_line.split(',') if 'id' in part][0]
        idle_perc = float(idle_str.strip().split()[0])
        status["cpu_usage"] = round(100.0 - idle_perc, 1) # Usage = 100 - Idle
        
    except Exception as e:
        # Default jika procps-ng belum terinstal atau parsing gagal
        status["cpu_usage"] = 0.0 

    # Load Average
    try:
        load_output = execute_command("cat /proc/loadavg")[1].strip()
        status["load_avg_1m"] = float(load_output.split()[0])
    except:
        status["load_avg_1m"] = 0.0

    status["timestamp"] = time.time()
    return status

def get_local_ip():
    """Mendapatkan alamat IP lokal Termux."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# --- Handler Permintaan HTTP ---
class XipserHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Tambahkan CORS header
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(DASHBOARD_CONTENT.encode('utf-8'))
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps(get_system_status())
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_error(404, "File/Endpoint Tidak Ditemukan")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        if self.path == '/login':
            self._handle_login(data)
        elif self.path == '/api/termux_command':
            self._handle_termux_command(data)
        else:
            self.send_error(404, "Endpoint Tidak Ditemukan")
            
    # --- Handler Khusus POST ---
    def _handle_login(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if USERS.get(username) == password:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"success": True, "message": "Login berhasil!"})
        else:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({"success": False, "message": "Username atau Password salah."})
            
        self.wfile.write(response.encode('utf-8'))

    def _handle_termux_command(self, data):
        command_type = data.get('type')
        
        if command_type == 'update':
            cmd = "pkg update -y && pkg upgrade -y"
            friendly_name = "Update Termux"
        elif command_type == 'unzip_deploy':
            filename = data.get('filename')
            target_dir = data.get('target_dir', os.getcwd())
            domain = data.get('domain')
            # Perintah riil: unzip, diikuti mock config Nginx/DB
            cmd = f"unzip -o '{filename}' -d '{target_dir}' && echo 'File {filename} berhasil di unzip ke {target_dir}' && echo '---' && echo 'SIMULASI: Membuat Nginx config untuk {domain} dan mengaitkannya dengan database...'"
            friendly_name = "Deployment & Unzip"
        elif command_type == 'backup':
            # Perintah backup sederhana (tarball home directory)
            backup_file = f"backup_{time.strftime('%Y%m%d%H%M%S')}.tar.gz"
            cmd = f"tar -czvf {backup_file} $HOME && echo 'Backup berhasil dibuat: {backup_file}'"
            friendly_name = "Backup CLI/Server"
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ERROR", "message": "Perintah tidak valid."}).encode('utf-8'))
            return

        status, output = execute_command(cmd)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Batasi output yang dikirim ke browser
        log_snippet = output[:1000] + ("..." if len(output) > 1000 else "")
        
        response = json.dumps({
            "status": status,
            "message": f"{friendly_name} selesai. Status: {status}",
            "log": log_snippet
        })
        self.wfile.write(response.encode('utf-8'))

# --- Main Program ---
if __name__ == '__main__':
    load_config()
    load_dashboard_content()
    
    IP_ADDRESS = get_local_ip()
    
    try:
        with socketserver.TCPServer((IP_ADDRESS, PORT), XipserHandler) as httpd:
            print("="*50)
            print(f"  ⚡ XipserCloud Server Berjalan ⚡  ")
            print("="*50)
            print(f"  IP Server Lokal Anda: {IP_ADDRESS}")
            print(f"  Port: {PORT}")
            print("-" * 50)
            print(f"  Akses Dashboard di Browser: http://{IP_ADDRESS}:{PORT}")
            print("-" * 50)
            print("  Tekan Ctrl+C untuk menghentikan server. ")
            print("  Aktifkan termux-wake-lock agar tetap berjalan. ")
            print("="*50)
            httpd.serve_forever()
    except OSError as e:
        print(f"\n[CRITICAL ERROR] Gagal memulai server: {e}")
        print("Pastikan port 8080 tidak digunakan atau periksa izin Termux.")
    except KeyboardInterrupt:
        print("\n[INFO] Server dihentikan oleh pengguna.")
