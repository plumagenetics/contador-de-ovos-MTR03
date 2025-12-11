import pdfplumber
import re
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import openpyxl

# Variáveis globais
resultados = []
linhas_extraidas = []
ano_escolhido = "2025"  # padrão

# ------------------------------
# 1) EXTRAIR LINHAS DO PDF (COM PROGRESSO)
# ------------------------------
def extrair_linhas_pdf(pdf_path):
    global linhas_extraidas
    global status_label, progress_var, progress_bar, root

    linhas_extraidas = []

    padrao = re.compile(r"\b\d+/\d+\b.*\b\d{2}/\d{2}\b")

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        if total_pages == 0:
            status_label.config(text="PDF sem páginas.")
            return

        progress_bar["maximum"] = total_pages
        progress_var.set(0)
        root.update_idletasks()

        for i, page in enumerate(pdf.pages, start=1):
            status_label.config(text=f"Lendo PDF: página {i} de {total_pages}...")
            progress_var.set(i)
            root.update_idletasks()

            texto = page.extract_text()
            if not texto:
                continue

            for linha in texto.split("\n"):
                linha_limpa = linha.replace("\u00A0", " ")

                if padrao.search(linha_limpa):
                    # print("Linha capturada:", linha_limpa)  # debug opcional
                    linhas_extraidas.append(linha_limpa)

    status_label.config(text=f"Leitura concluída. {len(linhas_extraidas)} linhas encontradas.")
    progress_var.set(0)
    root.update_idletasks()
    print("Total de linhas extraídas:", len(linhas_extraidas))


# ------------------------------
# 2) PARSE DA LINHA
# ------------------------------
def parse_linha(linha):
    tokens = linha.split()
    if len(tokens) < 5:
        return None, None, None

    # DATA É O 2º TOKEN
    txt_data = tokens[1]

    global ano_escolhido

    # Se vier DD/MM, adiciona o ano selecionado
    if len(txt_data) == 5:
        txt_data += "/" + ano_escolhido

    try:
        data = datetime.strptime(txt_data, "%d/%m/%Y")
    except:
        return None, None, None

    nums = re.findall(r"[\d\.]+(?:,\d+)?", linha)

    def to_num(s):
        return float(s.replace(".", "").replace(",", "."))

    if len(nums) < 3:
        return data, None, None

    total = to_num(nums[-3])      # TOTAL
    apr_pct = to_num(nums[-1]) / 100  # %APR

    bons = total * apr_pct

    return data, bons, total


# ------------------------------
# 3) ANALISAR INTERVALO
# ------------------------------
def analisar_intervalo(d_ini, d_fim):
    di = datetime.strptime(d_ini, "%d/%m/%Y")
    df = datetime.strptime(d_fim, "%d/%m/%Y")

    total = 0.0
    bons = 0.0

    if not linhas_extraidas:
        print("Nenhuma linha extraída do PDF.")
        return total, bons

    for linha in linhas_extraidas:
        data, b, t = parse_linha(linha)
        if data is None:
            continue

        if di <= data <= df:
            if b is not None:
                bons += b
            if t is not None:
                total += t

    return total, bons


# ------------------------------
# 4) GERAR INTERVALOS
# ------------------------------
def gerar_intervalos(data_inicio, qtd_intervalos):
    intervalos = []
    data_inicial = datetime.strptime(data_inicio, "%d/%m/%Y")

    for i in range(qtd_intervalos):
        inicio = data_inicial + timedelta(weeks=i)
        fim = inicio + timedelta(days=6)
        intervalos.append((inicio.strftime("%d/%m/%Y"),
                           fim.strftime("%d/%m/%Y")))
    return intervalos


# ------------------------------
# 5) EXPORTAR PARA EXCEL
# ------------------------------
def exportar_para_excel():
    global resultados

    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Resultados"

    sheet.append(["Início", "Fim", "Total Ovos Gerais", "Total Ovos Incubáveis (BONS-A)"])

    for resultado in resultados:
        sheet.append(resultado)

    arquivo_exportado = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx")]
    )

    if arquivo_exportado:
        wb.save(arquivo_exportado)
        messagebox.showinfo("Sucesso", "Arquivo exportado com sucesso!")


# ------------------------------
# 6) BOTÕES (CALCULAR / ANEXAR)
# ------------------------------
def selecionar_arquivo():
    return filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])


def calcular():
    global pdf_path
    global resultados
    global ano_escolhido

    if not pdf_path:
        messagebox.showerror("Erro", "Por favor, selecione um arquivo PDF.")
        return

    d_ini = entry_data_inicio.get()
    qtd_intervalos = int(entry_qtd_intervalos.get())
    ano_escolhido = entry_ano.get().strip()

    if not ano_escolhido.isdigit():
        messagebox.showerror("Erro", "Ano inválido. Digite algo como 2024.")
        return

    btn_calcular.config(state=tk.DISABLED)
    btn_anexar.config(state=tk.DISABLED)

    try:
        intervalos = gerar_intervalos(d_ini, qtd_intervalos)

        for item in tree.get_children():
            tree.delete(item)

        resultados = []

        for inicio, fim in intervalos:
            total, bons = analisar_intervalo(inicio, fim)
            resultados.append((inicio, fim, total, bons))
            tree.insert("", "end", values=(inicio, fim, f"{total:.2f}", f"{bons:.2f}"))

        btn_exportar.config(state=tk.NORMAL)

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

    finally:
        btn_calcular.config(state=tk.NORMAL)
        btn_anexar.config(state=tk.NORMAL)


def anexar_pdf():
    global pdf_path

    pdf_path = selecionar_arquivo()

    if not pdf_path:
        messagebox.showerror("Erro", "Nenhum arquivo foi selecionado.")
        return

    # Atualiza status e desabilita botões durante a leitura
    status_label.config(text="Iniciando leitura do PDF...")
    btn_anexar.config(state=tk.DISABLED)
    btn_calcular.config(state=tk.DISABLED)
    root.update_idletasks()

    try:
        extrair_linhas_pdf(pdf_path)
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao ler o PDF: {e}")
        status_label.config(text="Erro ao ler o PDF.")
    finally:
        btn_anexar.config(state=tk.NORMAL)
        btn_calcular.config(state=tk.NORMAL)


# ------------------------------
# 7) INTERFACE TKINTER
# ------------------------------
root = tk.Tk()
root.title("Analisador de Produção de Ovos")

label_instrucoes = tk.Label(root, text="Selecione o arquivo PDF e insira os intervalos:")
label_instrucoes.pack(pady=10)

label_inicio = tk.Label(root, text="Data Início (dd/mm/aaaa):")
label_inicio.pack()
entry_data_inicio = tk.Entry(root)
entry_data_inicio.pack(pady=5)

label_qtd_intervalos = tk.Label(root, text="Quantos intervalos deseja criar?")
label_qtd_intervalos.pack()
entry_qtd_intervalos = tk.Entry(root)
entry_qtd_intervalos.pack(pady=5)

# CAMPO - ANO DO RELATÓRIO
label_ano = tk.Label(root, text="Ano do relatório (ex: 2024):")
label_ano.pack()
entry_ano = tk.Entry(root)
entry_ano.insert(0, "2024")  # valor padrão
entry_ano.pack(pady=5)

# STATUS DE LEITURA
status_label = tk.Label(root, text="Nenhum PDF carregado.")
status_label.pack(pady=5)

# BARRA DE PROGRESSO
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill="x", padx=20, pady=5)

btn_anexar = tk.Button(root, text="Anexar PDF", command=anexar_pdf)
btn_anexar.pack(pady=10)

btn_calcular = tk.Button(root, text="Calcular", command=calcular)
btn_calcular.pack(pady=10)

tree = ttk.Treeview(
    root,
    columns=("Início", "Fim", "Total Ovos Gerais", "Total Ovos Incubáveis (BONS-A)"),
    show="headings"
)
tree.heading("Início", text="Início")
tree.heading("Fim", text="Fim")
tree.heading("Total Ovos Gerais", text="Total Ovos Gerais")
tree.heading("Total Ovos Incubáveis (BONS-A)", text="Total Ovos Incubáveis (BONS-A)")
tree.pack(pady=20)

btn_exportar = tk.Button(root, text="Exportar para Excel", command=exportar_para_excel, state=tk.DISABLED)
btn_exportar.pack(pady=10)

root.mainloop()
