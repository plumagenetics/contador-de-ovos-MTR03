import os
import sys
import time
import threading
import webbrowser
import traceback
from pathlib import Path

def _base_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

def _log_path() -> Path:
    # grava log ao lado do exe (funciona no onedir)
    return Path(sys.executable).resolve().parent / "mtr03_launcher.log"

def _write_log(text: str):
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass

def _open_browser_once(url: str):
    if os.environ.get("MTR03_BROWSER_OPENED") == "1":
        return
    os.environ["MTR03_BROWSER_OPENED"] = "1"
    time.sleep(1.2)
    webbrowser.open(url)

def main():
    # desliga watchdog durante debug do exe
    os.environ["MTR03_DISABLE_WATCHDOG"] = "1"
    # força modo não-dev do Streamlit (evita Node dev server / porta 3000)
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["STREAMLIT_SERVER_RUN_ON_SAVE"] = "false"
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

    # ---------- PASTA LIMPA DE CONFIG DO STREAMLIT ----------
    # Impede o Streamlit de ler ~/.streamlit/config.toml do usuário
    tmp_cfg = Path(os.environ.get("TEMP", str(Path.cwd()))) / "mtr03_streamlit_cfg"
    tmp_cfg.mkdir(parents=True, exist_ok=True)

    os.environ["STREAMLIT_CONFIG_DIR"] = str(tmp_cfg)

    base = _base_dir()
    app_py = base / "app.py"

    _write_log("=== START ===")
    _write_log(f"sys.executable: {sys.executable}")
    _write_log(f"base: {base}")
    _write_log(f"app_py exists: {app_py.exists()} path={app_py}")

    if not app_py.exists():
        raise FileNotFoundError(f"Não achei app.py em: {app_py}")

    # abre navegador (uma vez)
    threading.Thread(target=_open_browser_once, args=("http://localhost:8501",), daemon=True).start()

    # roda streamlit dentro do processo
    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        str(app_py),
        "--server.headless=true",
        "--server.fileWatcherType=none",
        "--server.runOnSave=false",
        "--browser.gatherUsageStats=false",
    ]

    _write_log("Calling streamlit cli...")
    stcli.main()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        _write_log("CRASH:\n" + traceback.format_exc())
        # segura um pouquinho pra você conseguir ver a tela preta se rodar clicando
        time.sleep(2)
        raise
