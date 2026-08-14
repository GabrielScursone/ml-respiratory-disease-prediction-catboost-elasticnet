# Figuras

São 33 figuras, cada uma disponível em dois formatos. A pasta `png/` traz a
versão raster em 300 dpi e a pasta `pdf/` traz a versão vetorial, indicada para
impressão e para inserção no texto da tese.

Os nomes foram mantidos exatamente como o script os gera, para que uma nova
execução de `src/pipeline_walkforward.py` reproduza o mesmo conjunto sem
renomeação manual. A numeração `fig01` a `fig33` é a do pipeline e não
corresponde à numeração das figuras dentro da tese.

O script também gera figuras suplementares de `fig34` a `fig47`, com
caracterização exploratória, recortes do período pandêmico, Q-Q plot dos
resíduos, dependências SHAP adicionais e o diagrama PRISMA da revisão
sistemática. Elas não estão neste repositório porque foram criadas depois da
execução aqui arquivada.

## Série temporal e ajuste

| Arquivo | Conteúdo |
|---|---|
| `fig01_timeseries_full` | série completa, HOSPCIDX observado e previsto |
| `fig02_timeseries_monthly_mean` | média mensal, observado e previsto |
| `fig03_timeseries_yearly_mean` | média anual, observado e previsto |
| `fig04_parity_hexbin` | paridade entre observado e previsto |
| `fig11_monthly_seasonality_observed_pred` | sazonalidade mensal, observado e previsto |

## Diagnóstico de resíduos

| Arquivo | Conteúdo |
|---|---|
| `fig05_residuals_timeseries` | resíduos ao longo do tempo |
| `fig06_residuals_hist` | distribuição dos resíduos |
| `fig07_residuals_vs_fitted` | resíduos contra valores previstos |
| `fig08_abs_error_timeseries` | erro absoluto ao longo do tempo |
| `fig09_rolling_rmse_30d` | RMSE móvel, janela de 30 dias |
| `fig10_rolling_mae_30d` | MAE móvel, janela de 30 dias |
| `fig12_residuals_boxplot_by_month` | resíduos por mês |
| `fig27_residual_autocorrelation` | autocorrelação dos resíduos |

## Desempenho por fold

| Arquivo | Conteúdo |
|---|---|
| `fig13_rmse_by_fold` | RMSE por fold |
| `fig14_mae_by_fold` | MAE por fold |
| `fig15_r2_by_fold` | R² por fold |
| `fig16_skill_improved_by_fold` | ganho sobre a baseline melhorada, por fold |
| `fig17_mape_by_fold` | MAPE por fold |
| `fig18_rmsle_by_fold` | RMSLE por fold |
| `fig19_selected_strategy_counts` | estratégia escolhida em cada fold |
| `fig20_blend_weight_by_fold` | peso do modelo residual na combinação |
| `fig28_fold_performance_heatmap` | mapa de calor do desempenho por fold |

## Desempenho por ano

| Arquivo | Conteúdo |
|---|---|
| `fig21_rmse_by_year` | RMSE por ano |
| `fig22_mae_by_year` | MAE por ano |
| `fig23_r2_by_year` | R² por ano |
| `fig24_skill_improved_by_year` | ganho sobre a baseline melhorada, por ano |
| `fig25_abs_error_boxplot_by_year` | erro absoluto por ano |
| `fig26_signed_error_boxplot_by_year` | erro com sinal por ano |

## Interpretabilidade

| Arquivo | Conteúdo |
|---|---|
| `fig29_env_feature_importance_only_raw` | importância do CatBoost residual nas 12 variáveis ambientais |
| `fig30_shap_mean_abs_only_raw_env` | SHAP médio absoluto das 12 variáveis ambientais |
| `fig31_shap_beeswarm_only_raw_env` | SHAP summary beeswarm |
| `fig32_shap_dependence_top1_only_raw_env` | dependência SHAP da variável mais importante, temperatura média nesta execução |
| `fig33_shap_dependence_top2_only_raw_env` | dependência SHAP da segunda variável mais importante, PM2,5 nesta execução |

Os valores numéricos por trás das figuras 29 e 30 estão em
`results/fig29_env_feature_importance_only_raw.csv` e
`results/fig30_shap_mean_abs_only_raw_env.csv`.
