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

A validação é **walk-forward**, com 30 janelas sucessivas cobrindo o período de
teste de janeiro de 2018 a dezembro de 2022, num total de 1826 dias previstos.
Em cada janela quatro estratégias competem entre si, `base_only`,
`residual_only`, `direct_only` e `blend`, e vence a que apresenta o menor RMSE de
validação, com limiar de melhora de 0,5%.

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
│   ├── README.md                   dicionário de dados e fontes
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
│   ├── README.md                   índice das 33 figuras
│   ├── png/                        raster, 300 dpi
│   └── pdf/                        vetorial
└── docs/
    └── mapa_de_nomes.md            correspondência entre nomes antigos e novos
```

---

## Como executar

Instale as dependências e rode o script único.

```bash
pip install -r requirements.txt
python src/pipeline_walkforward.py
```

O script foi escrito para rodar em notebook local, com caminhos de entrada e
saída definidos no topo do arquivo. Ajuste o caminho da planilha e da pasta de
saída antes de executar. O CatBoost é instalado automaticamente se não estiver
presente.

A busca bayesiana de hiperparâmetros com Optuna está implementada, mas ficou
desativada na execução que gerou os resultados deste repositório. Os valores
usados são os que estão em `config/model_config.json`.

---

## Resultados principais

Médias das 30 janelas de validação walk-forward.

| Métrica | Média | Desvio padrão |
|---|---|---|
| MAE | 18,21 | 5,32 |
| RMSE | 23,53 | 6,60 |
| R² | 0,375 | 0,331 |
| MAPE | 15,0% | 5,21 |
| RMSLE | 0,184 | 0,055 |

O R² por fold é baixo porque cada janela cobre apenas dois meses, o que reduz a
variância disponível. Consolidado por ano o desempenho é bem maior, com R² de
0,79 em 2018 e 0,81 em 2019.

Ganho médio sobre a baseline melhorada, 0,028 por fold. Entre as 30 janelas a
estratégia `blend` venceu 23 vezes, `direct_only` 4, `residual_only` 2 e
`base_only` 1.

As quatro variáveis ambientais mais relevantes pelo SHAP médio absoluto são
temperatura média, PM2,5, NO₂ e CO, nessa ordem.

---

## Fontes de dados

Internações do SIH/SUS, poluentes da CETESB e variáveis meteorológicas do INMET,
para o município de São Paulo, de 2017 a 2022. Detalhes de cada coluna estão em
[`data/README.md`](data/README.md).

---

## Licença

A definir. Sugestão de MIT para o código e CC BY 4.0 para figuras e dados
derivados, respeitando os termos originais de cada fonte pública.

## Como citar

A referência completa da tese será incluída aqui após a defesa.
