import re
from datetime import datetime, timedelta

# ---------------------------------------------------------
# REGEX PRÉ-COMPILADO PARA NÚMEROS
# ---------------------------------------------------------
NUM_REGEX = re.compile(r"[\d\.]+(?:,\d+)?")

# ---------------------------------------------------------
# PROCESSAMENTO OTIMIZADO DE UMA LINHA
# ---------------------------------------------------------
def parse_linha(linha, ano_escolhido):
    """
    Converte uma linha bruta do PDF em um pacote:
    (data, bons, total)
    """
    tokens = linha.split()
    if len(tokens) < 5:
        return None

    txt_data = tokens[1]

    if len(txt_data) == 5:
        txt_data += "/" + ano_escolhido

    try:
        data = datetime.strptime(txt_data, "%d/%m/%Y")
    except:
        return None

    numeros = NUM_REGEX.findall(linha)
    if len(numeros) < 3:
        return (data, None, None)

    def to_num(s):
        return float(s.replace(".", "").replace(",", "."))

    total = to_num(numeros[-3])
    apr = to_num(numeros[-1]) / 100
    bons = total * apr

    return (data, bons, total)


# ---------------------------------------------------------
# PRÉ-PROCESSAMENTO COMPLETO
# ---------------------------------------------------------
def preprocessar_linhas(linhas_brutas, ano):
    """
    Converte todas as linhas brutas do PDF em uma estrutura já parseada.
    Isso acelera o cálculo dos intervalos em até 10x.
    """
    processadas = []
    for linha in linhas_brutas:
        pacote = parse_linha(linha, ano)
        if pacote:
            processadas.append(pacote)
    return processadas


# ---------------------------------------------------------
# CÁLCULO DO INTERVALO USANDO LINHAS JÁ PROCESSADAS
# ---------------------------------------------------------
def analisar_intervalo(linhas_processadas, d_ini, d_fim):
    di = datetime.strptime(d_ini, "%d/%m/%Y")
    df = datetime.strptime(d_fim, "%d/%m/%Y")

    total = 0.0
    bons = 0.0

    for data, b, t in linhas_processadas:
        if di <= data <= df:
            if b is not None:
                bons += b
            if t is not None:
                total += t

    return total, bons


# ---------------------------------------------------------
# GERAÇÃO DE INTERVALOS AUTOMÁTICOS
# ---------------------------------------------------------
def gerar_intervalos(data_inicio, qtd, dias):
    intervalos = []
    inicio = datetime.strptime(data_inicio, "%d/%m/%Y")

    for i in range(qtd):
        ini = inicio + timedelta(days=i * dias)
        fim = ini + timedelta(days=dias - 1)
        intervalos.append((ini.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y")))

    return intervalos
