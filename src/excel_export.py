from io import BytesIO
import openpyxl

def exportar_resultados_excel_bytes(resultados):
    """
    resultados: lista de tuplas (ini, fim, total, bons)
    Retorna bytes de um XLSX para download.
    """
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Resultados"

    sheet.append(["Início", "Fim", "Total Ovos", "Ovos Bons"])

    for r in resultados:
        sheet.append(r)

    output = BytesIO()
    wb.save(output)
    return output.getvalue()
