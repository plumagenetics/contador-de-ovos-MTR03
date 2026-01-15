import os
import sys
import time
import socket
import subprocess
import webbrowser
import urllib.request
from contextlib import suppress

# Porta “preferida” (vamos escolher automaticamente uma livre a partir dela)
PREFERRED_PORT = 8501

# Porta apenas para trava de instância única (use uma porta alta para evitar conflito)
LOCK_PORT = 49500

# Timeout para esperar o servidor subir
STARTUP_TIMEOUT = 25


def get_base_dir():
    # Em modo executável (PyInstaller), _MEIPASS aponta para onde os "datas" foram extraídos
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def already_running():
    """
    Trava instância única “reservando” uma porta local.
    Se já estiver em uso, significa que já existe instância rodando.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
        s.listen(1)
        return False, s
    except OSError:
        with suppress(Exception):
            s.close()
        return True, None


def porta_livre(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) != 0


def escolher_porta(inicio=PREFERRED_PORT, tentativas=50):
    """
    Escolhe uma porta livre a partir da porta 'inicio'.
    Evita o caso clássico: 8501 já ocupado e abrir 404 de outro serviço.
    """
    for p in range(inicio, inicio + tentativas):
        if porta_livre(p):
            return p
    raise RuntimeError("Nenhuma porta livre encontrada (8501+).")


def wait_http_ready(url, timeout=STARTUP_TIMEOUT):
    """
    Espera o servidor responder via HTTP (não só TCP).
    Isso evita abrir o browser para um serviço errado na mesma porta.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                # Basta obter qualquer resposta HTTP para considerar “no ar”
                # (Streamlit pode retornar HTML principal logo no início)
                _ = resp.read(200)
                return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    base_dir = get_base_dir()
    os.chdir(base_dir)

    # Proteção extra anti-loop (caso algum cenário reinvoque o processo)
    if os.environ.get("MTR03_LAUNCHED") == "1":
        return
    os.environ["MTR03_LAUNCHED"] = "1"

    running, lock_socket = already_running()

    # Se já existe instância, tente abrir a URL salva (se houver), senão tenta 8501
    url_file = os.path.join(base_dir, ".mtr03_url")
    if running:
        url = None
        with suppress(Exception):
            if os.path.exists(url_file):
                with open(url_file, "r", encoding="utf-8") as f:
                    url = f.read().strip() or None
        if not url:
            url = f"http://127.0.0.1:{PREFERRED_PORT}"
        webbrowser.open(url, new=2)
        return

    # Evita que o Streamlit tente abrir navegador por conta própria
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    # Escolhe uma porta realmente livre
    app_port = escolher_porta(PREFERRED_PORT)
    url = f"http://127.0.0.1:{app_port}"

    # Salva a URL para a próxima instância abrir corretamente
    with suppress(Exception):
        with open(url_file, "w", encoding="utf-8") as f:
            f.write(url)

    app_path = os.path.join(base_dir, "app.py")

    if getattr(sys, "frozen", False):
        # MODO EXECUTÁVEL: roda Streamlit no mesmo processo (evita recursão do sys.executable)
        from streamlit.web import bootstrap

        # Simula argv do streamlit CLI
        sys.argv = [
            "streamlit",
            "run",
            app_path,
            "--server.headless=true",
            f"--server.port={app_port}",
            "--server.fileWatcherType=none",
            "--browser.gatherUsageStats=false",
        ]

        # Abre o navegador quando o HTTP estiver respondendo (ou após timeout)
        # Como bootstrap é bloqueante, fazemos uma pequena tentativa antes
        # e, se não estiver pronto, abrimos mesmo assim após alguns segundos.
        time.sleep(0.5)
        if wait_http_ready(url, timeout=STARTUP_TIMEOUT):
            webbrowser.open(url, new=2)
        else:
            # fallback: abre mesmo assim (mas só uma vez)
            webbrowser.open(url, new=2)

        # Inicia o Streamlit (bloqueante)
        bootstrap.run(app_path, "", [], {})

    else:
        # MODO DEV: subprocess normal
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless=true",
            f"--server.port={app_port}",
            "--browser.gatherUsageStats=false",
            "--server.fileWatcherType=none",
        ]

        # Durante diagnóstico, recomendo logar para arquivo:
        log_path = os.path.join(base_dir, "streamlit.log")
        logf = open(log_path, "a", encoding="utf-8")

        proc = subprocess.Popen(
            cmd,
            stdout=logf,
            stderr=logf,
            cwd=base_dir
        )

        if wait_http_ready(url, timeout=STARTUP_TIMEOUT):
            webbrowser.open(url, new=2)
        else:
            # Se não respondeu, não abra para evitar páginas erradas
            pass

        try:
            while proc.poll() is None:
                time.sleep(1)
        finally:
            with suppress(Exception):
                proc.terminate()
            with suppress(Exception):
                logf.close()

    # Libera trava
    if lock_socket:
        with suppress(Exception):
            lock_socket.close()


if __name__ == "__main__":
    main()
