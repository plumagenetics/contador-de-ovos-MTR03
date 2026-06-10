# services/session_watchdog.py
import os
import time
import threading

# Config padrao (voce pode ajustar no app.py)
DEFAULT_IDLE_TIMEOUT_SEC = 10       # fecha alguns segundos apos a ultima aba fechar
DEFAULT_WATCH_INTERVAL_SEC = 2      # checar a cada 2s

_SESSIONS_LAST_SEEN: dict[str, float] = {}
_WATCHDOG_STARTED = False
_HAS_EVER_HAD_SESSION = False
_LOCK = threading.Lock()


def _get_session_id() -> str:
    """
    Tenta pegar um identificador de sessao do Streamlit.
    Em algumas versoes pode mudar. Se falhar, usa 'unknown'.
    """
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        return getattr(ctx, "session_id", None) or "unknown"
    except Exception:
        return "unknown"


def _is_streamlit_session_active(session_id: str) -> bool:
    if not session_id or session_id == "unknown":
        return False

    try:
        from streamlit.runtime import get_instance

        return bool(get_instance().is_active_session(session_id))
    except Exception:
        return False


def _watchdog_loop(idle_timeout_sec: int, watch_interval_sec: int):
    while True:
        time.sleep(watch_interval_sec)
        now = time.time()

        with _LOCK:
            # Mantem sessoes realmente ativas vivas, mesmo quando a pagina
            # nao reroda. Isso evita fechar o programa com a aba ainda aberta.
            for sid in list(_SESSIONS_LAST_SEEN):
                if _is_streamlit_session_active(sid):
                    _SESSIONS_LAST_SEEN[sid] = now

            # Remove sessoes sem conexao ha tempo demais.
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
        # Se o session_id nao estiver disponivel, usa fallback "unknown".
        _SESSIONS_LAST_SEEN[sid] = now
        _HAS_EVER_HAD_SESSION = True

        # Inicia o watchdog uma unica vez.
        if not _WATCHDOG_STARTED:
            t = threading.Thread(
                target=_watchdog_loop,
                args=(idle_timeout_sec, watch_interval_sec),
                daemon=True
            )
            t.start()
            _WATCHDOG_STARTED = True
