import pdfplumber
import re

PADRAO_LINHA = re.compile(r"\b\d+/\d+\b.*\b\d{2}/\d{2}\b")

def extrair_linhas_pdf(pdf_file, progress_callback=None, status_callback=None):
    """
    Lê o PDF e retorna apenas as linhas relevantes.

    pdf_file pode ser:
    - caminho (str)
    - arquivo em memória (BytesIO / UploadedFile do Streamlit)
    """

    linhas = []

    with pdfplumber.open(pdf_file) as pdf:
        total_pages = len(pdf.pages)

        for i, page in enumerate(pdf.pages, start=1):
            if status_callback:
                status_callback(f"Lendo PDF: página {i}/{total_pages}...")

            if progress_callback:
                progress_callback(i, total_pages)

            texto = page.extract_text()
            if not texto:
                continue

            for linha in texto.split("\n"):
                if "/" not in linha:
                    continue

                linha_limpa = linha.replace("\u00A0", " ")

                if PADRAO_LINHA.search(linha_limpa):
                    linhas.append(linha_limpa)

    return linhas
