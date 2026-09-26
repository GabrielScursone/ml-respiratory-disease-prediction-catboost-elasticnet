# Dashboard

Painel interativo em Streamlit com os resultados da validação walk-forward do
modelo híbrido ElasticNet + CatBoost. O painel lê os arquivos de `results/` e de
`config/` deste repositório e não treina nenhum modelo.

## O que o painel mostra

- A série diária observada e prevista, com uma faixa de variação esperada e os
  dias em que o observado passou dessa faixa, chamados de sinais.
- Os episódios de dias seguidos com sinal e a distribuição dos sinais por mês.
- A qualidade do modelo: erro de cada abordagem, desempenho e estratégia
  escolhida em cada fold e métricas anuais.
- A contribuição das variáveis ambientais, por SHAP e por
  PredictionValuesChange.

Na barra lateral, escolha os folds de teste, do fold 1 (jan–fev/2018) ao fold 30
(nov–dez/2022). Para ver um único fold, coloque as duas pontas do seletor no
mesmo número.

## Executar localmente

A partir da raiz do repositório:

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

O painel abre em http://localhost:8501.

A exploração das variáveis ambientais e a marcação das ondas de COVID-19 usam a
planilha `data/sp_hosp_ar_meteo_2017_2022.xlsx`. Sem ela, essas duas partes ficam
ocultas e o restante do painel funciona normalmente.

## Publicar no Streamlit Community Cloud

1. Entre em https://share.streamlit.io com a conta do GitHub.
2. Crie um app a partir deste repositório, com a branch `main` e o arquivo
   principal `dashboard/app.py`.
3. Escolha o endereço do app, por exemplo `internacoes-respiratorias-sp`, e
   confirme o deploy.

O Community Cloud instala as dependências de `dashboard/requirements.txt` e
atualiza o painel a cada novo commit na branch escolhida.

## Como ler os resultados

- A coluna `baseline_improved` é a previsão da base linear ElasticNet do próprio
  modelo (`base_pred_d` em `src/pipeline_walkforward.py`). O "ganho sobre a base
  linear" mede, portanto, o valor agregado pela camada CatBoost com as variáveis
  ambientais: 2,3% de RMSE em 2018–2022, com o modelo final melhor que a base em
  20 dos 30 folds.
- O esperado é uma previsão de 1 dia à frente. Depois de prever cada dia, o
  pipeline acrescenta o valor observado ao histórico, então cada previsão usa as
  internações observadas até a véspera. Por isso os sinais destacam saltos
  bruscos, e um patamar alto que se mantém tende a ser incorporado à previsão em
  poucos dias.
- Os sinais cobrem 2018 a 2022 e servem para avaliar o método, não como alerta
  em tempo real.

## Como o sinal é calculado

Um dia gera sinal quando o observado supera o esperado mais um quantil (80%,
90%, 95% ou 99%) dos erros do modelo nos 365 dias anteriores. O limiar usa apenas
dias passados, sem depender de informação futura. No quantil 95%, cerca de 6% dos
dias geram sinal. Dias com sinal próximos entre si são agrupados em episódios.

Um sinal indica um dia para investigar. Não é diagnóstico, surto confirmado nem
prova de causalidade climática.
