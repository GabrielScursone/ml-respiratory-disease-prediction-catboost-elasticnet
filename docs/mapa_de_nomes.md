# Mapa de nomes

Correspondência entre a organização anterior, a pasta `GPT 4` com a subpasta
`figures_env_meteo_only`, e a estrutura deste repositório. Serve apenas para
localizar arquivos durante a transição e pode ser apagado depois.

## Arquivos renomeados

| Nome anterior | Novo caminho |
|---|---|
| `Código_em_Python` e `gpt_4_FIGURAS_CLAUDE_NOVAS.py` | `src/pipeline_walkforward.py` |
| `config_used.json` | `config/model_config.json` |
| `0_ArPol_VarMet_Hosp_Mort_2017a2022_SP_CENARIO_COVID_ONDAS_TODOS_HOSP_MORT_CLEAN.xlsx` | `data/sp_hosp_ar_meteo_2017_2022.xlsx` |

## Arquivos movidos sem mudança de nome

O nome desses arquivos é escrito pelo próprio script. Mantê-los preserva a
reprodutibilidade, pois uma nova execução gera exatamente os mesmos nomes.

| Nome anterior | Novo caminho |
|---|---|
| `run_summary.json` | `results/run_summary.json` |
| `walkforward_results_by_fold.csv` | `results/walkforward_results_by_fold.csv` |
| `walkforward_results_by_year.csv` | `results/walkforward_results_by_year.csv` |
| `walkforward_summary_mean_std.csv` | `results/walkforward_summary_mean_std.csv` |
| `walkforward_predictions_concat.csv` | `results/walkforward_predictions_concat.csv` |
| `figures_env_meteo_only/fig29_env_feature_importance_only_raw.csv` | `results/fig29_env_feature_importance_only_raw.csv` |
| `figures_env_meteo_only/fig30_shap_mean_abs_only_raw_env.csv` | `results/fig30_shap_mean_abs_only_raw_env.csv` |

## Figuras

Todas as figuras saíram de `figures_env_meteo_only/` e foram separadas por
formato, em `figures/png/` e `figures/pdf/`. Quinze arquivos PNG tinham o
prefixo `z ` com espaço, que atrapalha o uso em linha de comando e em URLs do
GitHub. O prefixo foi removido.

| Nome anterior | Novo nome |
|---|---|
| `z fig03_timeseries_yearly_mean.png` | `figures/png/fig03_timeseries_yearly_mean.png` |
| `z fig10_rolling_mae_30d.png` | `figures/png/fig10_rolling_mae_30d.png` |
| `z fig11_monthly_seasonality_observed_pred.png` | `figures/png/fig11_monthly_seasonality_observed_pred.png` |
| `z fig13_rmse_by_fold.png` | `figures/png/fig13_rmse_by_fold.png` |
| `z fig15_r2_by_fold.png` | `figures/png/fig15_r2_by_fold.png` |
| `z fig16_skill_improved_by_fold.png` | `figures/png/fig16_skill_improved_by_fold.png` |
| `z fig17_mape_by_fold.png` | `figures/png/fig17_mape_by_fold.png` |
| `z fig18_rmsle_by_fold.png` | `figures/png/fig18_rmsle_by_fold.png` |
| `z fig20_blend_weight_by_fold.png` | `figures/png/fig20_blend_weight_by_fold.png` |
| `z fig21_rmse_by_year.png` | `figures/png/fig21_rmse_by_year.png` |
| `z fig22_mae_by_year.png` | `figures/png/fig22_mae_by_year.png` |
| `z fig23_r2_by_year.png` | `figures/png/fig23_r2_by_year.png` |
| `z fig24_skill_improved_by_year.png` | `figures/png/fig24_skill_improved_by_year.png` |
| `z fig25_abs_error_boxplot_by_year.png` | `figures/png/fig25_abs_error_boxplot_by_year.png` |
| `z fig26_signed_error_boxplot_by_year.png` | `figures/png/fig26_signed_error_boxplot_by_year.png` |

## Arquivos deixados de fora

| Arquivo | Motivo |
|---|---|
| `figures_env_meteo_only/figures_generated.txt` | contém apenas caminhos locais do Windows, sem valor fora da máquina de origem |
| `Código_em_Python` | é o mesmo pipeline de `pipeline_walkforward.py` sem a função de figuras suplementares, foi omitido para não duplicar cerca de 1800 linhas |
| PDF da tese | ainda em revisão e antes da defesa, pode ser adicionado em `docs/` quando fizer sentido publicar |
