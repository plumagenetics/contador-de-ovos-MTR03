# ui/results.py
import streamlit as st
import pandas as pd

from src.excel_export import exportar_resultados_excel_bytes

def render_results(resultados):
    df = pd.DataFrame(resultados, columns=["Início", "Fim", "Total Ovos", "Ovos Bons"])

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
