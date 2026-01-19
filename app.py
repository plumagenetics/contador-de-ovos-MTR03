# app.py
import streamlit as st
import os

from ui.layout import configure_page, apply_styles, header
from ui.sidebar import render_sidebar
from ui.results import render_results

from services.session_watchdog import register_heartbeat

from src.pdf_reader import extrair_linhas_pdf
from src.interval_logic import preprocessar_linhas, analisar_intervalo, gerar_intervalos


# ---- Config do watchdog (fecha o programa inteiro) ----
IDLE_TIMEOUT_SEC = 3 * 60     # 3 min sem nenhuma aba conectada -> fecha
WATCH_INTERVAL_SEC = 10       # checa a cada 10s

# Registra heartbeat (faz o app fechar sozinho quando ninguém estiver usando)
if os.environ.get("MTR03_DISABLE_WATCHDOG") != "1":
    register_heartbeat(IDLE_TIMEOUT_SEC, WATCH_INTERVAL_SEC)

# ---- UI base ----
configure_page()
apply_styles()
header()

# ---- Inputs ----
cfg = render_sidebar()

# ---- Session State ----
st.session_state.setdefault("linhas_brutas", [])
st.session_state.setdefault("linhas_processadas", [])
st.session_state.setdefault("resultados", [])

# ---- UI progress/status ----
status_box = st.empty()
progress = st.progress(0)

def status_callback(msg: str):
    status_box.info(msg)

def progress_callback(cur: int, total: int):
    if total <= 0:
        return
    pct = int((cur / total) * 100)
    progress.progress(min(pct, 100))

# ---- Execução ----
if cfg["executar"]:
    pdf_file = cfg["pdf_file"]
    if not pdf_file:
        st.error("Selecione um PDF antes de calcular.")
        st.stop()

    progress.progress(0)
    status_box.empty()
    status_callback("Iniciando leitura do PDF...")

    pdf_file.seek(0)

    linhas_brutas = extrair_linhas_pdf(
        pdf_file,
        progress_callback=progress_callback,
        status_callback=status_callback
    )

    if not linhas_brutas:
        st.error("Nenhuma linha válida encontrada no PDF.")
        st.stop()

    st.session_state.linhas_brutas = linhas_brutas
    status_callback(f"{len(linhas_brutas)} linhas extraídas do PDF.")

    status_callback("Processando linhas (pré-processamento)...")
    linhas_processadas = preprocessar_linhas(linhas_brutas, str(cfg["ano_escolhido"]))
    st.session_state.linhas_processadas = linhas_processadas

    ini_str = cfg["data_inicio"].strftime("%d/%m/%Y")

    if cfg["modo"] == "Manual":
        fim_str = cfg["data_fim"].strftime("%d/%m/%Y")
        intervalos = [(ini_str, fim_str)]
    else:
        intervalos = gerar_intervalos(
            ini_str,
            int(cfg["qtd_intervalos"]),
            int(cfg["dias_por_intervalo"])
        )

    status_callback("Calculando intervalos...")
    resultados = []
    for (ini, fim) in intervalos:
        total, bons = analisar_intervalo(linhas_processadas, ini, fim)
        resultados.append((ini, fim, total, bons))

    st.session_state.resultados = resultados
    progress.progress(100)
    status_callback("Cálculo concluído.")

# ---- Render ----
if st.session_state.resultados:
    render_results(st.session_state.resultados)
else:
    st.info("Carregue um PDF e clique em Calcular para ver os resultados.")
