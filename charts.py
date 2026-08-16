import numpy as np
import pandas as pd
import plotly.graph_objects as go
from branding import COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT

FONT = "Poppins, sans-serif"
GRID_COLOR = "rgba(0,0,0,0.06)"

# Passar em todo st.plotly_chart(..., config=PLOTLY_CONFIG). Tira os ícones
# menos essenciais da modebar (select/lasso de área, escala automática,
# comparação de hover) — ela já colidia com rótulo de dado em alguns cantos
# em telas normais, e em tela de celular (menos espaço, alvo de toque
# grosso do dedo) esse excesso de ícones piora. Mantém zoom/pan/reset/
# download porque a matriz de correlação completa depende de zoom pra
# explorar (instrução própria da tela é "role e amplie").
# "displayModeBar": "hover" (em vez de sempre visível) resolve o resto do
# problema: em tela estreita a modebar ficava sobreposta ao rótulo da barra
# do topo o tempo todo, sem jeito de "tirar do caminho" — só aparecendo ao
# passar o mouse, ela nunca chega a competir com o dado em quem só olha (ou
# usa o dedo) sem gesto de hover disponível. Pinça/arrasto pra zoom/pan
# continuam funcionando por gesto direto no gráfico, sem depender do ícone.
PLOTLY_CONFIG = {
    "displaylogo": False,
    "displayModeBar": "hover",
    "modeBarButtonsToRemove": [
        "select2d",
        "lasso2d",
        "autoScale2d",
        "toggleSpikelines",
        "hoverCompareCartesian",
        "hoverClosestCartesian",
    ],
    "responsive": True,
}


def _with_alpha(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


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


def _wrap(label: str, width: int = 22) -> str:
    """Quebra o texto em várias linhas (sem cortar palavras) usando <br>, pra caber
    a frase inteira em vez de truncar com "..."."""
    words = label.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "<br>".join(lines)


def donut(counts: pd.Series, height: int = 320) -> go.Figure:
    palette = [COLOR_PRIMARY, COLOR_SECONDARY, "#F2A65A", "#7B6FD1", "#D1667B"]
    colors = (palette * (len(counts) // len(palette) + 1))[: len(counts)]
    full_labels = counts.index.astype(str).tolist()
    total = counts.values.sum()
    text = [f"{_wrap(lbl)}<br>{v / total:.1%}" for lbl, v in zip(full_labels, counts.values)]
    fig = go.Figure(
        go.Pie(
            labels=full_labels,
            values=counts.values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="white", width=2)),
            text=text,
            textinfo="text",
            textposition="outside",
            textfont=dict(size=10),
            customdata=full_labels,
            hovertemplate="%{customdata}<br>%{value} produtores (%{percent})<extra></extra>",
            showlegend=False,
        )
    )
    fig = _base_layout(fig, height + 40)
    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=110, r=110))
    return fig


def ranked_bar(
    counts: pd.Series, unit: str = "produtores", height: int | None = None, category_order: list[str] | None = None
) -> go.Figure:
    if category_order:
        # Ordem lógica da própria variável (ex: faixas de produção crescentes) em vez
        # de por frequência — Plotly desenha a última posição da série no topo, então
        # invertemos aqui pra "1) ..." ficar em cima e "5) ..." embaixo, lendo de cima
        # pra baixo na ordem natural.
        ordered = [c for c in category_order if c in counts.index]
        counts = counts.reindex(ordered).dropna().iloc[::-1]
    else:
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


_CORR_SHORT_LABELS = {
    "Idade (anos)": "Idade",
    "Tempo que é produtor(a) de leite (anos)": "Tempo produtor",
    "Produção de leite média dos últimos 12 meses (consumido + vendido) (litros/dia)": "Produção total",
    "Produção nas águas (litros/dia)": "Produção (águas)",
    "Produção na seca (litros/dia)": "Produção (seca)",
    "Produtividade média / vaca em lactação (litros/vaca/dia)": "Produtiv. média",
    "Produtividade nas águas (litros/vaca/dia)": "Produtiv. (águas)",
    "Produtividade na seca (litros/vaca/dia)": "Produtiv. (seca)",
    "Área própria total da propriedade (hectares)": "Área total",
    "Área destinada ao gado de leite (hectares)": "Área p/ gado",
    "Total familiar (trabalhador/dia)": "MDO familiar",
    "Total contratada (trabalhador/dia)": "MDO contratada",
    "Mdo total (trabalhador/dia)": "MDO total",
    "Número de ordenhas nas águas": "Ordenhas (águas)",
    "Número de ordenhas na seca": "Ordenhas (seca)",
    "Se sim, qual o valor médio anual do seu custo de produção? (R$/litro)": "Custo produção",
    "Nos últimos 12 meses, quantas vezes um técnico visitou sua propriedade para orientá-lo(a) sobre a produção de leite? (visitas/ano)": "Visitas técnicas",
    "Idade média que desfaz dos machos (meses)": "Idade desfaz machos",
    "Idade média de desmama dos bezerros(as) (meses)": "Idade desmame",
    "Peso médio ao desmame dos bezerros(as) (Kg)": "Peso ao desmame",
    "Idade média das novilhas ao primeiro parto (meses)": "Idade 1º parto",
    "Intervalo entre partos médio (meses)": "Intervalo partos",
    "Taxa de mortalidade média de bezerros (%)": "Mortal. bezerros",
    "Taxa de mortalidade média de animais adultos (%)": "Mortal. adultos",
    "Há quanto tempo vende para o mesmo comprador? (anos)": "Tempo c/ comprador",
    "Preço recebido no último mês? (R$/litro)": "Preço (mês)",
    "Preço médio recebido nas águas? (R$/litro)": "Preço (águas)",
    "Preço médio recebido na seca? (R$/litro)": "Preço (seca)",
}


def _short_corr_label(label: str) -> str:
    return _CORR_SHORT_LABELS.get(label, _truncate(label, max_len=18))


def correlation_heatmap(corr: pd.DataFrame, height: int = 600, threshold: float = 0.5) -> go.Figure:
    """Mapa de calor de correlação, só com o triângulo inferior (a matriz é
    espelhada — mostrar as duas metades só duplica a informação) e só destacando
    |r| >= threshold (correlações fracas viram ruído visual e são escondidas)."""
    full_labels = list(corr.columns)
    short_labels = [_short_corr_label(c) for c in full_labels]
    n = len(full_labels)
    values = corr.values.astype(float)

    upper_or_diag = np.triu(np.ones((n, n), dtype=bool), k=0)
    weak = np.abs(values) < threshold
    z_display = np.where(upper_or_diag | weak, np.nan, values)

    customdata = [
        [f"{full_labels[c]} × {full_labels[r]}<br>r = {values[r, c]:.2f}" for c in range(n)] for r in range(n)
    ]

    fig = go.Figure(
        go.Heatmap(
            z=z_display,
            x=short_labels,
            y=short_labels,
            customdata=customdata,
            colorscale="RdBu",
            zmid=0,
            zmin=-1,
            zmax=1,
            xgap=2,
            ygap=2,
            colorbar=dict(title="r"),
            hovertemplate="%{customdata}<extra></extra>",
        )
    )
    fig = _base_layout(fig, height)
    fig.update_layout(
        xaxis=dict(tickangle=-45, automargin=True, tickfont=dict(size=10)),
        yaxis=dict(autorange="reversed", automargin=True, tickfont=dict(size=10)),
        margin=dict(t=16, b=140, l=160, r=16),
    )
    return fig


_ORDINAL_ORDERS = [
    ["Baixo", "Médio-baixo", "Médio-alto", "Alto"],
    ["Baixo", "Alto"],
]


def _category_order(values: list[str]) -> list[str]:
    """Ordena as categorias da 1ª dimensão de forma previsível: se forem faixas de
    quartil (Baixo/Médio-baixo/Médio-alto/Alto), mantém essa ordem natural; senão,
    ordena alfabeticamente, deixando "Não informado" por último."""
    uniq = list(dict.fromkeys(values))
    for order in _ORDINAL_ORDERS:
        if set(uniq) <= set(order):
            return [c for c in order if c in uniq]
    rest = sorted(c for c in uniq if c != "Não informado")
    return rest + (["Não informado"] if "Não informado" in uniq else [])


def parallel_categories(
    df: pd.DataFrame, dim_cols: list[str], dim_labels: list[str], height: int = 520
) -> tuple[go.Figure, list[tuple[str, str]]]:
    """Diagrama de categorias paralelas: mostra como até ~5 variáveis (categóricas,
    de múltipla escolha ou numéricas já divididas em faixas) se relacionam entre si
    através de faixas que fluem de uma variável pra outra. As faixas são coloridas
    pelas categorias da 1ª variável escolhida; devolve também essa legenda
    (categoria, cor) em ordem organizada, pra ser desenhada ao lado do gráfico."""
    dimensions = [dict(values=df[col].astype(str), label=label) for col, label in zip(dim_cols, dim_labels)]
    first_values = df[dim_cols[0]].astype(str).tolist()
    order = _category_order(first_values)
    ramp = teal_ramp(len(order))
    color_of = dict(zip(order, ramp))
    codes = [order.index(v) for v in first_values]
    colorscale = [[i / max(len(order) - 1, 1), ramp[i]] for i in range(len(order))]
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
    legend_items = [(cat, color_of[cat]) for cat in order]
    return fig, legend_items


NEUTRAL_ASSOC_COLOR = "#7B6FD1"  # roxo — usado pra η/Cramér's V, que não têm sinal


def factor_association_bar(
    ranking: pd.DataFrame, labels: list[str], full_labels: list[str] | None = None, height: int | None = None
) -> go.Figure:
    """Barras horizontais com a força/direção da associação de um fator com
    cada um dos outros já listados em `ranking` (mão única, other_key). Barra
    azul/vermelha (RdBu) quando o método tem sinal (Pearson/ponto-bisserial/
    Phi); roxo neutro quando não tem (η, Cramér's V) — pra não sugerir uma
    direção que a métrica não define. `labels` já vem quebrado em várias
    linhas (nunca truncado) — `full_labels` (opcional) é o texto sem quebra,
    só pro hover. Plotly dá a mesma altura pra toda linha do eixo categórico,
    então a altura da figura precisa considerar o rótulo com MAIS linhas de
    todos, não uma altura fixa por barra."""
    n = len(ranking)
    max_label_lines = max((lbl.count("<br>") + 1 for lbl in labels), default=1)
    height = height or max(280, n * (22 * max_label_lines + 20))
    full_labels = full_labels or labels
    plot_values = []
    colors = []
    text = []
    for _, row in ranking.iterrows():
        signed = pd.notna(row["r"])
        v = row["r"] if signed else row["value"]
        plot_values.append(v)
        # Barra esmaecida quando não-significativa (p >= 0,05) — sem isso, uma
        # associação forte só por acaso (comum ao testar 200+ pares numa
        # amostra pequena) fica visualmente idêntica a um achado real. p-valor
        # ausente (raro, casos inválidos) não esmaece: sem evidência de que
        # NÃO é significativo, não presumimos isso visualmente.
        p = row["p_value"]
        alpha = 1.0 if pd.isna(p) or p < 0.05 else 0.35
        if signed:
            base = COLOR_PRIMARY if v >= 0 else "#B2182B"
            text.append(f"{v:+.2f}")
        else:
            base = NEUTRAL_ASSOC_COLOR
            text.append(f"{v:.2f}")
        colors.append(_with_alpha(base, alpha))

    customdata = np.stack(
        [ranking["method"].values, ranking["p_value"].values, ranking["n"].values, full_labels], axis=-1
    )
    fig = go.Figure(
        go.Bar(
            x=plot_values,
            y=labels,
            orientation="h",
            marker=dict(color=colors),
            text=text,
            textposition="outside",
            customdata=customdata,
            hovertemplate=(
                "%{customdata[3]}<br>Coeficiente: %{x:.3f}<br>Método: %{customdata[0]}<br>"
                "p = %{customdata[1]:.3f}<br>N = %{customdata[2]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed", showgrid=False, automargin=True),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=True, zerolinecolor="rgba(0,0,0,0.25)", zerolinewidth=1.5),
        showlegend=False,
    )
    return _base_layout(fig, height)


def full_association_heatmap(matrix_wide: pd.DataFrame, p_wide: pd.DataFrame | None = None, height: int = 900) -> go.Figure:
    """Heatmap completo de todos os fatores (magnitude 0-1, sem sinal — mistura
    métodos diferentes, então mostrar sinal seria enganoso). Rolagem/zoom vêm
    de graça do Plotly; nomes truncados com o completo disponível no hover.
    `p_wide` (opcional) leva o p-valor pro hover — testar 200+ fatores par a
    par numa amostra pequena produz muita célula "forte" só por acaso, então
    o p-valor precisa estar a um hover de distância, não só na aba de fator
    único."""
    labels = list(matrix_wide.columns)
    short_labels = [_truncate(str(c), max_len=22) for c in labels]
    n = len(labels)
    customdata = np.empty((n, n, 2), dtype=object)
    for i, a in enumerate(labels):
        for j, b in enumerate(labels):
            customdata[j, i, 0] = f"{a} × {b}"
            p = p_wide.iat[j, i] if p_wide is not None else np.nan
            customdata[j, i, 1] = "não significativo (p ≥ 0,05)" if pd.notna(p) and p >= 0.05 else (f"p = {p:.3f}" if pd.notna(p) else "—")
    fig = go.Figure(
        go.Heatmap(
            z=matrix_wide.values,
            x=short_labels,
            y=short_labels,
            customdata=customdata,
            colorscale=[[0, "#F5F8F9"], [1, COLOR_PRIMARY]],
            zmin=0,
            zmax=1,
            colorbar=dict(title="força"),
            hovertemplate="%{customdata[0]}<br>%{z:.2f} · %{customdata[1]}<extra></extra>",
        )
    )
    fig = _base_layout(fig, height)
    fig.update_layout(
        xaxis=dict(tickangle=-45, automargin=True, tickfont=dict(size=9)),
        yaxis=dict(autorange="reversed", automargin=True, tickfont=dict(size=9)),
        margin=dict(t=16, b=160, l=200, r=16),
    )
    return fig
