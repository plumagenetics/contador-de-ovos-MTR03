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
ano_escolhido = "2025"
pdf_path = None


# ============================================================
# 1) EXTRAIR LINHAS DO PDF
# ============================================================
def extrair_linhas_pdf(pdf_path):
    global linhas_extraidas
    linhas_extraidas = []

    padrao = re.compile(r"\b\d+/\d+\b.*\b\d{2}/\d{2}\b")

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        progress_bar["maximum"] = total_pages
        progress_var.set(0)
        root.update_idletasks()

        for i, page in enumerate(pdf.pages, start=1):
            status_label.config(text=f"Lendo PDF: página {i}/{total_pages}...")
            progress_var.set(i)
            root.update_idletasks()

            texto = page.extract_text()
            if not texto:
                continue

            for linha in texto.split("\n"):
                linha_limpa = linha.replace("\u00A0", " ")
                if padrao.search(linha_limpa):
                    linhas_extraidas.append(linha_limpa)

    status_label.config(text=f"{len(linhas_extraidas)} linhas encontradas.")
    progress_var.set(0)


# ============================================================
# 2) PARSE DE CADA LINHA
# ============================================================
def parse_linha(linha):
    tokens = linha.split()
    if len(tokens) < 5:
        return None, None, None

    txt_data = tokens[1]

    global ano_escolhido
    if len(txt_data) == 5:
        txt_data += "/" + ano_escolhido

    try:
        data = datetime.strptime(txt_data, "%d/%m/%Y")
    except:
        return None, None, None

    nums = re.findall(r"[\d\.]+(?:,\d+)?", linha)

    def to_num(s): return float(s.replace(".", "").replace(",", "."))

    if len(nums) < 3:
        return data, None, None

    total = to_num(nums[-3])
    apr_pct = to_num(nums[-1]) / 100
    bons = total * apr_pct

    return data, bons, total


# ============================================================
# 3) ANALISAR INTERVALO
# ============================================================
def analisar_intervalo(d_ini, d_fim):
    di = datetime.strptime(d_ini, "%d/%m/%Y")
    df = datetime.strptime(d_fim, "%d/%m/%Y")

    total = 0
    bons = 0

    for linha in linhas_extraidas:
        data, b, t = parse_linha(linha)
        if data and di <= data <= df:
            if b: bons += b
            if t: total += t

    return total, bons


# ============================================================
# 4) GERAR INTERVALOS AUTOMÁTICOS
# ============================================================
def gerar_intervalos(data_inicio, qtd_intervalos, dias_intervalo):
    intervalos = []
    inicio = datetime.strptime(data_inicio, "%d/%m/%Y")

    for i in range(qtd_intervalos):
        ini = inicio + timedelta(days=i * dias_intervalo)
        fim = ini + timedelta(days=dias_intervalo - 1)
        intervalos.append((ini.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y")))

    return intervalos


# ============================================================
# 5) EXPORTAR PARA EXCEL
# ============================================================
def exportar_para_excel():
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Resultados"

    sheet.append(["Início", "Fim", "Total Ovos Gerais", "Total Ovos Incubáveis"])

    for row in resultados:
        sheet.append(row)

    file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])

    if file:
        wb.save(file)
        messagebox.showinfo("Sucesso", "Arquivo exportado com sucesso!")


# ============================================================
# 6) CALCULAR
# ============================================================
def calcular():
    global resultados, ano_escolhido

    if not pdf_path:
        messagebox.showerror("Erro", "Selecione um PDF antes de calcular.")
        return

    ano_escolhido = entry_ano.get().strip()

    resultados = []

    # -----------------------------------------
    # MODO MANUAL
    # -----------------------------------------
    if modo_manual.get() == 1:
        d_ini = entry_data_inicio.get()
        d_fim = entry_data_fim.get()
        intervalos = [(d_ini, d_fim)]

    # -----------------------------------------
    # MODO AUTOMÁTICO
    # -----------------------------------------
    else:
        d_ini = entry_data_inicio.get()
        qtd = int(entry_qtd_intervalos.get())
        dias = int(entry_dias_intervalo.get())
        intervalos = gerar_intervalos(d_ini, qtd, dias)

    # limpar tabela
    for i in tree.get_children():
        tree.delete(i)

    # calcular
    for ini, fim in intervalos:
        total, bons = analisar_intervalo(ini, fim)
        resultados.append((ini, fim, total, bons))
        tree.insert("", "end", values=(ini, fim, f"{total:.2f}", f"{bons:.2f}"))

    btn_exportar.config(state=tk.NORMAL)


# ============================================================
# 7) SELECIONAR PDF
# ============================================================
def anexar_pdf():
    global pdf_path
    pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not pdf_path:
        return
    status_label.config(text="Lendo PDF...")
    extrair_linhas_pdf(pdf_path)


# ============================================================
# 8) ATUALIZAR CAMPOS DA UI AO TROCAR DE MODO
# ============================================================
def atualizar_campos():
    if modo_manual.get() == 1:
        # Manual → esconder automáticos
        frame_intervalos_auto.pack_forget()
        frame_data_fim.pack(fill="x", pady=5)
    else:
        # Automático → esconder data fim
        frame_data_fim.pack_forget()
        frame_intervalos_auto.pack(fill="x", pady=5)


# ============================================================
# INTERFACE PROFISSIONAL
# ============================================================
root = tk.Tk()
root.title("Analisador de Produção de Ovos")
root.geometry("660x690")
root.configure(bg="#f4f4f4")

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 11), padding=6)
style.configure("TLabel", font=("Segoe UI", 11))
style.configure("Treeview", font=("Segoe UI", 10))


# ---------------- HEADER ----------------
header = tk.Label(root, text="Analisador de Produção de Ovos",
                  font=("Segoe UI", 16, "bold"),
                  bg="#f4f4f4")
header.pack(pady=10)


# ---------------- FRAME PRINCIPAL ----------------
main_frame = tk.Frame(root, bg="#f4f4f4")
main_frame.pack(pady=10, fill="x")


# DATA INÍCIO
tk.Label(main_frame, text="Data Início (dd/mm/aaaa):", bg="#f4f4f4").pack()
entry_data_inicio = tk.Entry(main_frame, font=("Segoe UI", 11), width=20)
entry_data_inicio.pack(pady=4)


# CHECKBOX MODO MANUAL
modo_manual = tk.IntVar()
check_manual = tk.Checkbutton(main_frame, text="Usar intervalo manual",
                              variable=modo_manual, command=atualizar_campos,
                              bg="#f4f4f4", font=("Segoe UI", 11))
check_manual.pack(pady=6)


# --------------- FRAME DATA FIM (MANUAL) ---------------
frame_data_fim = tk.Frame(main_frame, bg="#f4f4f4")
tk.Label(frame_data_fim, text="Data Fim (dd/mm/aaaa):", bg="#f4f4f4").pack()
entry_data_fim = tk.Entry(frame_data_fim, font=("Segoe UI", 11), width=20)
entry_data_fim.pack(pady=4)


# --------------- FRAME INTERVALOS AUTOMÁTICOS ---------------
frame_intervalos_auto = tk.Frame(main_frame, bg="#f4f4f4")

tk.Label(frame_intervalos_auto, text="Quantos intervalos deseja criar?", bg="#f4f4f4").pack()
entry_qtd_intervalos = tk.Entry(frame_intervalos_auto, font=("Segoe UI", 11), width=20)
entry_qtd_intervalos.pack(pady=4)

tk.Label(frame_intervalos_auto, text="Quantos dias terá cada intervalo?", bg="#f4f4f4").pack()
entry_dias_intervalo = tk.Entry(frame_intervalos_auto, font=("Segoe UI", 11), width=20)
entry_dias_intervalo.insert(0, "7")
entry_dias_intervalo.pack(pady=4)

frame_intervalos_auto.pack(fill="x", pady=5)


# CAMPO ANO
tk.Label(main_frame, text="Ano do relatório (ex: 2025):", bg="#f4f4f4").pack()
entry_ano = tk.Entry(main_frame, font=("Segoe UI", 11), width=20)
entry_ano.insert(0, "2025")
entry_ano.pack(pady=4)


# ---------------- STATUS ----------------
status_label = tk.Label(root, text="Nenhum PDF carregado.", bg="#f4f4f4",
                        font=("Segoe UI", 10))
status_label.pack(pady=5)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill="x", padx=20, pady=5)


# ---------------- BOTÕES ----------------
btn_frame = tk.Frame(root, bg="#f4f4f4")
btn_frame.pack(pady=10)

btn_pdf = ttk.Button(btn_frame, text="Anexar PDF", command=anexar_pdf)
btn_pdf.grid(row=0, column=0, padx=8)

btn_calcular = ttk.Button(btn_frame, text="Calcular", command=calcular)
btn_calcular.grid(row=0, column=1, padx=8)

btn_exportar = ttk.Button(btn_frame, text="Exportar Excel",
                          command=exportar_para_excel, state="disabled")
btn_exportar.grid(row=0, column=2, padx=8)


# ---------------- TABELA ----------------
tree = ttk.Treeview(
    root,
    columns=("Início", "Fim", "Total", "Bons"),
    show="headings",
    height=12
)
tree.heading("Início", text="Início")
tree.heading("Fim", text="Fim")
tree.heading("Total", text="Total Ovos")
tree.heading("Bons", text="Ovos Bons")

tree.pack(padx=15, pady=10, fill="both")


root.mainloop()
