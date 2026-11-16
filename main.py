# SHERLOCK TERRA
# Este programa faz 4 coisas:
# 1. Baixa chuva e temperatura de 27 cidades usando dados da NASA.
# 2. Calcula os valores de cada ano para cada região.
# 3. Descobre se cada ano teve El Niño, La Niña ou ficou neutro.
# 4. Junta tudo e salva os arquivos CSV na pasta "dados".

import calendar
import os
import pandas as pd
import requests


# Primeiro e último ano que vamos analisar
ANO_INICIO = 1981
ANO_FIM = 2025


# Aqui ficam as cidades de cada região.
# Cada cidade tem: nome, latitude e longitude.
# Também colocamos os meses da estação e o índice usado para consultar o El Niño.
REGIOES = {
    # Brasil
    "Sertao Nordeste": {
        "cidades": [
            ("Crateus", -5.18, -40.67),
            ("Quixada", -4.97, -39.02),
            ("Caico", -6.46, -37.10),
        ],
        "meses": [2, 3, 4, 5],
        "indice": "DJF",
    },
    "Sul do Brasil": {
        "cidades": [
            ("Santa Maria", -29.69, -53.81),
            ("Passo Fundo", -28.26, -52.41),
            ("Uruguaiana", -29.75, -57.09),
        ],
        "meses": [9, 10, 11],
        "indice": "SON",
    },
    "Litoral Leste NE": {
        "cidades": [
            ("Recife", -8.05, -34.88),
            ("Joao Pessoa", -7.12, -34.86),
            ("Maceio", -9.67, -35.74),
        ],
        "meses": [2, 3, 4, 5],
        "indice": "DJF",
    },

    # Pacífico
    "Leste Australia": {
        "cidades": [
            ("Roma", -26.57, 148.79),
            ("Moree", -29.47, 149.84),
            ("Dubbo", -32.25, 148.60),
        ],
        "meses": [9, 10, 11],
        "indice": "SON",
    },
    "Kiribati": {
        "cidades": [
            ("Tarawa", 1.33, 172.98),
            ("Butaritari", 3.07, 172.79),
            ("Abemama", 0.35, 173.87),
        ],
        "meses": [9, 10, 11],
        "indice": "SON",
    },
    "Sudoeste Australia": {
        "cidades": [
            ("Perth", -31.95, 115.86),
            ("Bunbury", -33.33, 115.64),
            ("Narrogin", -32.93, 117.18),
        ],
        "meses": [6, 7, 8],
        "indice": "JJA",
    },

    # Andes
    "Costa Norte Peru": {
        "cidades": [
            ("Machala", -3.26, -79.96),
            ("Piura", -5.19, -80.63),
            ("Chiclayo", -6.77, -79.84),
        ],
        "meses": [1, 2, 3, 4],
        "indice": "NINO12",
    },
    "Altiplano": {
        "cidades": [
            ("Puno", -15.84, -70.02),
            ("Juliaca", -15.50, -70.13),
            ("Ayaviri", -14.88, -70.59),
        ],
        "meses": [1, 2, 3, 4],
        "indice": "NINO12",
    },
    "Peninsula Iberica": {
        "cidades": [
            ("Lisboa", 38.72, -9.14),
            ("Madri", 40.42, -3.70),
            ("Sevilha", 37.39, -5.98),
        ],
        "meses": [1, 2, 3],
        "indice": "DJF",
    },
}


# PARTE 1 - Baixar os dados da NASA
def baixar_dados_nasa(latitude, longitude):
    # Endereço da API da NASA POWER
    endereco = "https://power.larc.nasa.gov/api/temporal/monthly/point"

    # Informações que vamos enviar para a NASA
    parametros = {
        "parameters": "PRECTOTCORR,T2M",  # chuva e temperatura
        "community": "AG",
        "latitude": latitude,
        "longitude": longitude,
        "start": ANO_INICIO,
        "end": ANO_FIM,
        "format": "JSON",
    }

    resposta = requests.get(endereco, params=parametros, timeout=60)
    resposta.raise_for_status()  # Mostra o erro se a requisição não funcionar

    dados = resposta.json()["properties"]["parameter"]
    chuva = dados["PRECTOTCORR"]
    temperatura = dados["T2M"]

    meses = []

    # A NASA informa os meses usando uma chave como "198101".
    # Os quatro primeiros números são o ano e os dois últimos são o mês.
    for chave in chuva:
        ano = int(chave[:4])
        mes = int(chave[4:])

        # O mês 13 representa uma média anual, então não vamos usar.
        if mes == 13:
            continue

        meses.append({
            "ano": ano,
            "mes": mes,
            "chuva_mm_dia": chuva[chave],
            "temp_c": temperatura[chave],
        })

    return meses


# PARTE 2 - Calcular os valores de cada ano
def calcular_valores_por_ano(dados_mensais, meses_da_estacao):
    # Vamos guardar os dados separados por ano.
    dados_por_ano = {}

    for dado in dados_mensais:
        ano = dado["ano"]
        mes = dado["mes"]

        # Ignora os meses que não fazem parte da estação escolhida.
        if mes not in meses_da_estacao:
            continue

        # A NASA usa -999 quando não existe um dado disponível.
        if dado["chuva_mm_dia"] == -999 or dado["temp_c"] == -999:
            continue

        # Cria o espaço para guardar os dados do ano, se necessário.
        if ano not in dados_por_ano:
            dados_por_ano[ano] = {
                "chuva_mm": 0,
                "temperaturas": [],
            }

        # A chuva vem em mm por dia. Multiplicamos pelos dias do mês
        # para descobrir aproximadamente quanto choveu naquele mês.
        dias_do_mes = calendar.monthrange(ano, mes)[1]
        chuva_do_mes = dado["chuva_mm_dia"] * dias_do_mes
        dados_por_ano[ano]["chuva_mm"] += chuva_do_mes

        # Guardamos a temperatura para calcular a média depois.
        dados_por_ano[ano]["temperaturas"].append(dado["temp_c"])

    resultado = []

    for ano in dados_por_ano:
        temperaturas = dados_por_ano[ano]["temperaturas"]

        # Só usamos o ano se todos os meses da estação tiverem dados.
        if len(temperaturas) != len(meses_da_estacao):
            continue

        chuva_total = dados_por_ano[ano]["chuva_mm"]
        temperatura_media = sum(temperaturas) / len(temperaturas)

        resultado.append({
            "ano": ano,
            "chuva_mm": round(chuva_total, 1),
            "temp_c": round(temperatura_media, 2),
        })

    return resultado


def calcular_media_da_regiao(regiao):
    # Vamos juntar os resultados das três cidades da região.
    dados_por_ano = {}

    for nome, latitude, longitude in regiao["cidades"]:
        print("  Baixando", nome, "...")

        dados_mensais = baixar_dados_nasa(latitude, longitude)
        dados_anuais = calcular_valores_por_ano(dados_mensais, regiao["meses"])

        for dado in dados_anuais:
            ano = dado["ano"]

            if ano not in dados_por_ano:
                dados_por_ano[ano] = {
                    "chuvas": [],
                    "temperaturas": [],
                }

            dados_por_ano[ano]["chuvas"].append(dado["chuva_mm"])
            dados_por_ano[ano]["temperaturas"].append(dado["temp_c"])

    resultado = []

    # Calcula a média das cidades em cada ano.
    for ano in sorted(dados_por_ano):
        chuvas = dados_por_ano[ano]["chuvas"]
        temperaturas = dados_por_ano[ano]["temperaturas"]

        # Só compara os anos em que temos dados das três cidades.
        if len(chuvas) != 3 or len(temperaturas) != 3:
            continue

        media_chuva = sum(chuvas) / 3
        media_temperatura = sum(temperaturas) / 3

        resultado.append({
            "ano": ano,
            "chuva_mm": round(media_chuva, 1),
            "temp_c": round(media_temperatura, 2),
        })

    return pd.DataFrame(resultado)


# PARTE 3 - Descobrir as fases do El Niño

def marcar_episodios(valores_acima_do_limite, fases, nome_da_fase, minimo=5):
    # Um trimestre isolado não é suficiente para confirmar
    # Por isso, precisamos encontrar pelo menos 5 trimestres seguidos.
    inicio = None

    # O +1 serve para conferir também uma sequência que chega até o final.
    for i in range(len(valores_acima_do_limite) + 1):
        if i < len(valores_acima_do_limite):
            esta_no_limite = valores_acima_do_limite[i]
        else:
            esta_no_limite = False

        if esta_no_limite and inicio is None:
            inicio = i

        # Quando a sequência termina, verificamos se ela foi longa o bastante.
        elif not esta_no_limite and inicio is not None:
            tamanho_da_sequencia = i - inicio

            if tamanho_da_sequencia >= minimo:
                for posição in range(inicio, i):
                    fases[posição] = nome_da_fase

            inicio = None


def baixar_fases_oni():
    # Esta tabela da NOAA informa a anomalia de temperatura do Pacífico.
    endereco = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
    tabela = pd.read_csv(endereco, sep=r"\s+")

    # A NOAA usa uma casa decimal para analisar os valores.
    anomalias = list(tabela["ANOM"].round(1))
    fases = ["Neutro"] * len(anomalias)

    # Valores positivos indicam El Niño; negativos indicam La Niña.
    valores_el_nino = []
    valores_la_nina = []

    for anomalia in anomalias:
        valores_el_nino.append(anomalia >= 0.5)
        valores_la_nina.append(anomalia <= -0.5)

    marcar_episodios(valores_el_nino, fases, "El Niño")
    marcar_episodios(valores_la_nina, fases, "La Niña")

    tabela["fase"] = fases
    return tabela


def fase_do_ano(tabela_oni, ano, trimestre):
    # Procura o ano e o trimestre que queremos consultar.
    linha = tabela_oni[
        (tabela_oni["YR"] == ano) &
        (tabela_oni["SEAS"] == trimestre)
    ]

    if len(linha) == 0:
        return None

    return linha["fase"].iloc[0]


def maior_sequencia(valores):
    # Conta qual foi a maior quantidade de valores True seguidos.
    maior = 0
    atual = 0

    for valor in valores:
        if valor:
            atual += 1
        else:
            atual = 0

        if atual > maior:
            maior = atual

    return maior


def fase_do_ano_peru(tabela_nino12, ano):
    # Para a costa do Peru, usamos os dados do índice Niño 1+2.
    # Aqui analisamos os meses de janeiro até abril.
    dados_do_ano = tabela_nino12[
        (tabela_nino12["YEAR"] == ano) &
        (tabela_nino12["MON"] <= 4)
    ]

    valores = list(dados_do_ano["rNINO1+2"])

    if len(valores) < 4:
        return None

    # Precisamos de pelo menos 3 meses seguidos acima ou abaixo do limite.
    valores_el_nino = []
    valores_la_nina = []

    for valor in valores:
        valores_el_nino.append(valor >= 0.5)
        valores_la_nina.append(valor <= -0.5)

    if maior_sequencia(valores_el_nino) >= 3:
        return "El Niño"

    if maior_sequencia(valores_la_nina) >= 3:
        return "La Niña"

    return "Neutro"


# PARTE 4 - Juntar tudo e salvar os arquivos

# Esta parte só roda quando executamos este arquivo diretamente.
# Assim, outro arquivo do projeto pode importar REGIOES sem baixar os dados.
if __name__ == "__main__":
    print("Baixando as fases do El Niño da NOAA...")

    oni = baixar_fases_oni()

    # Cria a pasta "dados" caso ela ainda não exista.
    pasta_dados = os.path.join(os.path.dirname(__file__), "dados")
    os.makedirs(pasta_dados, exist_ok=True)

    # Salva a tabela ONI, que também será usada no gráfico do aplicativo.
    oni.to_csv(os.path.join(pasta_dados, "oni.csv"), index=False)
    print("Salvo em dados/oni.csv")

    # Este índice é usado nas regiões da costa do Peru e dos Andes.
    endereco_nino12 = "https://www.cpc.ncep.noaa.gov/data/indices/rel_mthsst9120.txt"
    nino12 = pd.read_csv(endereco_nino12, sep=r"\s+")

    # Agora fazemos o processo para cada região.
    for nome in REGIOES:
        regiao = REGIOES[nome]

        print("\n=====", nome, "=====")

        tabela = calcular_media_da_regiao(regiao)

        # Descobre a fase do El Niño para cada ano da região.
        fases = []

        for ano in tabela["ano"]:
            if regiao["indice"] == "NINO12":
                fase = fase_do_ano_peru(nino12, ano)
            else:
                fase = fase_do_ano(oni, ano, regiao["indice"])

            fases.append(fase)

        tabela["fase"] = fases

        # Coloca o nome da região na primeira coluna.
        tabela.insert(0, "regiao", nome)

        # Transforma o nome da região em nome de arquivo.
        nome_arquivo = nome.lower().replace(" ", "_") + ".csv"
        caminho_arquivo = os.path.join(pasta_dados, nome_arquivo)

        tabela.to_csv(caminho_arquivo, index=False)

        print(tabela.head())
        print("Anos:", len(tabela), "| por fase:", tabela["fase"].value_counts().to_dict())
        print("Salvo em dados/" + nome_arquivo)