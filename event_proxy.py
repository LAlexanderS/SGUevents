import os
import sys
import ssl
import time
import json
import threading
import subprocess
import socket
import shutil
from dotenv import load_dotenv, find_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

load_dotenv(find_dotenv(usecwd=True))

DOMAIN = os.getenv("EVENT_DOMAIN", "event.larin.work")
VPS_REMOTE = os.getenv("VPS_REMOTE", "root@107.174.26.138")
# По умолчанию слушаем на всех интерфейсах на VPS, чтобы контейнеры могли достучаться
REMOTE_BIND_HOST = os.getenv("REMOTE_BIND_HOST", "0.0.0.0")
REMOTE_BIND_PORT = int(os.getenv("REMOTE_BIND_PORT", "6100"))
REMOTE_ALSO_BIND_LOCALHOST = os.getenv("REMOTE_ALSO_BIND_LOCALHOST", "1") in ("1", "true", "True", "yes", "on")
LOCAL_HOST = os.getenv("LOCAL_HOST", "127.0.0.1")
LOCAL_PORT = int(os.getenv("LOCAL_PORT", "8000"))
SSH_BIN = os.getenv("SSH_BIN", "ssh")
SSH_PORT = os.getenv("SSH_PORT")  # optional
SSH_IDENTITY = os.getenv("SSH_IDENTITY")  # приватный ключ (опционально)
SSH_PASSWORD = os.getenv("SSH_PASSWORD")  # пароль (опционально)
SSH_HOSTKEY = os.getenv("SSH_HOSTKEY")  # опционально: отпечаток хост-ключа для plink
RECONNECT_DELAY_SEC = float(os.getenv("RECONNECT_DELAY_SEC", "3"))
HEALTHCHECK_TIMEOUT_SEC = float(os.getenv("HEALTHCHECK_TIMEOUT_SEC", "5"))
SSH_IDENTITY = os.getenv("SSH_IDENTITY")  # приватный ключ (опционально)
SSH_PASSWORD = os.getenv("SSH_PASSWORD")  # пароль (опционально, используем sshpass если задан)
RECONNECT_DELAY_SEC = float(os.getenv("RECONNECT_DELAY_SEC", "3"))
HEALTHCHECK_TIMEOUT_SEC = float(os.getenv("HEALTHCHECK_TIMEOUT_SEC", "5"))


def is_port_listening(host: str, port: int, timeout_sec: float = 0.6) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_sec)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass


class ProbeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/healthz"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return

        if self.path.startswith("/whoami"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            headers = {k: v for k, v in self.headers.items()}
            payload = {
                "path": self.path,
                "client_addr": self.client_address[0],
                "headers": headers,
            }
            self.wfile.write(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        msg = f"hello from local test server on {self.server.server_address}\n"
        self.wfile.write(msg.encode("utf-8"))

    def log_message(self, fmt, *args):
        sys.stdout.write("[REQ] " + (fmt % args) + "\n")


def ensure_local_http_server(host: str, preferred_port: int) -> int:
    if is_port_listening(host, preferred_port):
        sys.stdout.write(f"[LOCAL] {host}:{preferred_port} already listening\n")
        return preferred_port
    sys.stdout.write(f"[LOCAL] {host}:{preferred_port} is empty, starting minimal HTTP\n")

    bound_port_holder = {"port": None}

    def _run(bind_host: str, first_port: int):
        server = None
        last_error = None
        for candidate in (first_port, 0):
            try:
                server = HTTPServer((bind_host, candidate), ProbeHandler)
                break
            except OSError as e:
                last_error = e
                continue
        if server is None:
            raise SystemExit(f"[LOCAL][ERR] failed to bind local HTTP on {bind_host}:{first_port} (last error: {last_error})")
        bound_host, bound_port = server.server_address
        bound_port_holder["port"] = bound_port
        sys.stdout.write(f"[LOCAL] HTTP listening on http://{bound_host}:{bound_port}\n")
        server.serve_forever()

    t = threading.Thread(target=_run, args=(host, preferred_port), daemon=True)
    t.start()
    # wait until it is up (max ~10s)
    deadline = time.time() + 10.0
    while time.time() < deadline:
        p = bound_port_holder["port"]
        if p is not None and is_port_listening(host, p):
            return p
        time.sleep(0.2)
    raise SystemExit(f"[LOCAL][ERR] failed to start local HTTP on {host}:{preferred_port}")


def health_check_loop(domain: str, stop_flag: threading.Event) -> None:
    ctx = ssl.create_default_context()
    url_health = f"https://{domain}/healthz"
    url_who = f"https://{domain}/whoami"
    while not stop_flag.is_set():
        try:
            with urlopen(Request(url_health, headers={"User-Agent": "event-proxy/1"}), timeout=HEALTHCHECK_TIMEOUT_SEC, context=ctx) as r:
                body = r.read().decode("utf-8", errors="replace")
                if body.strip().startswith("ok"):
                    sys.stdout.write(f"[OK] {url_health} => ok\n")
                    try:
                        with urlopen(Request(url_who, headers={"User-Agent": "event-proxy/1"}), timeout=HEALTHCHECK_TIMEOUT_SEC, context=ctx) as rw:
                            who = rw.read().decode("utf-8", errors="replace")
                            sys.stdout.write("[WHOAMI]\n" + who + "\n")
                    except Exception as e:
                        sys.stdout.write(f"[WHOAMI][ERR] {e}\n")
                    break
        except (URLError, HTTPError) as e:
            pass
        except Exception as e:
            pass
        time.sleep(2)


def build_ssh_command(local_port: int) -> list:
    reverse_rules = [f"{REMOTE_BIND_HOST}:{REMOTE_BIND_PORT}:{LOCAL_HOST}:{local_port}"]
    if REMOTE_ALSO_BIND_LOCALHOST and REMOTE_BIND_HOST != "127.0.0.1":
        reverse_rules.append(f"127.0.0.1:{REMOTE_BIND_PORT}:{LOCAL_HOST}:{local_port}")
    cmd = [
        SSH_BIN,
        "-v",
        "-N",
        # Парольная аутентификация без попыток ключей (как у тебя работало)
        "-o", "PreferredAuthentications=password",
        "-o", "PubkeyAuthentication=no",
        "-o", "PasswordAuthentication=yes",
        # Принимаем новый host key автоматически
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
    ]
    for rr in reverse_rules:
        cmd += ["-R", rr]
    if SSH_PORT:
        cmd += ["-p", str(SSH_PORT)]
    cmd.append(VPS_REMOTE)
    return cmd


def run():
    effective_local_port = ensure_local_http_server(LOCAL_HOST, LOCAL_PORT)

    stop_flag = threading.Event()
    checker = threading.Thread(target=health_check_loop, args=(DOMAIN, stop_flag), daemon=True)
    checker.start()

    sys.stdout.write("[INFO] event-proxy туннель запускается. Нажми 'q' + Enter для остановки.\n")
    sys.stdout.write(f"[ENV] SSH_PASSWORD: {'set' if os.getenv('SSH_PASSWORD') else 'not set'}; SSH_BIN={SSH_BIN}\n")
    sys.stdout.write(f"[BIND] remote will listen on: {REMOTE_BIND_HOST}:{REMOTE_BIND_PORT}"
                     + (" and 127.0.0.1:" + str(REMOTE_BIND_PORT) if REMOTE_ALSO_BIND_LOCALHOST and REMOTE_BIND_HOST != '127.0.0.1' else "")
                     + f" -> {LOCAL_HOST}:{LOCAL_PORT}\n")

    proc: subprocess.Popen | None = None

    def _spawn_process():
        nonlocal proc
        cmd = build_ssh_command(effective_local_port)
        sys.stdout.write("[SSH] " + " ".join(cmd) + "\n")
        try:
            proc = subprocess.Popen(cmd)
        except FileNotFoundError as e:
            sys.stdout.write(f"[ERR] Не найден бинарь SSH/sshpass: {e}\n")
            return False
        return True

    def _input_watcher():
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                if line.strip().lower() == 'q':
                    sys.stdout.write("[CTRL] Stop requested. Terminating SSH...\n")
                    try:
                        if proc and proc.poll() is None:
                            proc.terminate()
                    except Exception:
                        pass
                    stop_flag.set()
                    break
        except Exception:
            pass

    threading.Thread(target=_input_watcher, daemon=True).start()

    try:
        while not stop_flag.is_set():
            if proc is None or proc.poll() is not None:
                # если нет процесса или он завершился — перезапускаем
                if proc is not None:
                    sys.stdout.write(f"[SSH] exited with code {proc.returncode}, reconnect in {RECONNECT_DELAY_SEC}s...\n")
                if not _spawn_process():
                    break
            # ждём немного, затем проверяем домен
            time.sleep(RECONNECT_DELAY_SEC)
    except KeyboardInterrupt:
        sys.stdout.write("\n[SSH] interrupted by user, terminating...\n")
    finally:
        try:
            if proc and proc.poll() is None:
                proc.terminate()
        except Exception:
            pass
        stop_flag.set()


if __name__ == "__main__":
    run()


