# ============================================================
# SHERLOCK TERRA - Em busca das tendências terrestres
# Aplicativo para comparar duas regiões e observar os dados de chuva e temperatura.
#
# Como executar:
#   1. Rode "python main.py" para gerar os arquivos CSV na pasta dados/.
#   2. Depois, rode "streamlit run app.py" no terminal.
#
# No aplicativo, é possível:
#   - escolher duas regiões e o período da análise;
#   - visualizar gráficos de chuva e temperatura;
#   - comparar os dados entre El Niño, La Niña e anos neutros;
#   - consultar alguns padrões encontrados nos dados;
#   - escrever anotações e exportar um relatório.
#
# ============================================================

import html
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pymannkendall as mk
import streamlit as st
from plotly.subplots import make_subplots

from main import REGIOES as DADOS_REGIOES   # cidades, meses da estação e índice de cada região

TITULO = "Sherlock Terra"
SUBTITULO = "EM BUSCA DAS TENDÊNCIAS TERRESTRES"

st.set_page_config(page_title=TITULO, layout="wide")

# ------------------------------------------------------------
# Informações das 9 regiões.
# Também guardamos a posição no mapa, o grupo e a resposta esperada
# para a chuva durante o El Niño.
#
# esperado:
# -1 = esperamos menos chuva
#  1 = esperamos mais chuva
#  0 = esperamos pouca mudança
#
# Os nomes precisam ser iguais aos usados no main.py.
# ------------------------------------------------------------
REGIOES = {
    "Sertao Nordeste":    {"titulo": "Sertão do Nordeste",     "trio": "Brasil",   "papel": "Afetada",   "esperado": -1, "lat": -5.54,  "lon": -38.93},
    "Sul do Brasil":      {"titulo": "Sul do Brasil",          "trio": "Brasil",   "papel": "Contrária", "esperado": +1, "lat": -29.23, "lon": -54.44},
    "Litoral Leste NE":   {"titulo": "Litoral leste do NE",    "trio": "Brasil",   "papel": "Fraca",     "esperado": 0,  "lat": -8.28,  "lon": -35.16},
    "Leste Australia":    {"titulo": "Leste da Austrália",     "trio": "Pacífico", "papel": "Afetada",   "esperado": -1, "lat": -29.43, "lon": 149.08},
    "Kiribati":           {"titulo": "Kiribati",               "trio": "Pacífico", "papel": "Contrária", "esperado": +1, "lat": 1.58,   "lon": 173.21},
    "Sudoeste Australia": {"titulo": "Sudoeste da Austrália",  "trio": "Pacífico", "papel": "Fraca",     "esperado": 0,  "lat": -32.74, "lon": 116.23},
    "Costa Norte Peru":   {"titulo": "Costa norte do Peru",    "trio": "Andes",    "papel": "Afetada",   "esperado": +1, "lat": -5.07,  "lon": -80.14},
    "Altiplano":          {"titulo": "Altiplano (Titicaca)",   "trio": "Andes",    "papel": "Contrária", "esperado": -1, "lat": -15.41, "lon": -70.25},
    "Peninsula Iberica":  {"titulo": "Península Ibérica",      "trio": "Andes",    "papel": "Fraca",     "esperado": 0,  "lat": 38.84,  "lon": -6.27},
}
CHAVES = list(REGIOES)

CORES_LOCAL = ["#f5a623", "#2dd4bf"]        # Local 1 (âmbar) e Local 2 (verde-água)
SIMBOLOS_LOCAL = ["circle", "diamond"]      # o formato do ponto também diferencia os locais
CORES_FASE = {"El Niño": "#e5484d", "La Niña": "#3b82f6", "Neutro": "#9e9e9e"}
FASES = ["El Niño", "Neutro", "La Niña"]

VARIAVEIS = {
    "chuva_mm": {"nome": "Chuva", "unidade": "mm", "sufixo": "%", "casas": 1},
    "temp_c":   {"nome": "Temperatura", "unidade": "°C", "sufixo": "°C", "casas": 2},
}
MODOS = ["Valores medidos", "Diferença da média"]   # como mostrar o gráfico temporal
NOMES_MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
NOMES_INDICE = {
    "DJF": "ONI de dez–fev (NOAA)",
    "SON": "ONI de set–nov (NOAA)",
    "JJA": "ONI de jun–ago (NOAA)",
    "NINO12": "Niño 1+2, mar da costa do Peru (NOAA)",
}
TRIMESTRES = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
ESPERADO_TEXTO = {-1: "menos chuva no El Niño", +1: "mais chuva no El Niño", 0: "resposta fraca"}
RODAPE = ("Fontes: NASA POWER e NOAA. Cada região representa a média de 3 cidades. "
          "Os resultados mostram relações entre os dados, mas não provam causa e efeito.")

PASTA = Path(__file__).parent   # a pasta do projeto, de onde quer que o app seja rodado
PASTA_DADOS = PASTA / "dados"   # todos os datasets (CSV) ficam aqui


def num(x, casas=1, sinal=False):
    """Número no jeito brasileiro, com vírgula decimal (ex.: 0,05 e +6,3)."""
    return f"{x:{'+' if sinal else ''}.{casas}f}".replace(".", ",")


# ============================================================
# PARTE 1 - Leitura dos dados e cálculos
# ============================================================
def carregar(chave):
    """Lê o CSV gerado pelo main.py."""
    return pd.read_csv(PASTA_DADOS / (chave.lower().replace(" ", "_") + ".csv"))


@st.cache_data
def limites_anos():
    """Primeiro e último ano que existem nos dados."""
    anos = pd.concat([carregar(c)["ano"] for c in CHAVES])
    return int(anos.min()), int(anos.max())


@st.cache_data
def carregar_oni():
    """O índice ONI de cada trimestre (salvo pelo main.py). None se o oni.csv ainda não existe."""
    caminho = PASTA_DADOS / "oni.csv"
    if not caminho.exists():
        return None
    oni = pd.read_csv(caminho)
    # Ajusta a posição dos trimestres para alinhar o índice ONI com os anos do gráfico.
    # Assim, os trimestres aparecem distribuídos ao longo de cada ano.
    posicao = {s: (i + 0.5) / 12 - 0.5 for i, s in enumerate(TRIMESTRES)}
    oni["x"] = oni["YR"] + oni["SEAS"].map(posicao)
    return oni


def anomalias(anos, valores, coluna):
    """Distância de cada ano até a reta de tendência (passo 6.2: tirar a tendência)."""
    inclinacao, intercepto = np.polyfit(anos, valores, 1)
    reta = inclinacao * anos + intercepto
    if coluna == "chuva_mm":
        return (valores - reta) / reta * 100   # Na chuva, o resultado é uma porcentagem.
    return valores - reta                      # Na temperatura, o resultado fica em graus Celsius.


def embaralhamento(grupo, neutro, sorteios=10_000):
    """Teste do embaralhamento (passo 6.4)."""
    diferenca_real = grupo.mean() - neutro.mean()
    todos = np.concatenate([grupo, neutro])
    n = len(grupo)
    rng = np.random.default_rng(42)
    vezes = 0
    for _ in range(sorteios):
        rng.shuffle(todos)
        if abs(todos[:n].mean() - todos[n:].mean()) >= abs(diferenca_real):
            vezes += 1
    return diferenca_real, vezes / sorteios


@st.cache_data
def analisar(chave, coluna, ano_ini, ano_fim):
    """Tudo o que o painel precisa de uma região, no intervalo escolhido (com cache)."""
    tabela = carregar(chave)
    tabela = tabela[tabela["ano"].between(ano_ini, ano_fim)].dropna(subset=[coluna]).reset_index(drop=True)
    anos = tabela["ano"].to_numpy()
    valores = tabela[coluna].to_numpy()

    # Calcula a tendência dos dados e a linha que será mostrada no gráfico.
    r = mk.hamed_rao_modification_test(valores)
    tabela["tendencia"] = r.intercept + r.slope * np.arange(len(valores))

    # Calcula a diferença em relação à tendência e separa os anos por fase.
    tabela["anomalia"] = anomalias(anos, valores, coluna)
    com_fase = tabela.dropna(subset=["fase"])
    medias = com_fase.groupby("fase")["anomalia"].mean().reindex(FASES)        # sem a tendência
    medias_abs = com_fase.groupby("fase")[coluna].mean().reindex(FASES)        # valores medidos
    contagem = com_fase["fase"].value_counts().reindex(FASES, fill_value=0)
    el_nino = com_fase[com_fase["fase"] == "El Niño"]["anomalia"].to_numpy()
    neutro = com_fase[com_fase["fase"] == "Neutro"]["anomalia"].to_numpy()
    if len(el_nino) >= 2 and len(neutro) >= 2:
        diferenca, p_fase = embaralhamento(el_nino, neutro)
    else:
        diferenca, p_fase = np.nan, np.nan   # poucos anos no intervalo para comparar

    return {
        "tabela": tabela, "media": valores.mean(),
        "tendencia": r.trend, "p_tendencia": r.p, "por_decada": r.slope * 10,
        "medias": medias, "medias_abs": medias_abs, "contagem": contagem,
        "diferenca": diferenca, "p_fase": p_fase,
    }


def fmt_p(p):
    """p-valor como número curto (para a tabela)."""
    if pd.isna(p):
        return "—"
    return "< 0,001" if p < 0.001 else num(p, 3)


def texto_p(p):
    """p-valor para uma frase: 'p = 0,012' ou 'p < 0,001'."""
    return "p < 0,001" if p < 0.001 else f"p = {num(p, 3)}"


# ============================================================
# PARTE 2 - Tabelas e explicações
# ============================================================
def fmt_diferenca(x, coluna):
    """Diferença com sinal: '+6,3%' para a chuva e '+0,94 °C' para a temperatura."""
    if pd.isna(x):
        return "—"
    if coluna == "chuva_mm":
        return f"{num(x, 1, sinal=True)}%"
    return f"{num(x, 2, sinal=True)} °C"


def marcar_p(p):
    """p-valor para a tabela, com * quando fica abaixo de 0,05 (a convenção usual)."""
    return fmt_p(p) + (" *" if p < 0.05 else "")


def qtd_anos(n):
    return f"{n} ano" if n == 1 else f"{n} anos"


def linhas_resumo(analises, coluna, locais):
    """Linhas da tabela de resultados: (rótulo, [valor do Local 1, valor do Local 2]).

    Só números e fatos, sem conclusões: a interpretação fica com o analista.
    """
    v = VARIAVEIS[coluna]
    casas, unidade = v["casas"], v["unidade"]
    casas_media = 0 if coluna == "chuva_mm" else 2
    linhas = {}

    def adicionar(rotulo, valor):
        linhas.setdefault(rotulo, []).append(valor)

    for chave in locais:
        a = analises[(chave, coluna)]
        anos = a["tabela"]["ano"]
        c = a["contagem"]
        adicionar("Anos analisados", f"{qtd_anos(len(anos))} ({anos.min()}–{anos.max()})")
        adicionar("Média no período", f"{num(a['media'], casas_media)} {unidade}")
        # Passo 5: tendência
        adicionar("Quanto muda a cada 10 anos (inclinação de Sen)", f"{num(a['por_decada'], casas, sinal=True)} {unidade}")
        adicionar("p-valor da tendência (teste de Mann-Kendall)", marcar_p(a["p_tendencia"]))
        # Passo 6: as fases
        for fase, nome_fase in [("El Niño", "anos de El Niño"), ("Neutro", "anos neutros"), ("La Niña", "anos de La Niña")]:
            media = a["medias_abs"][fase]
            adicionar(f"Média nos {nome_fase}",
                      "—" if pd.isna(media) else f"{num(media, casas_media)} {unidade} ({qtd_anos(c[fase])})")
        adicionar("Diferença entre anos de El Niño e neutros (sem a tendência)", fmt_diferenca(a["diferenca"], coluna))
        adicionar("p-valor da diferença (teste do embaralhamento)", marcar_p(a["p_fase"]))
        if coluna == "chuva_mm":
            adicionar("Hipótese do projeto", ESPERADO_TEXTO[REGIOES[chave]["esperado"]])
    return list(linhas.items())


def texto_metodo():
    """Como a análise foi feita, passo a passo (aparece no botão da página e no relatório)."""
    ano_min, ano_max = limites_anos()
    return [
        f"**1. De onde vêm os dados.** Usamos a NASA POWER, um serviço da NASA que junta medições de "
        f"satélites com modelos do clima (a chamada reanálise MERRA-2). Para cada região escolhemos "
        f"3 cidades e fazemos a média delas, mês a mês, de {ano_min} a {ano_max}.",
        "**2. Um número por ano.** Cada região tem a sua estação chuvosa: no Sertão, por exemplo, ela vai "
        "de fevereiro a maio. Somamos a chuva desses meses e fazemos a média da temperatura neles. "
        "Assim, cada ano vira um único número de chuva e um único número de temperatura.",
        "**3. Como saber se foi ano de El Niño.** A NOAA, agência de clima dos Estados Unidos, mede quanto "
        "o mar no meio do Oceano Pacífico está mais quente ou mais frio que o normal (é o índice ONI). "
        "Se ele fica pelo menos 0,5 °C mais quente por 5 trimestres seguidos, é El Niño; se fica 0,5 °C "
        "mais frio, é La Niña; nos outros casos, o ano é neutro. A costa do Peru e o Altiplano usam um "
        "índice do mar bem perto da costa peruana (o Niño 1+2), olhando de janeiro a abril.",
        "**4. O período.** Todas as contas usam só os anos escolhidos em \"Período\", no topo da página.",
        "**5. Está subindo ou descendo? (teste de Mann-Kendall)** O teste compara cada ano com todos os "
        "anos que vêm depois dele e conta quantas vezes o valor subiu e quantas vezes desceu. Se sobe "
        "muito mais vezes do que desce (ou o contrário), existe uma tendência. A versão que usamos "
        "(de Hamed e Rao) também funciona quando um ano influencia o seguinte, o que é comum no clima.",
        "**6. Quanto muda? (inclinação de Sen)** Calculamos a inclinação da reta entre todos os pares de "
        "anos e ficamos com a do meio (a mediana), que não se deixa levar por um ano muito fora do comum. "
        "É a inclinação da linha tracejada do gráfico, mostrada na tabela como \"quanto muda a cada 10 anos\".",
        "**7. Tirando a tendência.** Se a temperatura vem subindo há décadas, um ano recente pode ser "
        "quente só por estar seguindo essa subida, e não por causa do El Niño. Por isso, antes de comparar "
        "as fases, medimos cada ano em relação à linha de tendência, e não em relação à média geral. "
        "Na chuva, essa diferença aparece em %; na temperatura, em °C.",
        "**8. Teste do embaralhamento (Teste dos papéis).** Imagine escrever o valor de cada ano "
        "de El Niño e de cada ano neutro num papelzinho e colocar todos num chapéu. Depois sorteamos, "
        "sem olhar, quais papéis vão formar o grupo \"El Niño\" e medimos a diferença entre os dois "
        "grupos. Repetimos isso 10.000 vezes. O p-valor é a fração dos sorteios em que a diferença "
        "sorteada foi igual ou maior que a diferença real. Se isso quase nunca acontece só por sorte, "
        "o p-valor fica pequeno. Na tabela, o * marca os p-valores menores que 0,05 (5%), o limite "
        "que os cientistas costumam usar.",
        "**9. O que este painel não faz.** Ele mostra os dados, as tendências e os testes, mas não tira "
        "conclusões: isso fica com o analista, no bloco de anotações. Vale lembrar que os números mostram "
        "associação, não causa (duas coisas acontecerem juntas não prova que uma causa a outra), que "
        "algumas regiões têm poucos anos de El Niño no período, o que deixa os testes menos seguros, e "
        "que os dados de reanálise podem ser um pouco diferentes das medições de estações meteorológicas.",
    ]


# Texto de apoio do "Resumo dos resultados": o que a tabela mostra e como ler cada linha
INTRO_RESUMO = ("A tabela compara os resultados das duas regiões. Primeiro, mostra como a chuva ou a "
                "temperatura mudou ao longo dos anos. Depois, compara os valores durante El Niño, La Niña "
                "e anos neutros. O gráfico abaixo ajuda a visualizar essa comparação.")
COMO_LER_TABELA = [
    "**Anos analisados:** quantos anos entraram na conta, dentro do período escolhido.",
    "**Média no período:** o valor típico do local. Na chuva, é a média do total de chuva da estação "
    "chuvosa de cada ano.",
    "**Quanto muda a cada 10 anos:** a inclinação da linha tracejada do gráfico. Por exemplo, "
    "\"+0,30 °C\" quer dizer que, seguindo a tendência, a temperatura sobe cerca de 0,3 °C a cada década.",
    "**p-valor da tendência:** mostra o quanto uma tendência como essa seria rara se, na verdade, nada "
    "estivesse mudando e as variações fossem só sorte. Quanto menor o número, mais rara ela seria. "
    "O * aparece quando ele é menor que 0,05 (5%).",
    "**Médias nos anos de El Niño, neutros e La Niña:** a média só dos anos de cada fase. Entre "
    "parênteses está quantos anos de cada fase existem no período; com poucos anos, a média fica "
    "menos confiável.",
    "**Diferença entre anos de El Niño e neutros:** quanto, em média, os anos de El Niño ficaram acima (+) "
    "ou abaixo (−) dos anos neutros, depois de tirar a tendência. Na chuva aparece em %; na temperatura, em °C.",
    "**p-valor da diferença:** a mesma ideia do outro p-valor, agora para a diferença entre El Niño e "
    "neutros: o quanto uma diferença desse tamanho seria rara se a fase do El Niño não tivesse nada a "
    "ver com a chuva ou com a temperatura.",
    "**Hipótese do projeto:** o que a equipe esperava encontrar antes de olhar os dados. Comparar essa "
    "ideia com os números é o trabalho do analista.",
]


def tabela_markdown(linhas, locais):
    """A tabela de tendência em Markdown (para mostrar no app)."""
    cabecalho = "| | " + " | ".join(
        f"<span style='color:{CORES_LOCAL[i]}'>●</span> **{REGIOES[c]['titulo']}**" for i, c in enumerate(locais)
    ) + " |"
    separador = "|---|" + "---|" * len(locais)
    corpo = [f"| {rotulo} | " + " | ".join(valores) + " |" for rotulo, valores in linhas]
    return "\n".join([cabecalho, separador, *corpo])


def tabela_html(linhas, locais):
    """A mesma tabela em HTML (para o relatório exportado)."""
    cabecalho = "".join(f"<th>{html.escape(REGIOES[c]['titulo'])}</th>" for c in locais)
    corpo = "".join(
        f"<tr><th>{html.escape(rotulo)}</th>" + "".join(f"<td>{html.escape(v)}</td>" for v in valores) + "</tr>"
        for rotulo, valores in linhas
    )
    return f"<table><tr><th></th>{cabecalho}</tr>{corpo}</table>"


# ------------------------------------------------------------
# Os textos de "Padrões nos dados" são criados por regras simples,
# usando os próprios resultados da análise.
# No futuro, essa parte poderá ser feita por um modelo de IA.
# ------------------------------------------------------------
AVISO_INSIGHTS = ("Estes padrões são resumos automáticos feitos a partir dos números. Eles ajudam a "
                  "observar os dados, mas não substituem a análise da equipe.")
COMO_PADROES = ("Como calculamos: cada ano é comparado com a linha de tendência do próprio local (a linha "
                "tracejada do gráfico), usando só os anos do período escolhido. A fase de cada ano vem do "
                "índice usado pelo local, e o r é a correlação de Pearson entre os dois locais, ano a ano, "
                "que vai de −1 a +1.")


def juntar(itens):
    """['a', 'b', 'c'] -> 'a, b e c'."""
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def contar_fases(fases):
    """Quantos anos de cada fase, em texto: '4 de El Niño e 1 neutro'."""
    contagem = fases.fillna("sem fase").value_counts()
    nomes = {"El Niño": ("de El Niño", "de El Niño"), "Neutro": ("neutro", "neutros"),
             "La Niña": ("de La Niña", "de La Niña"), "sem fase": ("sem fase", "sem fase")}
    partes = [f"{contagem[f]} {nomes[f][0] if contagem[f] == 1 else nomes[f][1]}" for f in nomes if f in contagem]
    return juntar(partes)


def gerar_destaques(analises, colunas, locais):
    """Padrões nos dados: contagens e números tirados dos próprios dados, sem interpretação.

    Devolve {nome da variável: [frases]}. Tudo é medido em relação à linha de tendência
    de cada local (a coluna "anomalia"), o mesmo critério da tabela de resultados.
    """
    destaques = {}
    for coluna in colunas:
        v = VARIAVEIS[coluna]
        menos, mais = ("secos", "chuvosos") if coluna == "chuva_mm" else ("frios", "quentes")
        tabelas = [analises[(chave, coluna)]["tabela"] for chave in locais]
        textos = []

        # 1. Frequência: em quantos anos de cada fase o local ficou acima ou abaixo da tendência
        for chave, t in zip(locais, tabelas):
            partes = []
            for fase in ["El Niño", "La Niña"]:
                anomalias_fase = t.loc[t["fase"] == fase, "anomalia"]
                n = len(anomalias_fase)
                if n == 0:
                    partes.append(f"nenhum ano de {fase}")
                else:
                    partes.append(f"{'no' if n == 1 else 'nos'} {qtd_anos(n)} de {fase}, "
                                  f"{(anomalias_fase < 0).sum()} abaixo e {(anomalias_fase > 0).sum()} acima")
            textos.append(f"**{REGIOES[chave]['titulo']}**, em relação à tendência: " + "; ".join(partes) + ".")

        # 2. Os anos mais extremos e as fases deles
        for chave, t in zip(locais, tabelas):
            k = 5 if len(t) >= 20 else 3

            def descrever(linhas):
                anos_txt = ", ".join(str(int(ano)) for ano in linhas["ano"])
                return f"{contar_fases(linhas['fase'])} ({anos_txt})"

            textos.append(f"**{REGIOES[chave]['titulo']}**, {k} anos mais {menos} em relação à tendência: "
                          f"{descrever(t.nsmallest(k, 'anomalia'))}. {k} mais {mais}: "
                          f"{descrever(t.nlargest(k, 'anomalia'))}.")

        # 3. Os dois locais juntos
        juntos = tabelas[0][["ano", "anomalia", "fase"]].merge(
            tabelas[1][["ano", "anomalia", "fase"]], on="ano", suffixes=("_1", "_2"))
        if len(juntos) >= 3:
            r = np.corrcoef(juntos["anomalia_1"], juntos["anomalia_2"])[0, 1]
            texto = f"**Os dois locais**: correlação ano a ano r = {num(r, 2, sinal=True)} ({qtd_anos(len(juntos))})."
            ambos = juntos[(juntos["fase_1"] == "El Niño") & (juntos["fase_2"] == "El Niño")]
            if len(ambos) >= 3:
                opostos = ((ambos["anomalia_1"] * ambos["anomalia_2"]) < 0).sum()
                texto += (f" Nos {qtd_anos(len(ambos))} de El Niño em comum, em {opostos} "
                          "um ficou acima e o outro abaixo da tendência.")
            else:
                comum = "Nenhum ano" if len(ambos) == 0 else f"Só {qtd_anos(len(ambos))}"
                texto += f" {comum} de El Niño em comum no período"
                # só explica pela estação/índice quando os dois locais realmente usam índices diferentes
                indices = {DADOS_REGIOES[chave]["indice"] for chave in locais}
                texto += " (os locais usam estações ou índices diferentes)." if len(indices) > 1 else "."
            textos.append(texto)

        destaques[v["nome"]] = textos
    return destaques


# ============================================================
# PARTE 3 - Criação dos gráficos
# ============================================================
def transformar(serie, media, coluna, modo):
    """No modo "Diferença da média", compara cada ano com a média do próprio local.

    Assim, regiões muito mais chuvosas (ou mais quentes) ficam na mesma escala:
    a chuva vira % acima/abaixo da média e a temperatura, °C acima/abaixo da média.
    """
    if modo == MODOS[0]:
        return serie
    if coluna == "chuva_mm":
        return (serie / media - 1) * 100
    return serie - media


def grafico_temporal(analises, colunas, locais, modo, oni, ano_ini, ano_fim, mostrar=None, legenda=False):
    """Passo 4: as duas regiões no tempo, com os anos de El Niño e La Niña marcados.

    Se o oni.csv existir, a última faixa mostra o índice ONI (o fenômeno no Pacífico).
    mostrar: o que exibir, vindo das caixas de seleção da legenda na página.
    legenda: desenha a legenda do próprio gráfico (usada no relatório exportado,
             porque na página a legenda são as caixas de seleção).
    """
    if mostrar is None:
        mostrar = {"locais": [True, True], "El Niño": True, "La Niña": True, "tendencia": True, "oni": True}
    tem_oni = oni is not None and mostrar["oni"]
    linhas_total = len(colunas) + (1 if tem_oni else 0)
    fig = make_subplots(rows=linhas_total, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        row_heights=[1] * len(colunas) + ([0.55] if tem_oni else []))

    for linha, coluna in enumerate(colunas, start=1):
        v = VARIAVEIS[coluna]
        diferenca = modo == MODOS[1]
        if not diferenca:
            unidade_eixo, unidade_hover = v["unidade"], f" {v['unidade']}"
        elif coluna == "chuva_mm":
            unidade_eixo, unidade_hover = "% em relação à média", "%"
        else:
            unidade_eixo, unidade_hover = "°C em relação à média", " °C"

        series = []   # (índice do local, tabela, valores) dos locais visíveis
        for i, chave in enumerate(locais):
            if not mostrar["locais"][i]:
                continue
            a = analises[(chave, coluna)]
            t = a["tabela"]
            y = transformar(t[coluna], a["media"], coluna, modo)
            nome = REGIOES[chave]["titulo"]
            cor = CORES_LOCAL[i]
            # Linha com os valores do local escolhido.
            textos = [num(valor, v["casas"], sinal=diferenca) for valor in y]
            fig.add_trace(go.Scatter(
                x=t["ano"], y=y, mode="lines", name=nome, legendgroup=nome,
                showlegend=legenda and linha == 1, line=dict(color=cor, width=2.5),
                customdata=np.column_stack([textos, t["fase"].fillna("sem fase")]),
                hovertemplate=f"{nome}: %{{customdata[0]}}{unidade_hover} · %{{customdata[1]}}<extra></extra>",
            ), row=linha, col=1)
            # a reta de tendência (Sen), tracejada
            if mostrar["tendencia"]:
                fig.add_trace(go.Scatter(
                    x=t["ano"], y=transformar(t["tendencia"], a["media"], coluna, modo), mode="lines",
                    legendgroup=nome, showlegend=False,
                    line=dict(color=cor, width=1.5, dash="dash"), hoverinfo="skip",
                ), row=linha, col=1)
            series.append((i, t, y))

        # Destaca os anos de El Niño e La Niña no gráfico.
        for i, t, y in series:
            for fase in ["El Niño", "La Niña"]:
                if not mostrar[fase]:
                    continue
                filtro = t["fase"] == fase
                fig.add_trace(go.Scatter(
                    x=t.loc[filtro, "ano"], y=y[filtro], mode="markers", legendgroup=fase, showlegend=False,
                    marker=dict(color=CORES_FASE[fase], size=14, symbol=SIMBOLOS_LOCAL[i],
                                line=dict(color=CORES_LOCAL[i], width=2.5)),
                    hoverinfo="skip",
                ), row=linha, col=1)
        if diferenca:
            fig.add_hline(y=0, line=dict(color="#9e9e9e", width=1), row=linha, col=1)
        fig.update_yaxes(title_text=f"{v['nome']} ({unidade_eixo})", row=linha, col=1)

    # Mostra o índice ONI, que acompanha a temperatura do Pacífico.
    if tem_oni:
        o = oni[oni["x"].between(ano_ini - 0.5, ano_fim + 0.5)]
        fig.add_trace(go.Bar(
            x=o["x"], y=o["ANOM"], marker_color=o["fase"].map(CORES_FASE), marker_line_width=0,
            name="ONI", showlegend=False,
            customdata=np.column_stack([o["SEAS"], o["YR"], o["fase"], [num(a, 1, sinal=True) for a in o["ANOM"]]]),
            hovertemplate="ONI %{customdata[0]} %{customdata[1]}: %{customdata[3]} °C · %{customdata[2]}<extra></extra>",
        ), row=linhas_total, col=1)
        for limite in (0.5, -0.5):
            fig.add_hline(y=limite, line=dict(color="#9e9e9e", width=1, dash="dot"), row=linhas_total, col=1)
        fig.update_yaxes(title_text="ONI (°C)", row=linhas_total, col=1)

    # Adiciona os itens da legenda no relatório exportado.
    if legenda:
        for fase in ["El Niño", "La Niña"]:
            if mostrar[fase]:
                fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=f"anos de {fase}",
                                         legendgroup=fase, marker=dict(color=CORES_FASE[fase], size=14),
                                         hoverinfo="skip"), row=1, col=1)
        if mostrar["tendencia"]:
            fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="tendência",
                                     line=dict(color="#9e9e9e", width=1.5, dash="dash"), hoverinfo="skip"),
                          row=1, col=1)

    fig.update_xaxes(hoverformat=".0f")
    fig.update_xaxes(title_text="Ano", row=linhas_total, col=1)
    fig.update_layout(
        height=330 * len(colunas) + (190 if tem_oni else 0) + (70 if legenda else 40),
        margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified", bargap=0,
        showlegend=legenda, legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        font=dict(size=14),
        separators=",.",   # vírgula decimal nos números do gráfico
    )
    return fig


def grafico_fases(analises, coluna, locais):
    """Passo 6: anomalia média em cada fase, os dois locais lado a lado."""
    v = VARIAVEIS[coluna]
    fig = go.Figure()
    numeros = []
    for i, chave in enumerate(locais):
        medias = analises[(chave, coluna)]["medias"]
        numeros += [x for x in medias.values if pd.notna(x)]
        fig.add_trace(go.Bar(
            x=medias.index, y=medias.values, name=REGIOES[chave]["titulo"], marker_color=CORES_LOCAL[i],
            text=[fmt_diferenca(x, coluna) if pd.notna(x) else "" for x in medias.values],
            textposition="outside", cliponaxis=False,
        ))
    # Cria um espaço para que os valores das barras não fiquem cortados.
    menor, maior = min([0] + numeros), max([0] + numeros)
    folga = (maior - menor) * 0.3 or 1
    fig.update_layout(
        barmode="group", height=300, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        yaxis_title=f"anomalia ({v['sufixo']})", yaxis_range=[menor - folga, maior + folga],
        font=dict(size=14), separators=",.",
    )
    return fig


def mapa_pontos(locais, escuro=True):
    """Mapa pequeno: as 9 regiões em cinza e os dois locais escolhidos em destaque."""
    if escuro:
        terra, oceano, fronteira, cinza = "#3b4252", "#1c212b", "#545b69", "#8b919c"
    else:
        terra, oceano, fronteira, cinza = "#d9dde3", "#f3f6f9", "#b8bec8", "#7b8494"
    fig = go.Figure()
    outros = [c for c in CHAVES if c not in locais]
    fig.add_trace(go.Scattergeo(
        lat=[REGIOES[c]["lat"] for c in outros], lon=[REGIOES[c]["lon"] for c in outros],
        text=[REGIOES[c]["titulo"] for c in outros], hoverinfo="text", mode="markers",
        marker=dict(size=6, color=cinza),
    ))
    for i, chave in enumerate(locais):
        r = REGIOES[chave]
        fig.add_trace(go.Scattergeo(
            lat=[r["lat"]], lon=[r["lon"]], text=[str(i + 1)], hovertext=[f"Local {i + 1}: {r['titulo']}"],
            hoverinfo="text", mode="markers+text", textposition="top center",
            textfont=dict(color=CORES_LOCAL[i], size=13),
            marker=dict(size=12, color=CORES_LOCAL[i], line=dict(color="white", width=1.5)),
        ))
    fig.update_geos(
        projection_type="natural earth", showframe=False, showcoastlines=False,
        showland=True, landcolor=terra, showocean=True, oceancolor=oceano,
        showcountries=True, countrycolor=fronteira, bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(height=140, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
    return fig


# ============================================================
# PARTE 4 - Criação do relatório
# ============================================================
def negrito_html(texto):
    """Troca o **negrito** do Markdown por <strong> (e protege o resto do texto)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(texto))


def gerar_relatorio(locais, colunas, ano_ini, ano_fim, analises, destaques, anotacao, figuras):
    nomes = [REGIOES[c]["titulo"] for c in locais]
    titulo = f"{TITULO}: {nomes[0]} × {nomes[1]}"
    partes = [
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>{html.escape(titulo)}</title>",
        "<style>"
        "body{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;"
        "color:#1f2328;line-height:1.5}"
        "table{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem}"
        "th,td{border:1px solid #d0d7de;padding:.4rem .6rem;text-align:left}th{background:#f6f8fa}"
        ".nota{white-space:pre-wrap;background:#f6f8fa;padding:1rem;border-radius:6px}"
        ".subtitulo{letter-spacing:.12em;color:#57606a;margin-top:-.5rem}"
        "</style></head><body>",
        f"<h1>{html.escape(titulo)}</h1>",
        f"<p class='subtitulo'>{html.escape(SUBTITULO)}</p>",
        f"<p>Gerado em {date.today():%d/%m/%Y} · Período: {ano_ini}–{ano_fim}</p>",
        "<h2>Padrões nos dados</h2>",
        f"<p><em>{html.escape(AVISO_INSIGHTS)}</em></p>",
    ]
    for nome_variavel, textos in destaques.items():
        partes.append(f"<h3>{html.escape(nome_variavel)}</h3><ul>")
        partes += [f"<li>{negrito_html(t)}</li>" for t in textos]
        partes.append("</ul>")
    partes.append(f"<p><small>{html.escape(COMO_PADROES)}</small></p>")
    partes.append("<h2>Resumo dos resultados</h2>")
    partes.append(f"<p>{html.escape(INTRO_RESUMO)}</p>")
    for coluna in colunas:
        partes.append(f"<h3>{VARIAVEIS[coluna]['nome']}</h3>")
        partes.append(tabela_html(linhas_resumo(analises, coluna, locais), locais))
        partes.append("<p><small>* = p &lt; 0,05.</small></p>")
    if colunas:
        partes.append("<h3>Como ler cada linha da tabela</h3><ul>")
        partes += [f"<li>{negrito_html(item)}</li>" for item in COMO_LER_TABELA]
        partes.append("</ul>")
    partes.append("<h2>Gráficos</h2>")
    for i, (nome, fig) in enumerate(figuras):
        partes.append(f"<h3>{html.escape(nome)}</h3>")
        partes.append(fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False))
    nota = html.escape(anotacao) if anotacao.strip() else "<em>Sem anotações.</em>"
    partes += ["<h2>Anotações e laudo</h2>", f"<div class='nota'>{nota}</div>",
               "<h2>Como foi feita a análise</h2>",
               *[f"<p>{negrito_html(t)}</p>" for t in texto_metodo()],
               f"<p><small>{html.escape(RODAPE)}</small></p></body></html>"]
    return "\n".join(partes)


# ============================================================
# PARTE 5 - Montagem da página do aplicativo
# ============================================================
ANO_MIN, ANO_MAX = limites_anos()


# Botão para trocar entre o tema claro e o tema escuro.
# Depois de mudar a configuração, atualizamos a página para aplicar o tema.
escuro = st._config.get_option("theme.base") != "light"
col_titulo, col_tema = st.columns([5, 1], vertical_alignment="center")
with col_titulo:
    st.title(TITULO)
    st.markdown(f"<div style='margin-top:-0.75rem;letter-spacing:.12em;font-size:.95rem;opacity:.75'>"
                f"{SUBTITULO}</div>", unsafe_allow_html=True)
if col_tema.button("Mudar para tema claro" if escuro else "Mudar para tema escuro", key="tema"):
    st._config.set_option("theme.base", "light" if escuro else "dark")
    st.rerun()
with st.container(border=True):
    st.markdown(
        "**Um fenômeno, diferentes regiões.** O El Niño aquece as águas do Pacífico equatorial. "
        "A La Niña provoca o resfriamento dessas águas. "
        f"Escolha duas regiões e um período para comparar os dados de chuva e temperatura da NASA "
        f"({ANO_MIN}–{ANO_MAX}) e observar como eles variam durante El Niño, La Niña e anos neutros."
    )

# Adiciona uma cor ou um símbolo antes de cada item da legenda.
# O CSS abaixo usa as chaves dos controles do Streamlit para fazer isso.
SIMBOLOS_LEGENDA = {
    "leg_local1": ("━", CORES_LOCAL[0]), "leg_local2": ("━", CORES_LOCAL[1]),
    "leg_elnino": ("●", CORES_FASE["El Niño"]), "leg_lanina": ("●", CORES_FASE["La Niña"]),
    "leg_tendencia": ("╌", "#9e9e9e"),
}
css = "".join(f".st-key-{chave} [data-testid='stMarkdownContainer'] p::before"
              f"{{content:'{simbolo} ';color:{cor};font-weight:700}}"
              for chave, (simbolo, cor) in SIMBOLOS_LEGENDA.items())
css += (".st-key-leg_oni [data-testid='stMarkdownContainer'] p::before{content:'▮▮ ';font-weight:700;"
        f"background:linear-gradient(90deg,{CORES_FASE['El Niño']} 50%,{CORES_FASE['La Niña']} 50%);"
        "-webkit-background-clip:text;background-clip:text;color:transparent}")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

esquerda, centro, direita = st.columns([1.1, 3.2, 1.3], gap="medium")

# --- Centro, parte de cima: os filtros ---
with centro:
    # Escolha dos anos e dos dados que serão mostrados.
    col_de, col_ate, col_chuva, col_temp = st.columns([1, 1, 0.8, 1.2], vertical_alignment="bottom")
    anos = list(range(ANO_MIN, ANO_MAX + 1))
    ano_ini = col_de.selectbox("Período", anos, index=0, key="ano_ini")
    ano_fim = col_ate.selectbox("até", anos, index=len(anos) - 1, key="ano_fim")
    ver_chuva = col_chuva.toggle("Chuva", value=True, key="ver_chuva")
    ver_temp = col_temp.toggle("Temperatura", value=False, key="ver_temp")

    # Escolha das duas regiões que serão comparadas.
    ROTULOS = {f"{r['titulo']} (trio {r['trio']})": c for c, r in REGIOES.items()}
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### <span style='color:{CORES_LOCAL[0]}'>●</span> Local 1", unsafe_allow_html=True)
        local1 = ROTULOS[st.selectbox("Local 1", list(ROTULOS), index=CHAVES.index("Sertao Nordeste"),
                                      label_visibility="collapsed", key="local1")]
    with col2:
        st.markdown(f"### <span style='color:{CORES_LOCAL[1]}'>●</span> Local 2", unsafe_allow_html=True)
        local2 = ROTULOS[st.selectbox("Local 2", list(ROTULOS), index=CHAVES.index("Sul do Brasil"),
                                      label_visibility="collapsed", key="local2")]


    # Verifica se as escolhas permitem fazer a comparação.
    problema = None
    if local1 == local2:
        problema = "Escolha duas regiões diferentes para comparar."
    elif not (ver_chuva or ver_temp):
        problema = "Ligue Chuva ou Temperatura para ver os gráficos."
    elif ano_ini > ano_fim:
        problema = "O ano inicial precisa vir antes do ano final."
    elif ano_fim - ano_ini + 1 < 10:
        problema = "Escolha um período de pelo menos 10 anos: com menos, os testes não são confiáveis."
    if problema:
        st.warning(problema)
        st.stop()

locais = [local1, local2]
colunas = [c for c, ligado in [("chuva_mm", ver_chuva), ("temp_c", ver_temp)] if ligado]
analises = {(c, col): analisar(c, col, ano_ini, ano_fim) for c in locais for col in VARIAVEIS}
destaques = gerar_destaques(analises, colunas, locais)
oni = carregar_oni()

# Gráficos e resumo dos resultados.
with centro:
    with st.container(border=True):
        cab_grafico, col_modo = st.columns([1, 1.4], vertical_alignment="center")
        cab_grafico.markdown("#### Mudanças ao longo do tempo")
        modo = col_modo.radio("Mostrar como", MODOS, horizontal=True, key="modo")

        explicacao = ("Cada linha representa uma região. Os pontos vermelhos indicam El Niño e os azuis, "
                      "La Niña. A linha tracejada mostra a tendência. Use as caixas abaixo para mostrar ou "
                      "esconder informações e passe o mouse sobre o gráfico para ver os valores.")
        if modo == MODOS[1]:
            explicacao += (" Em \"Diferença da média\", cada região é comparada com a sua própria média. "
                           "Assim, fica mais fácil comparar regiões com valores muito diferentes.")
        st.caption(explicacao)

        # Permite escolher quais informações aparecem no gráfico.
        linhas_legenda = [
            [("leg_local1", REGIOES[local1]["titulo"]), ("leg_local2", REGIOES[local2]["titulo"]),
             ("leg_tendencia", "tendência")],
            [("leg_elnino", "anos de El Niño"), ("leg_lanina", "anos de La Niña")]
            + ([("leg_oni", "índice ONI")] if oni is not None else []),
        ]
        marcados = {}
        for itens in linhas_legenda:
            for (chave, rotulo), col in zip(itens, st.columns([1.3, 1.3, 1])):
                marcados[chave] = col.checkbox(rotulo, value=True, key=chave)
        mostrar = {"locais": [marcados["leg_local1"], marcados["leg_local2"]],
                   "El Niño": marcados["leg_elnino"], "La Niña": marcados["leg_lanina"],
                   "tendencia": marcados["leg_tendencia"], "oni": marcados.get("leg_oni", False)}

        fig_tempo = grafico_temporal(analises, colunas, locais, modo, oni, ano_ini, ano_fim, mostrar)
        st.plotly_chart(fig_tempo, key="grafico_temporal")
        if oni is not None and mostrar["oni"]:
            st.caption("O gráfico inferior mostra o índice ONI da NOAA. Ele indica quanto a temperatura "
                       "do Pacífico equatorial está acima ou abaixo da média. Vermelho representa El Niño "
                       "e azul representa La Niña. A costa do Peru e o Altiplano usam o índice Niño 1+2.")
        elif oni is None:
            st.info("Para mostrar o índice ONI, execute `python main.py` novamente. "
                    "Esse comando cria o arquivo `dados/oni.csv`.")

    figuras_fases = {}
    with st.container(border=True):
        cabecalho, botao = st.columns([3, 1.5], vertical_alignment="center")
        cabecalho.markdown("#### Resumo dos resultados")
        with botao.popover("Como foi feita esta análise?"):
            st.markdown("\n\n".join(texto_metodo()))
        st.markdown(INTRO_RESUMO)

        for coluna in colunas:
            st.markdown(f"##### {VARIAVEIS[coluna]['nome']}")
            # A tabela mostra os resultados. A interpretação fica por conta de quem analisa.
            st.markdown(tabela_markdown(linhas_resumo(analises, coluna, locais), locais),
                        unsafe_allow_html=True)
            figuras_fases[coluna] = grafico_fases(analises, coluna, locais)
            st.plotly_chart(figuras_fases[coluna], key=f"fases_{coluna}")
            st.caption("Cada barra mostra a diferença em relação à tendência da região. "
                       "Valores positivos ficam acima da tendência; valores negativos ficam abaixo.")
        with st.expander("Como ler cada linha da tabela"):
            st.markdown("\n".join(f"- {item}" for item in COMO_LER_TABELA))
        st.caption("\\* = p-valor menor que 0,05. Para entender cada passo da análise, abra "
                   "\"Como foi feita esta análise?\".")

# Mapa e informações das regiões escolhidas.
with esquerda:
    with st.container(border=True):
        st.markdown("**Localização das regiões**")
        st.plotly_chart(mapa_pontos(locais, escuro), key="mapa", config={"displayModeBar": False})
    for i, chave in enumerate(locais):
        r, d = REGIOES[chave], DADOS_REGIOES[chave]
        meses = ", ".join(NOMES_MESES[m - 1] for m in d["meses"])
        cidades = ", ".join(nome for nome, _, _ in d["cidades"])
        with st.container(border=True):
            st.markdown(f"<span style='color:{CORES_LOCAL[i]}'>●</span> **Local {i + 1}: {r['titulo']}**",
                        unsafe_allow_html=True)
            st.caption(f"Grupo: {r['trio']} · classificação: {r['papel'].lower()}")
            for rotulo, valor in [("Chuva média na estação", f"{num(analises[(chave, 'chuva_mm')]['media'], 0)} mm"),
                                  ("Temperatura média", f"{num(analises[(chave, 'temp_c')]['media'], 1)} °C")]:
                st.markdown(f"<div style='font-size:.85rem;opacity:.75'>{rotulo}</div>"
                            f"<div style='font-size:1.5rem;font-weight:600;margin-bottom:.5rem'>{valor}</div>",
                            unsafe_allow_html=True)
            st.caption(f"**Estação:** {meses}  \n**Fase do ENSO:** {NOMES_INDICE[d['indice']]}  \n"
                       f"**Cidades:** {cidades}")

# Padrões encontrados, anotações e exportação do relatório.
with direita:
    with st.container(border=True):
        st.markdown("#### O que aparece nos dados")
        st.info(AVISO_INSIGHTS)
        for nome_variavel, textos in destaques.items():
            st.markdown(f"**{nome_variavel}**\n\n" + "\n".join(f"- {texto}" for texto in textos))
        st.caption(COMO_PADROES)
    with st.container(border=True):
        st.markdown("#### Anotações da equipe")
        anotacao = st.text_area("Anotações", key="anotacao", height=260, label_visibility="collapsed",
                                placeholder="Escreva aqui o que você observou nos gráficos e tabelas...")
        fig_tempo_relatorio = grafico_temporal(analises, colunas, locais, modo, oni, ano_ini, ano_fim,
                                               mostrar, legenda=True)
        figuras = [("Gráfico temporal", fig_tempo_relatorio)] + [
            (f"{VARIAVEIS[c]['nome']}: El Niño × neutro × La Niña", figuras_fases[c]) for c in colunas
        ]
        relatorio = gerar_relatorio(locais, colunas, ano_ini, ano_fim, analises, destaques, anotacao, figuras)
        st.download_button("Baixar relatório", data=relatorio, mime="text/html",
                           file_name=f"relatorio_{local1}_x_{local2}.html".lower().replace(" ", "_"))
        st.caption("O arquivo HTML reúne os gráficos, as tabelas, os padrões e as suas anotações. "
                   "Antes de exportar, pressione Ctrl+Enter para salvar o texto da anotação.")

st.divider()
st.caption(RODAPE)