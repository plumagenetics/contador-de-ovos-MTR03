import streamlit as st
import pandas as pd
from datetime import date

from src.pdf_reader import extrair_linhas_pdf
from src.interval_logic import preprocessar_linhas, analisar_intervalo, gerar_intervalos
from src.excel_export import exportar_resultados_excel_bytes

st.set_page_config(
    page_title="Contador MTR03 — Produção de Ovos",
    page_icon="📄",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
      div[data-testid="stMetricValue"] { font-size: 1.6rem; }
      .stDownloadButton button { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Contador MTR03 — Produção de Ovos")
st.caption("Carregue o PDF, defina o intervalo (manual ou automático), visualize os resultados e exporte em Excel.")

# -----------------------------
# Sidebar: entradas
# -----------------------------
with st.sidebar:
    st.header("Entrada")
    pdf_file = st.file_uploader("Anexar PDF", type=["pdf"], accept_multiple_files=False)

    st.divider()
    st.header("Configurações")

    modo = st.radio(
        "Modo de intervalos",
        ["Automático", "Manual"],
        horizontal=True
    )

    data_inicio = st.date_input("Data início", value=date(2025, 1, 1))

    if modo == "Manual":
        data_fim = st.date_input("Data fim", value=date(2025, 1, 7))
    else:
        qtd_intervalos = st.number_input("Quantos intervalos?", min_value=1, max_value=500, value=4, step=1)
        dias_por_intervalo = st.number_input("Dias por intervalo", min_value=1, max_value=365, value=7, step=1)

    ano_escolhido = st.number_input("Ano do relatório", min_value=2000, max_value=2100, value=2025, step=1)

    st.divider()
    executar = st.button("Calcular", use_container_width=True, type="primary")

# -----------------------------
# Estado (para manter resultado)
# -----------------------------
if "linhas_brutas" not in st.session_state:
    st.session_state.linhas_brutas = []
if "linhas_processadas" not in st.session_state:
    st.session_state.linhas_processadas = []
if "resultados" not in st.session_state:
    st.session_state.resultados = []

# -----------------------------
# Funções UI progress/status
# -----------------------------
status_box = st.empty()
progress = st.progress(0)

def status_callback(msg: str):
    status_box.info(msg)

def progress_callback(cur: int, total: int):
    if total <= 0:
        return
    pct = int((cur / total) * 100)
    progress.progress(min(pct, 100))

# -----------------------------
# Execução
# -----------------------------
if executar:
    if not pdf_file:
        st.error("Selecione um PDF antes de calcular.")
        st.stop()

    # Limpa status e progress
    progress.progress(0)
    status_callback("Iniciando leitura do PDF...")

    # Importante: garantir que o ponteiro do arquivo volte ao início
    pdf_file.seek(0)

    # Extrai linhas (com progresso)
    linhas_brutas = extrair_linhas_pdf(
        pdf_file,
        progress_callback=progress_callback,
        status_callback=status_callback
    )

    st.session_state.linhas_brutas = linhas_brutas
    status_callback(f"{len(linhas_brutas)} linhas extraídas do PDF.")

    # Preprocessa
    status_callback("Processando linhas (pré-processamento)...")
    linhas_processadas = preprocessar_linhas(linhas_brutas, str(ano_escolhido))
    st.session_state.linhas_processadas = linhas_processadas

    # Intervalos
    ini_str = data_inicio.strftime("%d/%m/%Y")

    if modo == "Manual":
        fim_str = data_fim.strftime("%d/%m/%Y")
        intervalos = [(ini_str, fim_str)]
    else:
        intervalos = gerar_intervalos(
            ini_str,
            int(qtd_intervalos),
            int(dias_por_intervalo)
        )

    # Calcula
    status_callback("Calculando intervalos...")
    resultados = []
    for (ini, fim) in intervalos:
        total, bons = analisar_intervalo(linhas_processadas, ini, fim)
        resultados.append((ini, fim, total, bons))

    st.session_state.resultados = resultados
    progress.progress(100)
    status_callback("Cálculo concluído.")

# -----------------------------
# Exibição de resultados
# -----------------------------
if st.session_state.resultados:
    resultados = st.session_state.resultados

    # DataFrame para visualizar
    df = pd.DataFrame(resultados, columns=["Início", "Fim", "Total Ovos", "Ovos Bons"])

    # Formatação “bonita” para tela (sem perder valores)
    df_view = df.copy()
    for col in ["Total Ovos", "Ovos Bons"]:
        df_view[col] = df_view[col].round(0).astype(int).map(lambda x: f"{x:,}".replace(",", "."))

    c1, c2, c3 = st.columns(3)
    c1.metric("Intervalos calculados", len(df))
    c2.metric("Total (soma)", int(df["Total Ovos"].sum()))
    c3.metric("Bons (soma)", int(df["Ovos Bons"].sum()))

    st.divider()
    st.subheader("Resultados")

    st.dataframe(df_view, use_container_width=True, height=520)

    st.divider()
    st.subheader("Exportar")

    excel_bytes = exportar_resultados_excel_bytes(resultados)
    st.download_button(
        "Baixar Excel",
        data=excel_bytes,
        file_name="resultados_mtr03.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
else:
    st.info("Carregue um PDF e clique em Calcular para ver os resultados.")
