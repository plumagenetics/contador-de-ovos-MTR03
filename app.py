import sys
import os

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

import openpyxl

from pdf_reader import extrair_linhas_pdf
from interval_logic import (
    preprocessar_linhas,
    analisar_intervalo,
    gerar_intervalos
)


# ============================================================
# VARIÁVEIS GLOBAIS
# ============================================================
linhas_brutas = []
linhas_processadas = []
resultados = []
pdf_path = None
ano_escolhido = "2025"


# ============================================================
# CALLBACKS PARA ATUALIZAÇÃO NA INTERFACE
# ============================================================
def update_status(msg):
    status_label.config(text=msg)
    root.update_idletasks()

def update_progress(current, total):
    progress_bar["maximum"] = total
    progress_var.set(current)
    root.update_idletasks()


# ============================================================
# CARREGAR PDF
# ============================================================
def anexar_pdf():
    global pdf_path, linhas_brutas

    pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not pdf_path:
        return

    update_status("Lendo PDF...")

    linhas_brutas = extrair_linhas_pdf(
        pdf_path,
        progress_callback=update_progress,
        status_callback=update_status
    )

    update_status(f"{len(linhas_brutas)} linhas extraídas do PDF.")
    progress_var.set(0)


# ============================================================
# CALCULAR RESULTADOS
# ============================================================
def calcular():
    global resultados, linhas_processadas, ano_escolhido

    if not pdf_path:
        messagebox.showerror("Erro", "Selecione um PDF antes de calcular.")
        return

    ano_escolhido = entry_ano.get().strip()

    # ---------------------------------------------------------
    # PRÉ-PROCESSAMENTO (grande otimização!)
    # ---------------------------------------------------------
    update_status("Processando linhas...")
    linhas_processadas = preprocessar_linhas(linhas_brutas, ano_escolhido)

    # ---------------------------------------------------------
    # DEFINIR INTERVALOS
    # ---------------------------------------------------------
    if modo_manual.get() == 1:
        intervalos = [(entry_data_inicio.get(), entry_data_fim.get())]
    else:
        intervalos = gerar_intervalos(
            entry_data_inicio.get(),
            int(entry_qtd_intervalos.get()),
            int(entry_dias_intervalo.get())
        )

    # limpa tabela
    for item in tree.get_children():
        tree.delete(item)

    resultados = []

    update_status("Calculando intervalos...")

    for ini, fim in intervalos:
        total, bons = analisar_intervalo(linhas_processadas, ini, fim)
        resultados.append((ini, fim, total, bons))
        tree.insert(
            "",
            "end",
            values=(
                ini,
                fim,
                f"{int(round(total)):,.0f}".replace(",", "."),
                f"{int(round(bons)):,.0f}".replace(",", ".")
            )
        )

    btn_exportar.config(state="normal")
    update_status("Cálculo concluído.")


# ============================================================
# EXPORTAÇÃO PARA EXCEL
# ============================================================
def exportar_para_excel():
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Resultados"

    sheet.append(["Início", "Fim", "Total Ovos", "Ovos Bons"])

    for r in resultados:
        sheet.append(r)

    file = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                        filetypes=[("Excel", "*.xlsx")])
    if file:
        wb.save(file)
        messagebox.showinfo("Sucesso", "Arquivo exportado com sucesso!")


# ============================================================
# ALTERAR CAMPOS CONFORME MODO
# ============================================================
def atualizar_campos():
    if modo_manual.get() == 1:
        frame_intervalos_auto.pack_forget()
        frame_data_fim.pack(fill="x", pady=5)
    else:
        frame_data_fim.pack_forget()
        frame_intervalos_auto.pack(fill="x", pady=5)


# ============================================================
# INTERFACE TKINTER (MANTIDA)
# ============================================================
root = tk.Tk()
root.title("Contador MTR03 Produção de Ovos")
root.geometry("660x690")
root.configure(bg="#f4f4f4")

# Caminho seguro para o ícone (funciona em .py e .exe)
def resource_path(relative_path):
    try:
        # PyInstaller cria uma pasta temporária quando o app é executado
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

root.iconbitmap(resource_path("icone.ico"))

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 11))

# HEADER
tk.Label(root, text="Contador MTR03 de Produção de Ovos",
         font=("Segoe UI", 16, "bold"), bg="#f4f4f4").pack(pady=10)

main = tk.Frame(root, bg="#f4f4f4")
main.pack(pady=10, fill="x")

# Data início
tk.Label(main, text="Data Início:", bg="#f4f4f4").pack()
entry_data_inicio = tk.Entry(main, font=("Segoe UI", 11))
entry_data_inicio.pack(pady=4)

# Check manual
modo_manual = tk.IntVar()
tk.Checkbutton(main, text="Usar intervalo manual",
               variable=modo_manual, command=atualizar_campos,
               bg="#f4f4f4").pack(pady=5)

# Frame data fim
frame_data_fim = tk.Frame(main, bg="#f4f4f4")
tk.Label(frame_data_fim, text="Data Fim:", bg="#f4f4f4").pack()
entry_data_fim = tk.Entry(frame_data_fim, font=("Segoe UI", 11))
entry_data_fim.pack(pady=4)

# Frame automáticos
frame_intervalos_auto = tk.Frame(main, bg="#f4f4f4")
tk.Label(frame_intervalos_auto, text="Quantos intervalos?", bg="#f4f4f4").pack()
entry_qtd_intervalos = tk.Entry(frame_intervalos_auto, font=("Segoe UI", 11))
entry_qtd_intervalos.pack(pady=4)

tk.Label(frame_intervalos_auto, text="Dias por intervalo:", bg="#f4f4f4").pack()
entry_dias_intervalo = tk.Entry(frame_intervalos_auto, font=("Segoe UI", 11))
entry_dias_intervalo.insert(0, "7")
entry_dias_intervalo.pack(pady=4)

frame_intervalos_auto.pack(fill="x")

# Ano
tk.Label(main, text="Ano do relatório:", bg="#f4f4f4").pack()
entry_ano = tk.Entry(main, font=("Segoe UI", 11))
entry_ano.insert(0, "2025")
entry_ano.pack(pady=4)

# Status
status_label = tk.Label(root, text="Nenhum PDF carregado.", bg="#f4f4f4")
status_label.pack()

# Progressbar
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var)
progress_bar.pack(fill="x", padx=20, pady=5)

# Botões
btn_frame = tk.Frame(root, bg="#f4f4f4")
btn_frame.pack(pady=10)

ttk.Button(btn_frame, text="Anexar PDF", command=anexar_pdf).grid(row=0, column=0, padx=5)
ttk.Button(btn_frame, text="Calcular", command=calcular).grid(row=0, column=1, padx=5)
btn_exportar = ttk.Button(btn_frame, text="Exportar Excel", command=exportar_para_excel, state="disabled")
btn_exportar.grid(row=0, column=2, padx=5)

# Tabela
tree = ttk.Treeview(root, columns=("Inicio", "Fim", "Total", "Bons"), show="headings")
for col in ("Inicio", "Fim", "Total", "Bons"):
    tree.heading(col, text=col)
tree.pack(fill="both", expand=True, padx=15, pady=10)

root.mainloop()
