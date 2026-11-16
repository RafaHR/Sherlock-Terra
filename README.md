# Sherlock Terra: Detetive das Tendências do Sistema Terrestre

**Em busca das tendências terrestres.**


## Sobre o projeto

O **Sherlock Terra** é um projeto desenvolvido no contexto do **NASA Space Apps Challenge**, com o objetivo de tornar os dados de observação da Terra mais acessíveis e facilitar a investigação de tendências ambientais.

A proposta é oferecer uma ferramenta que permita explorar dados climáticos, identificar padrões ao longo do tempo e comparar o comportamento de diferentes regiões do planeta.

Na versão atual, desenvolvida como um protótipo MVP (*Minimum Viable Product*), o projeto trabalha com aproximadamente 45 anos de dados históricos (1981–2025), reunindo informações de precipitação e temperatura de nove regiões distribuídas pela América do Sul, Oceania e Europa.

O foco desta versão é investigar como essas regiões se comportam durante períodos de El Niño, La Niña e condições neutras.

O sistema apresenta os dados, as tendências e os resultados estatísticos para apoiar a investigação. A interpretação dos resultados fica a cargo do analista.

## Funcionalidades

### Comparação entre regiões

O usuário pode selecionar duas regiões por meio de menus de seleção e definir o intervalo de anos que deseja investigar.

Os dados são apresentados lado a lado, permitindo comparar o comportamento climático de cada local e observar possíveis diferenças e semelhanças.

### Gráficos de precipitação e temperatura

O painel apresenta séries históricas de chuva e temperatura, com identificação dos períodos de El Niño e La Niña e suas respectivas linhas de tendência.

É possível escolher quais variáveis serão exibidas e alternar entre duas formas de visualização:

- **Valores observados:** apresenta os valores registrados em cada região.
- **Anomalias em relação à tendência:** mostra como os valores se comportaram em relação à tendência de longo prazo, facilitando a comparação entre regiões com volumes de chuva e características climáticas diferentes.

A legenda interativa permite mostrar ou ocultar os elementos do gráfico conforme a necessidade da análise.

### Mapa de regiões

O painel apresenta um mapa para visualizar a distribuição das regiões incluídas no projeto.

Essa visualização permite identificar onde estão localizados os pontos de análise e compreender melhor a distribuição espacial das regiões utilizadas nas comparações.

### Índice do fenômeno no Pacífico

O painel apresenta o índice ONI (que significa Oceanic Niño Index), disponibilizado pela NOAA, em uma série trimestral.

Esse indicador permite acompanhar as fases do ENSO e cruzar com os dados das condições climáticas observadas nas regiões selecionadas.

### Resumo estatístico

Uma tabela reúne os principais resultados dos cálculos realizados para cada região:

- Médias de precipitação e temperatura;
- Variação por década;
- Médias observadas em cada fase do ENSO;
- Diferença entre os períodos de El Niño e neutros;
- Valores de significância estatística p-valores;
- Hipótese de resposta climática definida para cada região.

Um gráfico complementar apresenta a média de cada variável nas diferentes fases do fenômeno.

Já o botão **"Como foi feita esta análise?"** explica os métodos utilizados e o significado dos indicadores estatísticos.

### Identificação de padrões

O painel apresenta informações calculadas a partir dos próprios dados, como:

- Quantidade de anos de El Niño e La Niña em que cada região ficou acima ou abaixo de sua tendência;
- Fases do ENSO associadas aos anos mais extremos;
- Correlação entre as séries históricas das duas regiões selecionadas.

Nesta versão, os textos apresentados nessa seção são gerados por regras fixas a partir dos resultados numéricos. Portanto, não representam uma interpretação produzida por inteligência artificial.

Uma das evoluções previstas é integrar um agente de IA capaz de analisar os indicadores apresentados e sugerir interpretações iniciais para auxiliar o trabalho do analista.

### Anotações e exportação de relatório

O usuário pode registrar suas observações e interpretações em um espaço destinado às anotações e ao laudo da análise.

Também é possível exportar um relatório em HTML contendo os gráficos, tabelas, padrões identificados, anotações e informações sobre a metodologia utilizada.

### Tema da interface

O painel oferece a opção de alternar entre os temas claro e escuro.

## Como executar o projeto

### Requisitos

O projeto utiliza Python e Streamlit.

Versões testadas durante o desenvolvimento:

- Python 3.15 com Streamlit 1.67.

### 1. Como Instalar as dependências

Iremos considerar que você já tem o Python 3.15 instalado e configurado em sua máquina.
No terminal, execute:

```bash
pip install -r requirements.txt
```

### 2. Atualizar os dados (opcional)

Os arquivos CSV já estão disponíveis na pasta `dados/`. Portanto, não é necessário executar esta etapa para abrir o painel.

Para baixar os dados novamente e atualizar os arquivos, execute:

```bash
python main.py
```

Essa etapa precisa de conexão com a internet e leva menos de um minuto, conforme os testes realizados durante o desenvolvimento.

### 3. Iniciar o painel

Execute:

```bash
streamlit run app.py
```

**Importante:** utilize `streamlit run` para iniciar o projeto. Executar `python app.py` não abre a interface do Streamlit.

O mapa apresentado no painel e alguns gráficos presentes no relatório exportado dependem de recursos carregados pela internet.

## Estrutura dos arquivos

Os conjuntos de dados utilizados pelo projeto ficam armazenados na pasta `dados/`.

O arquivo `main.py` é responsável por obter e organizar os dados, enquanto o `app.py` utiliza os arquivos gerados para construir o painel interativo.

```text
Projeto_Hackathonn/
├── app.py                  # Interface e funcionalidades do painel
├── main.py                 # Coleta e organização dos dados da NASA e NOAA
├── requirements.txt        # Bibliotecas necessárias para executar o projeto
├── README.md               # Documentação do projeto
├── .streamlit/
│   └── config.toml         # Configurações visuais do Streamlit
└── dados/
    ├── sertao_nordeste.csv
    ├── sul_do_brasil.csv
    ├── ...                 # 9 arquivos, um para cada região
    ├── oni.csv             # Índice ONI da NOAA
    └── antigos/            # Arquivos de versões anteriores
```

Cada arquivo CSV regional contém valores anuais de precipitação acumulada na estação chuvosa, temperatura média e fase do ENSO.

## Regiões analisadas

As nove regiões foram organizadas em três conjuntos de comparação. Em cada conjunto, foram selecionadas regiões com diferentes respostas esperadas à influência do El Niño sobre a precipitação.

Essas respostas formam as hipóteses iniciais do projeto. O painel apresenta os dados e os resultados estatísticos que permitem compará-las com o comportamento observado.

| Região | Conjunto | Papel | Hipótese para o El Niño | Cidades utilizadas | Estação analisada | Índice de referência |
|---|---|---|---|---|---|---|
| Sertão do Nordeste | Brasil | Afetada | Menos chuva | Crateús, Quixadá, Caicó | Fev–mai | ONI dez–fev |
| Sul do Brasil | Brasil | Contrária | Mais chuva | Santa Maria, Passo Fundo, Uruguaiana | Set–nov | ONI set–nov |
| Litoral leste do NE | Brasil | Fraca | Resposta fraca | Recife, João Pessoa, Maceió | Fev–mai | ONI dez–fev |
| Leste da Austrália | Pacífico | Afetada | Menos chuva | Roma, Moree, Dubbo | Set–nov | ONI set–nov |
| Kiribati | Pacífico | Contrária | Mais chuva | Tarawa, Butaritari, Abemama | Set–nov | ONI set–nov |
| Sudoeste da Austrália | Pacífico | Fraca | Resposta fraca | Perth, Bunbury, Narrogin | Jun–ago | ONI jun–ago |
| Costa norte do Peru | Conjunto 3 | Afetada | Mais chuva | Machala (Equador), Piura, Chiclayo | Jan–abr | Niño 1+2 |
| Altiplano (Titicaca) | Conjunto 3 | Contrária | Menos chuva | Puno, Juliaca, Ayaviri | Jan–abr | Niño 1+2 |
| Península Ibérica | Conjunto 3 | Fraca | Resposta fraca | Lisboa, Madri, Sevilha | Jan–mar | ONI dez–fev |

O terceiro conjunto reúne regiões dos Andes e da Europa, organizadas para fins de comparação. A seleção da Costa norte do Peru também inclui Machala, no Equador.

## Fontes de dados

Os dados utilizados no projeto são obtidos de fontes públicas disponibilizadas por instituições científicas.

### Precipitação e temperatura: NASA POWER

Os dados climáticos são obtidos pela plataforma [NASA POWER](https://power.larc.nasa.gov/), que disponibiliza informações meteorológicas e climáticas.

O projeto utiliza os seguintes itens:

- `PRECTOTCORR`: precipitação corrigida;
- `T2M`: temperatura média a 2 metros de altura.

Os dados são organizados em uma escala mensal e utilizados para calcular os indicadores anuais de cada região, a partir da reanálise MERRA-2.

### Fases do ENSO: NOAA

O índice ONI (*Oceanic Niño Index*), disponibilizado pelo [Climate Prediction Center da NOAA](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt), é utilizado para identificar os períodos de El Niño, La Niña e condições neutras.

### Costa do Peru e Altiplano: Índice Niño 1+2

Para essas regiões, também é utilizado o [índice Niño 1+2 da NOAA](https://www.cpc.ncep.noaa.gov/data/indices/rel_mthsst9120.txt), relacionado às condições de temperatura da superfície do mar no Pacífico equatorial leste.

## Metodologia de análise

O processamento dos dados segue as etapas descritas abaixo.

### 1. Coleta e organização

São obtidos dados mensais de precipitação e temperatura para três cidades de cada região. Em seguida, os valores das três cidades são utilizados para representar o comportamento médio da região.

### 2. Definição da estação analisada

Para cada região, é definida uma estação do ano considerada relevante para a análise da precipitação.

A chuva acumulada nos meses dessa estação é calculada para cada ano, enquanto a temperatura é representada pela média dos meses correspondentes. Dessa forma, cada região passa a ter um conjunto de valores anuais.

### 3. Classificação das fases do ENSO

Cada ano recebe uma classificação de acordo com a fase do ENSO correspondente ao trimestre de referência da região.

Para o índice ONI:

- **El Niño:** anomalia de temperatura do Pacífico igual ou superior a +0,5 °C durante pelo menos cinco trimestres consecutivos;
- **La Niña:** anomalia igual ou inferior a -0,5 °C durante pelo menos cinco trimestres consecutivos;
- **Neutro:** períodos que não atendem aos critérios anteriores.

Para a Costa norte do Peru e o Altiplano, é utilizado o índice Niño 1+2, considerando os limites de ±0,5 °C por pelo menos três meses consecutivos entre janeiro e abril.

### 4. Análise de tendências

A identificação de tendências de longo prazo é realizada utilizando o teste de Mann-Kendall modificado, que considera a possibilidade de autocorrelação entre os valores de anos consecutivos.

A tendência em si é calculada utilizando a inclinação de Sen, que permite estimar a variação dos indicadores ao longo do tempo.

### 5. Cálculo das anomalias

Antes de comparar as diferentes fases do ENSO, a tendência de longo prazo é retirada dos dados.

Essa etapa ajuda a separar as variações associadas às fases do fenômeno das mudanças graduais observadas ao longo dos anos.

As anomalias são expressas em porcentagem em relação à tendência para a precipitação e em graus Celsius para a temperatura.

### 6. Teste de permutação

A diferença entre a média dos anos de El Niño e a média dos anos neutros é avaliada por meio de um teste de permutação.

Em resumo, o procedimento realiza 10.000 sorteios, embaralhando as classificações de El Niño e neutro para construir uma distribuição de diferenças simuladas.

O p-valor representa a proporção dos sorteios que apresentam uma diferença igual ou superior à observada. Valores menores indicam que uma diferença desse tamanho seria menos frequente, dando a entender que existe uma ausência de associação entre a fase do ENSO e a variável analisada.

Na tabela de resultados, o símbolo `*` indica valores de p inferiores a 0,05.

**Observação:** todos os cálculos consideram somente os anos pertencentes ao intervalo selecionado pelo usuário no painel, respeitando um mínimo de dez anos de dados.

O sistema apresenta resultados quantitativos e indicadores estatísticos, mas não estabelece relações de causa e efeito nem substitui a interpretação do analista.

## Limitações

Algumas limitações devem ser consideradas durante a interpretação dos resultados:

- **Associação não significa causa:** os resultados indicam possíveis relações entre as fases do ENSO e as variáveis climáticas, mas não comprovam que o fenômeno seja a única causa das alterações observadas.
- **Quantidade de observações:** algumas regiões possuem poucos anos classificados como El Niño ou La Niña, o que pode reduzir a sensibilidade dos testes estatísticos.
- **Dados de reanálise:** os dados utilizados podem apresentar diferenças em relação às medições realizadas diretamente por estações meteorológicas.
- **Interpretação dos padrões:** os textos da seção de padrões são gerados como exemplos, devem ser tratados como indicadores descritivos, não como conclusões científicas, esse é o papel do investigador.

## Próximos passos

O Sherlock Terra foi desenvolvido como um protótipo MVP, com foco em apresentar uma primeira versão funcional da ferramenta de investigação climática.

Entre as principais evoluções planejadas estão:

### Novas variáveis ambientais

Inclusão de informações sobre umidade do solo, concentração de aerossóis e outros indicadores relevantes para a investigação climática.

### Novas fontes de dados

Integração com outros conjuntos de dados de observação da Terra, como MODIS e GPM, ampliando as possibilidades de análise e comparação.

### Integração de um agente de inteligência artificial

A proposta é integrar um agente de IA à seção "Padrões nos dados". Esse agente poderá receber os resultados numéricos do painel, como tendências, diferenças entre fases e valores de significância estatística, para produzir sugestões de interpretação.

Essas sugestões deverão servir como ponto de partida para o analista, que poderá revisar, corrigir e complementar as observações antes de registrar seu laudo.

A integração com IA deverá funcionar como uma ferramenta de apoio à investigação, mantendo os dados científicos e os métodos estatísticos como base para a análise.

## Uso de inteligência artificial

Durante o desenvolvimento do Sherlock Terra, ferramentas de inteligência artificial foram utilizadas como apoio à equipe em diferentes etapas do projeto, principalmente nas seguintes atividades:

- **Pesquisa:** levantamento de informações sobre fenômenos climáticos, indicadores ambientais, fontes de dados e métodos de análise.
- **Depuração de código (*debugging*):** identificação de erros, compreensão de mensagens de exceção e busca por possíveis soluções durante a implementação.
- **Desenvolvimento do Frontend:** auxílio na criação e organização da interface em Streamlit, incluindo componentes visuais, gráficos e elementos interativos.
- **Documentação:** apoio à elaboração e revisão de textos técnicos e instruções de utilização.

As ferramentas foram utilizadas como suporte ao trabalho da equipe, que permaneceu responsável pelas decisões de desenvolvimento, escolhas metodológicas e avaliação dos resultados.
