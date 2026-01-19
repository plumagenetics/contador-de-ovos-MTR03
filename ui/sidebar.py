# ui/sidebar.py
import streamlit as st
from datetime import date

def render_sidebar():
    with st.sidebar:
        st.header("Entrada")
        pdf_file = st.file_uploader("Anexar PDF", type=["pdf"], accept_multiple_files=False)

        st.divider()
        st.header("Configurações")

        modo = st.radio("Modo de intervalos", ["Automático", "Manual"], horizontal=True)

        data_inicio = st.date_input("Data início", value=date(2025, 1, 1))

        data_fim = None
        qtd_intervalos = None
        dias_por_intervalo = None

        if modo == "Manual":
            data_fim = st.date_input("Data fim", value=date(2025, 1, 7))
        else:
            qtd_intervalos = st.number_input("Quantos intervalos?", min_value=1, max_value=500, value=4, step=1)
            dias_por_intervalo = st.number_input("Dias por intervalo", min_value=1, max_value=365, value=7, step=1)

        ano_escolhido = st.number_input("Ano do relatório", min_value=2000, max_value=2100, value=2025, step=1)

        st.divider()
        executar = st.button("Calcular", use_container_width=True, type="primary")

    return {
        "pdf_file": pdf_file,
        "modo": modo,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "qtd_intervalos": qtd_intervalos,
        "dias_por_intervalo": dias_por_intervalo,
        "ano_escolhido": ano_escolhido,
        "executar": executar,
    }
