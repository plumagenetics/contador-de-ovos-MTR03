# services/session_watchdog.py
import os
import time
import threading

# Config padrão (você pode ajustar no app.py)
DEFAULT_IDLE_TIMEOUT_SEC = 3 * 60   # 3 minutos
DEFAULT_WATCH_INTERVAL_SEC = 10     # checar a cada 10s

_SESSIONS_LAST_SEEN: dict[str, float] = {}
_WATCHDOG_STARTED = False
_HAS_EVER_HAD_SESSION = False
_LOCK = threading.Lock()


def _get_session_id() -> str:
    """
    Tenta pegar um identificador de sessão do Streamlit.
    Em algumas versões pode mudar. Se falhar, usa 'unknown'.
    """
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        return getattr(ctx, "session_id", None) or "unknown"
    except Exception:
        return "unknown"


def _watchdog_loop(idle_timeout_sec: int, watch_interval_sec: int):
    while True:
        time.sleep(watch_interval_sec)
        now = time.time()

        with _LOCK:
            # Remove sessões sem heartbeat há tempo demais
            dead = [
                sid for sid, last in _SESSIONS_LAST_SEEN.items()
                if now - last > idle_timeout_sec
            ]
            for sid in dead:
                _SESSIONS_LAST_SEEN.pop(sid, None)

            any_alive = len(_SESSIONS_LAST_SEEN) > 0

        if _HAS_EVER_HAD_SESSION and (not any_alive):
            os._exit(0)


def register_heartbeat(idle_timeout_sec: int = DEFAULT_IDLE_TIMEOUT_SEC,
                       watch_interval_sec: int = DEFAULT_WATCH_INTERVAL_SEC):
    global _WATCHDOG_STARTED, _HAS_EVER_HAD_SESSION

    sid = _get_session_id()
    now = time.time()

    with _LOCK:
        # Só considera "sessão ativa" se existir um session_id real
        if sid != "unknown":
            _SESSIONS_LAST_SEEN[sid] = now
            _HAS_EVER_HAD_SESSION = True

        # Inicia o watchdog uma única vez
        if not _WATCHDOG_STARTED:
            t = threading.Thread(
                target=_watchdog_loop,
                args=(idle_timeout_sec, watch_interval_sec),
                daemon=True
            )
            t.start()
            _WATCHDOG_STARTED = True