# Previsão diária de internações por doenças respiratórias em São Paulo

Código, dados e resultados da tese de doutorado em Modelagem Computacional
desenvolvida na Universidade Federal do Rio Grande (FURG).

O trabalho aplica um modelo híbrido de aprendizado de máquina para prever o
número diário de internações por doenças respiratórias no município de São Paulo
a partir de variáveis de poluição do ar e de meteorologia.

**Autor** Gabriel Fuscald Scursone
**Orientadora** Dra. Diana Francisca Adamatti
**Programa** Pós-Graduação em Modelagem Computacional, FURG

---

## Sobre o modelo

O pipeline combina dois modelos em sequência. Um **ElasticNet** capta a estrutura
temporal da série, com defasagens do alvo, médias móveis e sazonalidade. Um
**CatBoost** corrige os resíduos não lineares usando 12 variáveis ambientais
brutas.

A validação é **walk-forward**, com 30 janelas bimestrais sucessivas. O período
de teste vai de 1 de janeiro de 2018 a 31 de dezembro de 2022, num total de
1.826 dias previstos. O ano de 2017 não entra no teste porque serve como janela
inicial de treino e alimenta as defasagens anuais de 364 e 365 dias. A primeira
janela treina com dados até 31 de dezembro de 2017 e prevê janeiro e fevereiro
de 2018.

Em cada janela quatro estratégias competem entre si, `base_only`,
`residual_only`, `direct_only` e `blend`, e vence a que apresenta o menor RMSE de
validação. O modelo base só é substituído quando outra estratégia melhora esse
RMSE em pelo menos 0,5%.

A interpretabilidade é feita com SHAP sobre as 12 variáveis ambientais e
meteorológicas.

### Variável alvo

`HOSPCIDX`, internações diárias por causas do Capítulo X da CID-10, doenças do
aparelho respiratório.

### Variáveis ambientais e meteorológicas

PM10, PM2,5, O₃, NO₂, SO₂, CO, temperatura média, umidade relativa,
precipitação, radiação, velocidade do vento e pressão atmosférica.

---

## Estrutura do repositório

```
.
├── src/
│   └── pipeline_walkforward.py     script único com todo o pipeline
├── config/
│   └── model_config.json           hiperparâmetros usados na execução
├── data/
│   └── sp_hosp_ar_meteo_2017_2022.xlsx
├── results/
│   ├── run_summary.json            resumo da execução
│   ├── walkforward_results_by_fold.csv
│   ├── walkforward_results_by_year.csv
│   ├── walkforward_summary_mean_std.csv
│   ├── walkforward_predictions_concat.csv
│   ├── fig29_env_feature_importance_only_raw.csv
│   └── fig30_shap_mean_abs_only_raw_env.csv
├── figures/
│   ├── png/                        raster, 300 dpi
│   └── pdf/                        vetorial
├── docs/
│   └── mapa_de_nomes.md            correspondência entre nomes antigos e novos
├── requirements.txt
├── LICENSE
└── .gitignore
```

---

## A base de dados

O arquivo `data/sp_hosp_ar_meteo_2017_2022.xlsx` tem uma única aba, chamada
`data_clean`, com 2.191 linhas e 56 colunas. Cada linha é um dia, de 1 de
janeiro de 2017 a 31 de dezembro de 2022.

As 56 colunas se organizam em quatro blocos.

| Bloco | Quantidade | Conteúdo |
|---|---|---|
| Data | 1 | coluna `Data`, índice temporal diário |
| Ambientais e meteorológicas | 12 | os seis poluentes e as seis variáveis meteorológicas listadas acima |
| Desfechos hospitalares e de mortalidade | 40 | 20 colunas com prefixo `HOSPCID` e 20 com prefixo `MORTCID`, separadas por capítulo da CID-10 |
| Auxiliares | 3 | colunas com prefixo `AUX_`, descritas abaixo |

Das 56 colunas, o pipeline usa 13, a variável alvo `HOSPCIDX` e as 12 ambientais.
As demais colunas hospitalares e de mortalidade ficam disponíveis para quem
quiser aplicar o mesmo método a outros desfechos.

### As três colunas auxiliares

As colunas `AUX_HOSPCIDX_ESTIMADO_COVID`, `AUX_MARCADOR_COVID_2020_2021` e
`AUX_INTENSIDADE_ONDA_COVID` foram geradas em etapas preliminares de preparação
da base e não são utilizadas pelo pipeline. Nenhum desses três nomes aparece no
código de `src/pipeline_walkforward.py`, e as três só assumem valores variáveis
nos anos de 2020 e 2021. Foram mantidas no arquivo para que a base publicada
corresponda exatamente à base descrita na tese.

### Fontes

Internações do SIH/SUS, poluentes da CETESB e variáveis meteorológicas do INMET,
para o município de São Paulo, de 2017 a 2022. A integração entre as três fontes
foi feita por linkage determinístico, com correspondência exata de data diária e
município.

---

## Como executar

O script foi escrito para rodar em computador pessoal, com os caminhos de entrada
e de saída definidos no topo do arquivo. Antes de executar, abra
`src/pipeline_walkforward.py` e ajuste a constante `EXCEL_PATH` para o caminho da
planilha na sua máquina, e a pasta de saída para onde quiser gravar os
resultados.

Depois disso, instale as dependências e rode o script.

```bash
pip install -r requirements.txt
python src/pipeline_walkforward.py
```

O CatBoost é instalado automaticamente caso não esteja presente. Ao final da
execução o script imprime o tempo total gasto.

Versão do Python utilizada na execução original, PREENCHER.

A busca bayesiana de hiperparâmetros com Optuna está implementada, mas ficou
desativada na execução que gerou os resultados deste repositório. Os valores
usados são os que estão em `config/model_config.json`.

---

## Resultados principais

### Médias das 30 janelas de validação

| Métrica | Média | Desvio padrão |
|---|---|---|
| MAE | 18,21 | 5,32 |
| RMSE | 23,53 | 6,60 |
| R² | 0,375 | 0,331 |
| MAPE | 15,0% | 5,2% |
| RMSLE | 0,184 | 0,055 |

O R² por janela é baixo porque cada janela cobre apenas dois meses, o que reduz
a variância disponível para o cálculo. Consolidado por ano o valor é bem maior.

### Desempenho por ano

| Ano | MAE | RMSE | R² | Dias |
|---|---|---|---|---|
| 2018 | 15,1 | 19,8 | 0,79 | 365 |
| 2019 | 13,9 | 17,9 | 0,81 | 365 |
| 2020 | 21,6 | 28,3 | 0,60 | 366 |
| 2021 | 23,0 | 29,6 | 0,64 | 365 |
| 2022 | 17,4 | 24,4 | 0,53 | 365 |

Os dois primeiros anos são os de melhor desempenho, e a queda a partir de 2020
acompanha a pandemia de COVID-19. Nesse período a série muda de nível e de
volatilidade de forma abrupta, e o modelo, treinado apenas com dados anteriores
a cada janela, não dispunha de exemplos de um regime parecido.

### Comparação com as baselines

Ganho médio do modelo sobre a baseline melhorada, 0,028 por janela e 0,024
consolidado por ano. Sobre a baseline semanal o ganho médio por janela é de
0,289 e sobre a baseline sazonal, de 0,385.

### Estratégias escolhidas

Entre as 30 janelas a estratégia `blend` venceu 23 vezes, `direct_only` 4,
`residual_only` 2 e `base_only` 1.

### Interpretabilidade

As quatro variáveis ambientais mais relevantes pelo SHAP médio absoluto são
temperatura média, PM2,5, NO₂ e CO, nessa ordem.

---

## Licença

O código deste repositório é distribuído sob a licença MIT, conforme o arquivo
`LICENSE`.

Os dados originais provêm de fontes públicas, SIH/SUS, CETESB e INMET. A licença
MIT não se estende a eles. Quem redistribuir ou reutilizar a base deve observar
os termos de cada uma dessas fontes.

## Como citar


A referência completa da tese será incluída aqui após a defesa.
