import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Internações respiratórias | Monitor",
    page_icon=":material/monitor_heart:",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
CONFIG_PATH = ROOT / "config" / "model_config.json"
DATA_DIR = ROOT / "data"
RESULT_FILES = ("walkforward_predictions_concat.csv", "walkforward_results_by_year.csv", "walkforward_results_by_fold.csv")
WAVE_COLUMNS = ("AUX_INTENSIDADE_ONDA_COVID", "WAVE_INTENSITY")
OUTCOME_LABEL = "Respiratórias (CID-10 cap. X)"
MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
ENV_LABELS = {
    "TEMPMED": "Temperatura média",
    "PM2_5": "PM2,5",
    "PM10": "PM10",
    "O3": "Ozônio (O3)",
    "NO2": "Dióxido de nitrogênio (NO2)",
    "SO2": "Dióxido de enxofre (SO2)",
    "CO": "Monóxido de carbono (CO)",
    "PRECIPIT": "Precipitação",
    "UMIDRELAT": "Umidade relativa",
    "RADIACAO": "Radiação",
    "VELVENTO": "Velocidade do vento",
    "PRESSAOATM": "Pressão atmosférica",
}
STRATEGY_LABELS = {
    "blend": "Combinação residual + direto",
    "direct_only": "CatBoost direto",
    "residual_only": "Base + correção CatBoost",
    "base_only": "Base linear ElasticNet",
}
# baseline_improved é a previsão da base linear (base_pred_d em src/pipeline_walkforward.py).
APPROACH_LABELS = {
    "expected": "Modelo final",
    "y_pred_residual_model": "Base + correção CatBoost",
    "y_pred_direct_model": "CatBoost direto",
    "baseline_improved": "Base linear ElasticNet",
    "baseline_weekly": "Baseline semanal, y(t−7)",
    "baseline_seasonal": "Baseline sazonal, y(t−364/365)",
}
COLORS = {
    "observed": "#173f5f",
    "expected": "#e07a5f",
    "band": "rgba(15, 118, 110, 0.14)",
    "alert": "#b42318",
    "wave": "rgba(217, 119, 6, 0.10)",
    "accent": "#0f766e",
    "muted": "#94a3b8",
}
THRESHOLD_WINDOW = 365
THRESHOLD_MIN_DAYS = 30


def fmt(value: float, decimals: int = 0) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: float, decimals: int = 1) -> str:
    percent = round(value * 100, decimals) + 0.0
    return f"{percent:+.{decimals}f}%".replace(".", ",") if percent else f"{0:.{decimals}f}%".replace(".", ",")


def fold_period(start: pd.Timestamp, end: pd.Timestamp) -> str:
    if start.year == end.year:
        return f"{MONTHS[start.month - 1]}–{MONTHS[end.month - 1]}/{end.year}"
    return f"{MONTHS[start.month - 1]}/{start.year}–{MONTHS[end.month - 1]}/{end.year}"


def finish(figure: go.Figure, height: int, **layout) -> go.Figure:
    settings = {
        "height": height,
        "margin": {"l": 10, "r": 10, "t": 10, "b": 10},
        "separators": ",.",
        "legend": {"orientation": "h", "y": 1.12, "x": 0, "title": None},
    }
    settings.update(layout)
    figure.update_layout(**settings)
    return figure


@st.cache_data
def load_results() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    predictions = pd.read_csv(RESULTS_DIR / RESULT_FILES[0], parse_dates=["date"])
    annual = pd.read_csv(RESULTS_DIR / RESULT_FILES[1])
    folds = pd.read_csv(RESULTS_DIR / RESULT_FILES[2], parse_dates=["train_end", "test_start", "test_end"])
    folds["period"] = [fold_period(start, end) for start, end in zip(folds["test_start"], folds["test_end"])]
    series = predictions.rename(columns={"y_true": "observed", "y_pred": "expected"})
    alternatives = [column for column in APPROACH_LABELS if column != "expected" and column in series.columns]
    series = series[["date", "fold", "observed", "expected", "selected_strategy", *alternatives]]
    return series.sort_values("date").reset_index(drop=True), annual, folds


@st.cache_data
def load_run_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}


@st.cache_data
def load_environment() -> pd.DataFrame:
    workbooks = sorted(path for path in DATA_DIR.glob("*.xlsx") if not path.name.startswith("~$"))
    if len(workbooks) != 1:
        return pd.DataFrame(columns=["date"])
    data = pd.read_excel(workbooks[0], sheet_name=0)
    data.columns = [str(column).strip() for column in data.columns]
    if "Data" not in data.columns:
        return pd.DataFrame(columns=["date"])
    wave_column = next((column for column in WAVE_COLUMNS if column in data.columns), None)
    if wave_column:
        data["wave_intensity"] = data[wave_column]
    data["date"] = pd.to_datetime(data["Data"], errors="coerce").dt.normalize()
    columns = [column for column in [*ENV_LABELS, "wave_intensity"] if column in data.columns]
    data[columns] = data[columns].apply(pd.to_numeric, errors="coerce")
    return data.dropna(subset=["date"])[["date", *columns]].sort_values("date").reset_index(drop=True)


def read_importance(filename: str, value_column: str) -> pd.Series:
    path = RESULTS_DIR / filename
    if not path.exists():
        return pd.Series(dtype=float)
    data = pd.read_csv(path)
    name_column = next((column for column in ("Variavel", "variavel", "feature", "variable") if column in data.columns), None)
    if name_column is None or value_column not in data.columns:
        return pd.Series(dtype=float)
    return data.set_index(name_column)[value_column]


@st.cache_data
def load_importance() -> pd.DataFrame:
    importance = pd.concat(
        {
            "shap": read_importance("fig30_shap_mean_abs_only_raw_env.csv", "mean_abs_shap"),
            "pvc": read_importance("fig29_env_feature_importance_only_raw.csv", "Importancia"),
        },
        axis=1,
    )
    importance.index.name = "variable"
    return importance.reset_index()


def add_thresholds(series: pd.DataFrame, level: float) -> pd.DataFrame:
    """Limiar empírico: quantil dos erros dos dias anteriores, sem usar informação futura."""
    data = series.copy()
    data["gap"] = data["observed"] - data["expected"]
    past_gaps = data["gap"].shift(1).rolling(THRESHOLD_WINDOW, min_periods=THRESHOLD_MIN_DAYS)
    data["upper"] = data["expected"] + past_gaps.quantile(level)
    data["lower"] = (data["expected"] + past_gaps.quantile(1 - level)).clip(lower=0)
    data["gap_pct"] = data["gap"] / data["expected"].where(data["expected"] > 0) * 100
    data["excess"] = (data["observed"] - data["upper"]).clip(lower=0)
    data["signal"] = data["observed"] > data["upper"]
    data["below"] = data["observed"] < data["lower"]
    return data


def find_episodes(data: pd.DataFrame, max_gap_days: int) -> pd.DataFrame:
    alerts = data[data["signal"]].sort_values("date")
    if alerts.empty:
        return pd.DataFrame(columns=["Início", "Fim", "Dias com sinal", "Excesso acumulado", "Pico observado", "Maior excesso diário"])
    new_episode = alerts["date"].diff().dt.days.fillna(max_gap_days + 2) > max_gap_days + 1
    alerts = alerts.assign(episode=new_episode.cumsum())
    episodes = alerts.groupby("episode").agg(
        start=("date", "min"),
        end=("date", "max"),
        days=("date", "size"),
        excess=("excess", "sum"),
        peak=("observed", "max"),
        max_excess=("excess", "max"),
    )
    episodes = episodes.sort_values(["days", "excess"], ascending=False)
    return episodes.rename(
        columns={"start": "Início", "end": "Fim", "days": "Dias com sinal", "excess": "Excesso acumulado", "peak": "Pico observado", "max_excess": "Maior excesso diário"}
    ).reset_index(drop=True)


def wave_spans(environment: pd.DataFrame) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    if "wave_intensity" not in environment.columns:
        return []
    in_wave = environment.set_index("date")["wave_intensity"].fillna(0) > 0
    run_id = (in_wave != in_wave.shift()).cumsum()
    spans = []
    for _, run in in_wave.groupby(run_id):
        if run.iloc[0]:
            spans.append((run.index.min(), run.index.max()))
    return spans


def timeline_chart(
    data: pd.DataFrame, waves: list[tuple[pd.Timestamp, pd.Timestamp]], boundaries: list[pd.Timestamp], level: float
) -> go.Figure:
    figure = go.Figure()
    start, end = data["date"].min(), data["date"].max()
    for wave_start, wave_end in waves:
        if wave_end >= start and wave_start <= end:
            figure.add_vrect(x0=max(wave_start, start), x1=min(wave_end, end), fillcolor=COLORS["wave"], line_width=0, layer="below")
    for boundary in boundaries:
        figure.add_vline(x=boundary, line_width=1, line_dash="dot", line_color="rgba(100, 116, 139, 0.5)")
    figure.add_trace(go.Scatter(x=data["date"], y=data["upper"], mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
    figure.add_trace(
        go.Scatter(
            x=data["date"], y=data["lower"], mode="lines", line={"width": 0}, fill="tonexty", fillcolor=COLORS["band"],
            name=f"Faixa esperada ({level:.0%})", hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data["date"], y=data["observed"], mode="lines", name="Observado", line={"color": COLORS["observed"], "width": 1.4},
            customdata=data["fold"], hovertemplate="Fold %{customdata} · observado: %{y:.0f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data["date"], y=data["expected"], mode="lines", name="Esperado", line={"color": COLORS["expected"], "width": 2, "dash": "dot"},
            hovertemplate="Esperado: %{y:.1f}<extra></extra>",
        )
    )
    alerts = data[data["signal"]]
    figure.add_trace(
        go.Scatter(
            x=alerts["date"], y=alerts["observed"], mode="markers", name="Sinal acima do limiar", marker={"color": COLORS["alert"], "size": 7},
            customdata=alerts["excess"], hovertemplate="Sinal · excesso sobre o limiar: %{customdata:.1f}<extra></extra>",
        )
    )
    if waves:
        figure.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker={"size": 12, "symbol": "square", "color": "rgba(217, 119, 6, 0.35)"}, name="Ondas de COVID-19"))
    finish(figure, 480, xaxis_title=None, yaxis_title="Internações por dia", hovermode="x unified", legend={"orientation": "h", "y": 1.1, "x": 0}, margin={"l": 10, "r": 10, "t": 30, "b": 10})
    figure.update_xaxes(hoverformat="%d/%m/%Y")
    return figure


def signal_heatmap(data: pd.DataFrame) -> go.Figure:
    table = data.assign(ano=data["date"].dt.year, mes=data["date"].dt.month).pivot_table(index="ano", columns="mes", values="signal", aggfunc="sum", fill_value=0)
    table = table.reindex(columns=range(1, 13), fill_value=0)
    figure = px.imshow(table.values, x=MONTHS, y=[str(year) for year in table.index], color_continuous_scale="Reds", text_auto=True, aspect="auto", labels={"color": "Dias"})
    return finish(figure, 80 + 45 * len(table), coloraxis_showscale=False)


def horizontal_bars(data: pd.DataFrame, x: str, y: str, x_title: str, decimals: int, colors: list[str] | None = None) -> go.Figure:
    figure = go.Figure(
        go.Bar(
            x=data[x], y=data[y], orientation="h", marker_color=colors or COLORS["accent"],
            text=data[x], texttemplate=f"%{{x:.{decimals}f}}", textposition="outside", cliponaxis=False,
            hovertemplate=f"%{{y}}: %{{x:.{decimals}f}}<extra></extra>",
        )
    )
    return finish(figure, 60 + 32 * len(data), xaxis_title=x_title, yaxis_title=None, showlegend=False)


def lag_correlations(environment: pd.DataFrame, data: pd.DataFrame, variable: str, max_lag: int) -> pd.DataFrame:
    env = environment.set_index("date")[variable].sort_index()
    target = data.set_index("date")[["observed", "gap"]]
    rows = []
    for lag in range(max_lag + 1):
        joined = target.join(env.shift(lag, freq="D").rename("env"), how="inner").dropna()
        rows.append({
            "Defasagem (dias)": lag,
            "Internações observadas": joined["env"].corr(joined["observed"], method="spearman"),
            "Excesso sobre o esperado": joined["env"].corr(joined["gap"], method="spearman"),
        })
    return pd.DataFrame(rows)


def period_metrics(data: pd.DataFrame) -> dict[str, float]:
    errors = data["observed"] - data["expected"]
    metrics = {"MAE": errors.abs().mean(), "RMSE": float(np.sqrt((errors**2).mean()))}
    if "baseline_improved" in data.columns:
        base_rmse = float(np.sqrt(((data["observed"] - data["baseline_improved"]) ** 2).mean()))
        metrics["gain_over_base"] = 1 - metrics["RMSE"] / base_rmse if base_rmse else float("nan")
    return metrics


def approach_errors(data: pd.DataFrame) -> pd.DataFrame:
    columns = [column for column in APPROACH_LABELS if column in data.columns]
    rows = data.dropna(subset=["observed", *columns])
    errors = rows[columns].sub(rows["observed"], axis=0)
    result = pd.DataFrame({
        "Abordagem": [APPROACH_LABELS[column] for column in columns],
        "RMSE": np.sqrt((errors**2).mean()).to_numpy(),
    })
    return result.sort_values("RMSE", ascending=False)


if not all((RESULTS_DIR / name).exists() for name in RESULT_FILES):
    st.error("Resultados do modelo não encontrados em `results/`. O painel precisa dos arquivos gerados por `src/pipeline_walkforward.py`.")
    st.stop()

series, annual, folds = load_results()
environment = load_environment()
fold_names = {int(row.fold): f"{int(row.fold)} · {row.period}" for row in folds.itertuples()}
fold_ids = list(fold_names)

with st.sidebar:
    st.header("Filtros")
    first_fold, last_fold = st.select_slider(
        "Folds de teste",
        options=fold_ids,
        value=(fold_ids[0], fold_ids[-1]),
        format_func=fold_names.get,
        help="Blocos bimestrais da validação walk-forward. Para ver um único fold, coloque as duas pontas no mesmo número.",
    )
    level = st.select_slider(
        "Sensibilidade do sinal",
        options=[0.80, 0.90, 0.95, 0.99],
        value=0.95,
        format_func=lambda value: f"Quantil {value:.0%}",
        help=f"Um dia gera sinal quando o observado supera o esperado mais o quantil escolhido dos erros dos {THRESHOLD_WINDOW} dias anteriores. Quantis mais altos geram menos sinais.",
    )
    merge_gap = st.number_input("Unir sinais separados por até (dias)", min_value=0, max_value=7, value=2, help="Dias com sinal separados por no máximo este intervalo formam um mesmo episódio.")
    st.divider()
    st.caption("Séries históricas de 2018 a 2022 para validação do método; não substituem monitoramento em tempo real.")

scored = add_thresholds(series, level)
selected = scored[scored["fold"].between(first_fold, last_fold)]
fold_view = folds[folds["fold"].between(first_fold, last_fold)]
alerts = selected[selected["signal"]]
episodes = find_episodes(selected, int(merge_gap))
metrics = period_metrics(selected)

st.caption("Vigilância epidemiológica · SUS · São Paulo")
st.title("Monitor de internações respiratórias")
fold_text = f"fold {first_fold}" if first_fold == last_fold else f"folds {first_fold} a {last_fold}"
st.markdown(
    f"**{OUTCOME_LABEL}** · modelo híbrido ElasticNet + CatBoost · {fold_text}, "
    f"{selected['date'].min():%d/%m/%Y} a {selected['date'].max():%d/%m/%Y} ({fmt(len(selected))} dias)"
)

with st.container(horizontal=True):
    st.metric("Internações observadas", fmt(selected["observed"].sum()), border=True)
    st.metric(
        "Observado vs esperado",
        pct(selected["observed"].sum() / selected["expected"].sum() - 1),
        help="Diferença percentual entre o total observado e o total esperado nos folds selecionados.",
        border=True,
    )
    st.metric(
        "Dias com sinal",
        fmt(len(alerts)),
        f"{len(alerts) / len(selected):.1%} dos dias".replace(".", ","),
        delta_color="off",
        delta_arrow="off",
        border=True,
    )
    st.metric("Episódios", fmt(len(episodes)), help="Sequências de dias com sinal, unindo intervalos curtos conforme o filtro lateral.", border=True)
    st.metric("Erro médio (MAE)", fmt(metrics["MAE"], 1), help="Erro absoluto médio da previsão de 1 dia à frente, em internações por dia.", border=True)

st.info(
    f"Sinal = observado acima do esperado mais o quantil {level:.0%} dos erros recentes do modelo. "
    "O esperado é a previsão para 1 dia à frente feita com as internações observadas até a véspera. Por isso os sinais destacam saltos bruscos, "
    "e um patamar alto que se mantém tende a ser incorporado à previsão em poucos dias. "
    "Um sinal serve para priorizar investigação: não é diagnóstico, surto confirmado nem prova de causalidade climática.",
    icon=":material/info:",
)

overview_tab, signals_tab, quality_tab, environment_tab, about_tab = st.tabs(
    [
        ":material/timeline: Visão geral",
        ":material/notifications: Sinais",
        ":material/fact_check: Qualidade do modelo",
        ":material/air: Ambiente",
        ":material/menu_book: Sobre o modelo",
    ]
)

with overview_tab:
    with st.container(border=True):
        st.subheader("Observado, esperado e faixa de variação")
        waves = wave_spans(environment)
        boundaries = fold_view["test_start"].iloc[1:].tolist()
        st.plotly_chart(timeline_chart(selected, waves, boundaries, level), width="stretch")
        notes = [
            f"A faixa usa os quantis {1 - level:.0%} e {level:.0%} dos erros dos {THRESHOLD_WINDOW} dias anteriores; os primeiros {THRESHOLD_MIN_DAYS} dias do fold 1 ficam sem faixa.",
            "Linhas pontilhadas separam os folds." if boundaries else "",
            "Áreas em laranja marcam ondas de COVID-19." if waves else "",
        ]
        st.caption(" ".join(note for note in notes if note))
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("Média mensal")
        monthly = selected.set_index("date")[["observed", "expected"]].resample("MS").mean().reset_index()
        monthly = monthly.melt("date", var_name="Série", value_name="Internações/dia")
        monthly["Série"] = monthly["Série"].map({"observed": "Observado", "expected": "Esperado"})
        figure = px.line(monthly, x="date", y="Internações/dia", color="Série", markers=len(monthly) <= 24, color_discrete_map={"Observado": COLORS["observed"], "Esperado": COLORS["expected"]})
        st.plotly_chart(finish(figure, 340, xaxis_title=None), width="stretch")
    with right, st.container(border=True):
        st.subheader("Média por dia da semana")
        weekday = selected.assign(dia=selected["date"].dt.dayofweek).groupby("dia")[["observed", "expected"]].mean().reset_index()
        weekday["dia"] = weekday["dia"].map(dict(enumerate(["seg", "ter", "qua", "qui", "sex", "sáb", "dom"])))
        weekday = weekday.melt("dia", var_name="Série", value_name="Internações/dia")
        weekday["Série"] = weekday["Série"].map({"observed": "Observado", "expected": "Esperado"})
        figure = px.bar(weekday, x="dia", y="Internações/dia", color="Série", barmode="group", color_discrete_map={"Observado": COLORS["observed"], "Esperado": COLORS["expected"]})
        st.plotly_chart(finish(figure, 340, xaxis_title=None), width="stretch")

with signals_tab:
    with st.container(border=True):
        st.subheader("Episódios de excesso")
        st.caption("Sequências de dias com sinal, ordenadas pela duração. Episódios longos são mais relevantes para vigilância que picos isolados.")
        st.dataframe(
            episodes,
            hide_index=True,
            column_config={
                "Início": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Fim": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Excesso acumulado": st.column_config.NumberColumn(format="%.0f"),
                "Pico observado": st.column_config.NumberColumn(format="%.0f"),
                "Maior excesso diário": st.column_config.NumberColumn(format="%.1f"),
            },
        )
    left, right = st.columns([3, 2])
    with left, st.container(border=True):
        st.subheader("Dias com sinal")
        alert_view = alerts.sort_values("excess", ascending=False)[["date", "fold", "observed", "expected", "upper", "excess", "gap_pct"]]
        st.dataframe(
            alert_view.rename(columns={"date": "Data", "fold": "Fold", "observed": "Observado", "expected": "Esperado", "upper": "Limiar", "excess": "Acima do limiar", "gap_pct": "Diferença (%)"}),
            hide_index=True,
            height=420,
            column_config={
                "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Observado": st.column_config.NumberColumn(format="%.0f"),
                "Esperado": st.column_config.NumberColumn(format="%.1f"),
                "Limiar": st.column_config.NumberColumn(format="%.1f"),
                "Acima do limiar": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=float(max(alert_view["excess"].max(), 1)) if not alert_view.empty else 1.0),
                "Diferença (%)": st.column_config.NumberColumn(format="%+.1f%%"),
            },
        )
        st.download_button(
            "Baixar sinais (CSV)",
            alerts.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            "sinais_internacoes.csv",
            "text/csv",
            icon=":material/download:",
        )
    with right, st.container(border=True):
        st.subheader("Sinais por mês")
        st.caption("Número de dias com sinal em cada mês dos folds selecionados.")
        st.plotly_chart(signal_heatmap(selected), width="stretch")

with quality_tab:
    folds_better = int((fold_view["skill_vs_improved_RMSE"] > 0).sum())
    with st.container(horizontal=True):
        st.metric("RMSE", fmt(metrics["RMSE"], 1), help="Raiz do erro quadrático médio nos folds selecionados, em internações por dia.", border=True)
        st.metric("MAE", fmt(metrics["MAE"], 1), help="Erro absoluto médio nos folds selecionados, em internações por dia.", border=True)
        st.metric(
            "Ganho sobre a base linear",
            pct(metrics["gain_over_base"]),
            help="Redução do RMSE do modelo final em relação à base linear ElasticNet sozinha (coluna baseline_improved). Mede o valor agregado pela camada CatBoost, que inclui as variáveis ambientais.",
            border=True,
        )
        st.metric(
            "Folds em que supera a base",
            f"{folds_better} de {len(fold_view)}",
            help="Folds em que o RMSE do modelo final ficou abaixo do RMSE da base linear.",
            border=True,
        )
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("Erro por abordagem")
        errors = approach_errors(selected)
        bar_colors = [COLORS["observed"] if name == APPROACH_LABELS["expected"] else COLORS["muted"] for name in errors["Abordagem"]]
        st.plotly_chart(horizontal_bars(errors, "RMSE", "Abordagem", "RMSE (internações/dia)", 1, bar_colors), width="stretch")
        if {"y_pred_residual_model", "baseline_improved"} <= set(selected.columns):
            correction = (selected["y_pred_residual_model"] - selected["baseline_improved"]).abs().mean()
            st.caption(
                "A base linear usa só o histórico de internações e o calendário. A correção do CatBoost, que inclui as variáveis ambientais, "
                f"altera a previsão da base em {fmt(correction, 1)} internações/dia em média nos folds selecionados."
            )
    with right, st.container(border=True):
        st.subheader("Observado × previsto")
        figure = px.scatter(selected, x="expected", y="observed", opacity=0.35, labels={"expected": "Previsto", "observed": "Observado"}, color_discrete_sequence=[COLORS["observed"]])
        top = float(max(selected["expected"].max(), selected["observed"].max()))
        figure.add_trace(go.Scatter(x=[0, top], y=[0, top], mode="lines", line={"color": COLORS["expected"], "dash": "dash"}, name="Previsão perfeita"))
        st.plotly_chart(finish(figure, 360, showlegend=False), width="stretch")
    with st.container(border=True):
        st.subheader("Desempenho por fold")
        fold_plot = fold_view.melt(id_vars=["fold", "period"], value_vars=["RMSE", "baseline_improved_RMSE", "baseline_weekly_RMSE"], var_name="Modelo", value_name="Erro (RMSE)")
        fold_plot["Modelo"] = fold_plot["Modelo"].map({"RMSE": "Modelo final", "baseline_improved_RMSE": "Base linear ElasticNet", "baseline_weekly_RMSE": "Baseline semanal"})
        figure = px.line(
            fold_plot, x="fold", y="Erro (RMSE)", color="Modelo", markers=True, hover_data={"period": True},
            labels={"fold": "Fold", "period": "Período"},
            color_discrete_map={"Modelo final": COLORS["observed"], "Base linear ElasticNet": COLORS["expected"], "Baseline semanal": "#cbd5e1"},
        )
        figure.update_xaxes(dtick=1)
        st.plotly_chart(finish(figure, 340), width="stretch")
        fold_table = fold_view.assign(
            estrategia=fold_view["selected_strategy"].map(STRATEGY_LABELS).fillna(fold_view["selected_strategy"]),
            peso=fold_view["blend_w_residual"].where(fold_view["selected_strategy"] == "blend"),
        )
        st.dataframe(
            fold_table[["fold", "period", "estrategia", "peso", "MAE", "RMSE", "skill_vs_improved_RMSE"]].rename(
                columns={"fold": "Fold", "period": "Período", "estrategia": "Estratégia escolhida", "peso": "Peso do residual", "skill_vs_improved_RMSE": "Ganho sobre a base linear"}
            ),
            hide_index=True,
            column_config={
                "Peso do residual": st.column_config.NumberColumn(format="%.2f", help="Só vale para a combinação: previsão = peso × (base + correção) + (1 − peso) × CatBoost direto."),
                "MAE": st.column_config.NumberColumn(format="%.1f"),
                "RMSE": st.column_config.NumberColumn(format="%.1f"),
                "Ganho sobre a base linear": st.column_config.NumberColumn(format="percent"),
            },
        )
        st.caption("Em cada fold, quatro estratégias competem numa validação interna no fim do treino. A base linear só é trocada quando a melhora de RMSE passa de 0,5%.")
        st.download_button(
            "Baixar métricas dos folds selecionados (CSV)",
            fold_view.drop(columns="period").to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            "metricas_walkforward_por_fold.csv",
            "text/csv",
            icon=":material/download:",
        )
    with st.container(border=True):
        st.subheader("Métricas anuais")
        st.caption("Anos que contêm os folds selecionados, com as métricas do ano inteiro.")
        annual_view = annual[annual["year"].between(selected["date"].dt.year.min(), selected["date"].dt.year.max())]
        st.dataframe(
            annual_view[["year", "MAE", "RMSE", "R2", "MAPE_%", "skill_vs_improved_RMSE", "skill_vs_weekly_RMSE", "skill_vs_seasonal_RMSE", "n_days"]].rename(
                columns={
                    "year": "Ano", "R2": "R²", "MAPE_%": "MAPE (%)", "skill_vs_improved_RMSE": "Ganho sobre a base linear",
                    "skill_vs_weekly_RMSE": "Ganho sobre o semanal", "skill_vs_seasonal_RMSE": "Ganho sobre o sazonal", "n_days": "Dias",
                }
            ),
            hide_index=True,
            column_config={
                "Ano": st.column_config.NumberColumn(format="%d"),
                "MAE": st.column_config.NumberColumn(format="%.1f"),
                "RMSE": st.column_config.NumberColumn(format="%.1f"),
                "R²": st.column_config.NumberColumn(format="%.3f"),
                "MAPE (%)": st.column_config.NumberColumn(format="%.1f"),
                "Ganho sobre a base linear": st.column_config.NumberColumn(format="percent"),
                "Ganho sobre o semanal": st.column_config.NumberColumn(format="percent"),
                "Ganho sobre o sazonal": st.column_config.NumberColumn(format="percent"),
            },
        )

with environment_tab:
    importance = load_importance()
    if not importance.empty:
        importance["Variável"] = importance["variable"].map(ENV_LABELS).fillna(importance["variable"])
        with st.container(border=True):
            st.subheader("Contribuição das variáveis ambientais")
            left, right = st.columns(2)
            with left:
                st.markdown("**Média de |SHAP|**, em internações/dia")
                shap = importance.dropna(subset=["shap"]).sort_values("shap")
                if not shap.empty:
                    st.plotly_chart(horizontal_bars(shap, "shap", "Variável", "Média de |SHAP|", 2), width="stretch")
            with right:
                st.markdown("**PredictionValuesChange**, em % da importância total")
                pvc = importance.dropna(subset=["pvc"]).sort_values("pvc")
                if not pvc.empty:
                    st.plotly_chart(horizontal_bars(pvc, "pvc", "Variável", "Importância (%)", 1), width="stretch")
            caption = (
                "As duas medidas vêm de um modelo CatBoost auxiliar treinado sobre os resíduos da base linear, só com as 12 variáveis brutas e sobre a série inteira, "
                "então não mudam com os folds selecionados. Indicam o quanto esse modelo usa cada variável, não efeito causal."
            )
            if not shap.empty:
                top = shap.iloc[-1]
                caption += (
                    f" A maior contribuição média ({top['Variável']}, {fmt(top['shap'], 2)} internação/dia) equivale a "
                    f"{fmt(top['shap'] / series['observed'].mean() * 100, 1)}% da média diária de internações."
                )
            st.caption(caption)
    with st.container(border=True):
        st.subheader("Exploração por variável")
        env_options = [column for column in ENV_LABELS if column in environment.columns]
        if not env_options:
            st.info(
                "Esta seção precisa da planilha de dados em `data/sp_hosp_ar_meteo_2017_2022.xlsx`, que não está no repositório no momento. "
                "Com a planilha em `data/`, a exploração das variáveis e a marcação das ondas de COVID-19 aparecem automaticamente.",
                icon=":material/dataset:",
            )
        else:
            variable = st.selectbox("Variável ambiental", env_options, format_func=ENV_LABELS.get)
            max_lag = st.slider("Defasagem máxima (dias)", min_value=0, max_value=21, value=14)
            left, right = st.columns(2)
            with left:
                lags = lag_correlations(environment, selected, variable, max_lag).melt("Defasagem (dias)", var_name="Alvo", value_name="Correlação de Spearman")
                figure = px.bar(lags, x="Defasagem (dias)", y="Correlação de Spearman", color="Alvo", barmode="group", color_discrete_map={"Internações observadas": COLORS["observed"], "Excesso sobre o esperado": COLORS["expected"]})
                st.plotly_chart(finish(figure, 360), width="stretch")
                st.caption(
                    "O excesso (observado − esperado) desconta o que o modelo já explica. As 12 variáveis e suas defasagens de até 28 dias "
                    "já entram na camada CatBoost, então correlações próximas de zero com o excesso são o esperado."
                )
            with right:
                scatter = environment[["date", variable]].merge(selected[["date", "observed", "signal"]], on="date", how="inner")
                scatter["Dia"] = np.where(scatter["signal"], "Com sinal", "Sem sinal")
                figure = px.scatter(
                    scatter, x=variable, y="observed", color="Dia", opacity=0.45, trendline="lowess", trendline_scope="overall",
                    labels={variable: ENV_LABELS[variable], "observed": "Internações observadas"},
                    color_discrete_map={"Com sinal": COLORS["alert"], "Sem sinal": COLORS["muted"]},
                )
                st.plotly_chart(finish(figure, 360), width="stretch")

with about_tab:
    st.subheader("Modelo híbrido ElasticNet + CatBoost")
    st.markdown(
        """
- **Alvo:** internações diárias por doenças do aparelho respiratório (CID-10, capítulo X; coluna `HOSPCIDX`) no município de São Paulo.
- **Dados:** SIH/SUS (internações), CETESB (poluentes atmosféricos) e INMET (meteorologia), de 2017 a 2022.
- **Base linear:** ElasticNet sobre o histórico de internações (defasagens entre 1 e 365 dias e médias móveis de 7, 14 e 28 dias), o calendário e um indicador de pandemia a partir de 01/03/2020. Nos arquivos de resultado, a previsão dessa base é a coluna `baseline_improved`.
- **Correção:** CatBoost ajusta os resíduos da base usando as 12 variáveis ambientais brutas e suas transformações (defasagens de até 28 dias, anomalias, variações e interações).
- **Validação:** walk-forward com 30 folds de teste bimestrais entre 2018 e 2022 e reajuste completo a cada fold. Em cada fold, quatro estratégias competem numa validação interna de 75 dias no fim do treino, e a base linear só é trocada quando a melhora de RMSE passa de 0,5%.
- **Horizonte:** previsão de 1 dia à frente. Depois de prever cada dia, o pipeline acrescenta o valor observado ao histórico, então cada previsão usa as internações observadas até a véspera.
- **Interpretabilidade:** SHAP e PredictionValuesChange num modelo CatBoost auxiliar treinado sobre os resíduos da base, restrito às 12 variáveis brutas.
"""
    )
    config = load_run_config()
    if config:
        with st.expander("Configuração da execução (config/model_config.json)"):
            st.dataframe(
                pd.DataFrame({
                    "Parâmetro": list(config),
                    "Valor": [", ".join(map(str, value)) if isinstance(value, list) else str(value) for value in config.values()],
                }),
                hide_index=True,
            )
    st.subheader("Como o sinal é calculado")
    st.markdown(
        f"Para cada dia, o painel olha os erros do modelo (observado − esperado) nos {THRESHOLD_WINDOW} dias anteriores, de qualquer fold. "
        f"O limiar superior é o esperado mais o quantil {level:.0%} desses erros, e o inferior usa o quantil {1 - level:.0%}. "
        f"Como só entram dias passados, o limiar não depende de informação futura. Os primeiros {THRESHOLD_MIN_DAYS} dias do fold 1 ficam sem limiar, "
        f"e dias com sinal separados por até {int(merge_gap)} dias formam um episódio."
    )
    st.divider()
    st.caption(
        "Tese de doutorado de Gabriel Fuscald Scursone · Orientação: Profa. Dra. Diana Francisca Adamatti · "
        "Programa de Pós-Graduação em Modelagem Computacional, Universidade Federal do Rio Grande (FURG)."
    )
