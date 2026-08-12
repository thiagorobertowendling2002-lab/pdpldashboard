import numpy as np
import pandas as pd
import plotly.graph_objects as go
from branding import COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT

FONT = "Poppins, sans-serif"
GRID_COLOR = "rgba(0,0,0,0.06)"


def _base_layout(fig: go.Figure, height: int, legend_below: bool = False) -> go.Figure:
    """Layout comum a todos os gráficos. O título NÃO é desenhado dentro do Plotly
    (o SVG corta texto longo sem quebrar linha) — quem chama renderiza o título como
    markdown normal do Streamlit logo acima do gráfico, que quebra linha livremente."""
    legend = dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0) if legend_below else dict(orientation="h")
    fig.update_layout(
        height=height,
        margin=dict(t=16, b=48 if legend_below else 8, l=8, r=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=COLOR_TEXT, size=12),
        legend=legend,
    )
    return fig


def teal_ramp(n: int) -> list[str]:
    """Rampa sequencial de um único matiz (teal), clara -> escura."""
    stops = [(0xCF, 0xEA, 0xF0), (0x1C, 0x9C, 0xB4), (0x0B, 0x4A, 0x58)]
    if n <= 1:
        return [COLOR_PRIMARY]
    colors = []
    for i in range(n):
        t = i / (n - 1)
        seg = t * (len(stops) - 1)
        idx = min(int(seg), len(stops) - 2)
        local_t = seg - idx
        c0, c1 = stops[idx], stops[idx + 1]
        rgb = tuple(round(c0[k] + (c1[k] - c0[k]) * local_t) for k in range(3))
        colors.append("#%02X%02X%02X" % rgb)
    return colors


def _truncate(label: str, max_len: int = 18) -> str:
    return label if len(label) <= max_len else label[: max_len - 1].rstrip() + "…"


def donut(counts: pd.Series, height: int = 320) -> go.Figure:
    palette = [COLOR_PRIMARY, COLOR_SECONDARY, "#F2A65A", "#7B6FD1", "#D1667B"]
    colors = (palette * (len(counts) // len(palette) + 1))[: len(counts)]
    full_labels = counts.index.astype(str).tolist()
    total = counts.values.sum()
    text = [f"{_truncate(lbl)}<br>{v / total:.1%}" for lbl, v in zip(full_labels, counts.values)]
    fig = go.Figure(
        go.Pie(
            labels=full_labels,
            values=counts.values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="white", width=2)),
            text=text,
            textinfo="text",
            textposition="outside",
            textfont=dict(size=11),
            customdata=full_labels,
            hovertemplate="%{customdata}<br>%{value} produtores (%{percent})<extra></extra>",
            showlegend=False,
        )
    )
    fig = _base_layout(fig, height)
    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=80, r=80))
    return fig


def ranked_bar(counts: pd.Series, unit: str = "produtores", height: int | None = None) -> go.Figure:
    counts = counts.sort_values(ascending=True)
    height = height or max(220, 42 * len(counts))
    fig = go.Figure(
        go.Bar(
            x=counts.values,
            y=[str(i) for i in counts.index],
            orientation="h",
            marker=dict(color=COLOR_PRIMARY),
            text=[str(v) for v in counts.values],
            textposition="outside",
            hovertemplate=f"%{{y}}<br>%{{x}} {unit}<extra></extra>",
        )
    )
    fig.update_layout(xaxis=dict(showgrid=True, gridcolor=GRID_COLOR), yaxis=dict(showgrid=False))
    return _base_layout(fig, height)


def histogram(series: pd.Series, unit: str = "", height: int = 260) -> go.Figure:
    fig = go.Figure(
        go.Histogram(
            x=series.dropna(),
            marker=dict(color=COLOR_PRIMARY, line=dict(color="white", width=1)),
            hovertemplate=f"%{{x}} {unit}<br>%{{y}} produtores<extra></extra>",
        )
    )
    fig.update_layout(
        bargap=0.08,
        xaxis=dict(title=unit, showgrid=False),
        yaxis=dict(title="Produtores", showgrid=True, gridcolor=GRID_COLOR),
    )
    return _base_layout(fig, height)


def box_by_category(df: pd.DataFrame, cat_col: str, num_col: str, unit: str = "", height: int = 340) -> go.Figure:
    fig = go.Figure()
    cats = df[cat_col].dropna().unique()
    for i, cat in enumerate(sorted(cats, key=str)):
        vals = df.loc[df[cat_col] == cat, num_col].dropna()
        fig.add_trace(
            go.Box(
                y=vals,
                name=str(cat),
                marker=dict(color=COLOR_PRIMARY if i % 2 == 0 else COLOR_SECONDARY),
                boxmean=True,
            )
        )
    fig.update_layout(
        showlegend=False,
        yaxis=dict(title=unit, showgrid=True, gridcolor=GRID_COLOR),
        xaxis=dict(showgrid=False),
    )
    return _base_layout(fig, height)


def scatter(df: pd.DataFrame, x_col: str, y_col: str, x_label: str = "", y_label: str = "", height: int = 400) -> go.Figure:
    x = df[x_col]
    y = df[y_col]
    fig = go.Figure(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(color=COLOR_PRIMARY, size=10, opacity=0.75, line=dict(color="white", width=1)),
            hovertemplate=f"{x_label or x_col}: %{{x}}<br>{y_label or y_col}: %{{y}}<extra></extra>",
        )
    )
    valid = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(valid) >= 3 and valid["x"].nunique() > 1:
        coeffs = np.polyfit(valid["x"], valid["y"], 1)
        xs = np.linspace(valid["x"].min(), valid["x"].max(), 50)
        ys = coeffs[0] * xs + coeffs[1]
        fig.add_trace(
            go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=COLOR_SECONDARY, width=2, dash="dash"), name="Tendência")
        )
    fig.update_layout(
        xaxis=dict(title=x_label or x_col, showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(title=y_label or y_col, showgrid=True, gridcolor=GRID_COLOR),
        showlegend=False,
    )
    return _base_layout(fig, height)


def grouped_bar_crosstab(df: pd.DataFrame, cat_a: str, cat_b: str, height: int = 400) -> go.Figure:
    ct = pd.crosstab(df[cat_a], df[cat_b])
    fig = go.Figure()
    colors = teal_ramp(len(ct.columns)) if len(ct.columns) > 2 else [COLOR_PRIMARY, COLOR_SECONDARY]
    for i, col in enumerate(ct.columns):
        fig.add_trace(go.Bar(x=[str(v) for v in ct.index], y=ct[col].values, name=str(col), marker=dict(color=colors[i % len(colors)])))
    fig.update_layout(
        barmode="group",
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Produtores", showgrid=True, gridcolor=GRID_COLOR),
    )
    return _base_layout(fig, height, legend_below=True)


def composition_bar(items: list[tuple[str, float]], is_percent: bool = True, height: int = 320) -> go.Figure:
    """Barra horizontal única mostrando a composição média de um grupo (soma ~100%)."""
    labels = [lbl for lbl, _ in items]
    values = [val for _, val in items]
    colors = teal_ramp(len(items))
    order = sorted(range(len(items)), key=lambda i: -values[i])
    labels = [labels[i] for i in order]
    values = [values[i] for i in order]
    colors = [colors[i] for i in order]
    unit = "%" if is_percent else ""
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=colors),
            text=[f"{v:.1f}{unit}" for v in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, title=unit),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    return _base_layout(fig, max(height, 42 * len(items)))


def correlation_heatmap(corr: pd.DataFrame, height: int = 600) -> go.Figure:
    short_labels = [_truncate(str(c)) for c in corr.columns]
    fig = go.Figure(
        go.Heatmap(
            z=corr.values,
            x=short_labels,
            y=short_labels,
            customdata=[[f"{a} × {b}" for a in corr.columns] for b in corr.columns],
            colorscale=[[0, "#D1667B"], [0.5, "#F5F8F9"], [1, COLOR_PRIMARY]],
            zmid=0,
            zmin=-1,
            zmax=1,
            colorbar=dict(title="r"),
            hovertemplate="%{customdata}<br>r = %{z:.2f}<extra></extra>",
        )
    )
    fig = _base_layout(fig, height)
    fig.update_layout(
        xaxis=dict(tickangle=-90, automargin=True),
        yaxis=dict(autorange="reversed", automargin=True),
        margin=dict(t=16, b=160, l=200, r=16),
    )
    return fig


def parallel_categories(df: pd.DataFrame, dim_cols: list[str], dim_labels: list[str], height: int = 520) -> go.Figure:
    """Diagrama de categorias paralelas: mostra como até ~5 variáveis (categóricas,
    de múltipla escolha ou numéricas já divididas em faixas) se relacionam entre si
    através de faixas que fluem de uma variável pra outra."""
    dimensions = [dict(values=df[col].astype(str), label=label) for col, label in zip(dim_cols, dim_labels)]
    codes, _ = pd.factorize(df[dim_cols[0]].astype(str))
    n_colors = max(codes.max() + 1, 1) if len(codes) else 1
    ramp = teal_ramp(n_colors)
    colorscale = [[i / max(n_colors - 1, 1), ramp[i]] for i in range(n_colors)]
    fig = go.Figure(
        go.Parcats(
            dimensions=dimensions,
            line=dict(color=codes, colorscale=colorscale, shape="hspline"),
            hoveron="category",
            hoverinfo="count+probability",
            labelfont=dict(size=12, family=FONT, color=COLOR_TEXT),
            tickfont=dict(size=11, family=FONT, color=COLOR_TEXT),
            arrangement="freeform",
        )
    )
    fig.update_layout(
        height=height,
        margin=dict(t=70, b=24, l=120, r=120),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=COLOR_TEXT, size=12),
    )
    return fig
