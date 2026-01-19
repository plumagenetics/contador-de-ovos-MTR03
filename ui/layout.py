# ui/layout.py
import streamlit as st

def configure_page():
    st.set_page_config(
        page_title="Contador MTR03 — Produção de Ovos",
        page_icon="📄",
        layout="wide",
    )

def apply_styles():
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

def header():
    st.title("Contador MTR03 — Produção de Ovos")
    st.caption("Carregue o PDF, defina o intervalo (manual ou automático), visualize os resultados e exporte em Excel.")
