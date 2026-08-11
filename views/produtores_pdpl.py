import pandas as pd
import streamlit as st

import charts
from branding import render_footer, render_header, render_kpi_row
from data_loader import SECTION_ORDER, apply_filters, build_catalog, filter_options, load_raw

render_header("Produtores PDPL")

try:
    raw = load_raw()
    catalog = build_catalog()
except FileNotFoundError:
    st.info(
        "Este dashboard ainda não tem dados publicados neste ambiente — "
        "disponível apenas rodando localmente por enquanto."
    )
    render_footer()
    st.stop()


def fmt_br(value, decimals: int = 1) -> str:
    if pd.isna(value):
        return "—"
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- Filtros
with st.container(border=True):
    st.markdown("**🔎 Filtros** — deixe em branco para incluir todos")
    options = filter_options()
    f1, f2, f3, f4 = st.columns(4)
    sel_municipio = f1.multiselect("Município", options["municipio"], default=[])
    sel_tipologia = f2.multiselect("Tipologia", options["tipologia"], default=[])
    sel_estrato = f3.multiselect("Estrato de produção", options["estrato_producao"], default=[])
    sel_sistema = f4.multiselect("Sistema de produção", options["sistema_producao"], default=[])

df = apply_filters(
    raw,
    {
        "municipio": sel_municipio,
        "tipologia": sel_tipologia,
        "estrato_producao": sel_estrato,
        "sistema_producao": sel_sistema,
    },
)

if df.empty:
    st.warning("Nenhum produtor corresponde aos filtros selecionados.")
    render_footer()
    st.stop()

st.caption(f"Mostrando **{len(df)}** de **{len(raw)}** produtores.")

# ---------------------------------------------------------------- KPIs
PRODUCAO_COL = "5.2. Produção de leite média dos últimos 12 meses (consumido + vendido) (litros/dia)"
PRODUTIVIDADE_COL = "5.3. Produtividade média / vaca em lactação (litros/vaca/dia)"
AREA_COL = "5.6. Área destinada ao gado de leite (hectares)"
IDADE_COL = "2.1. Idade (anos)"
PRECO_COL = "11.3. Preço recebido no último mês? (R$/litro)"

render_kpi_row(
    [
        ("Produtores", str(len(df))),
        ("Produção média", f"{fmt_br(df[PRODUCAO_COL].mean(), 0)} L/dia"),
        ("Produtividade média", f"{fmt_br(df[PRODUTIVIDADE_COL].mean())} L/vaca/d"),
        ("Área p/ gado de leite", f"{fmt_br(df[AREA_COL].mean())} ha"),
        ("Idade média", f"{fmt_br(df[IDADE_COL].mean(), 0)} anos"),
        ("Preço médio recebido", f"R$ {fmt_br(df[PRECO_COL].mean(), 2)}"),
    ]
)

st.markdown("")


# ---------------------------------------------------------------- Helpers de render
def render_categorical_grid(cat_vars: list[dict], key_prefix: str) -> None:
    for i in range(0, len(cat_vars), 2):
        row = cat_vars[i : i + 2]
        cols = st.columns(len(row))
        for j, (col, var) in enumerate(zip(cols, row)):
            counts = df[var["key"]].value_counts()
            if counts.empty:
                continue
            with col:
                fig = charts.donut(counts, var["label"]) if len(counts) <= 5 else charts.ranked_bar(counts, var["label"])
                st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_cat_{i}_{j}")


def render_numeric_groups(groups: list[dict], key_prefix: str) -> None:
    for i, g in enumerate(groups):
        items = [(lbl, df[col].mean()) for lbl, col in g["items"]]
        items = [(lbl, v) for lbl, v in items if pd.notna(v)]
        if not items:
            continue
        fig = charts.composition_bar(items, g["label"], is_percent=g["is_percent"])
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_grp_{i}")


def render_multiselect_groups(groups: list[dict], key_prefix: str) -> None:
    for i, g in enumerate(groups):
        counts = pd.Series({lbl: int((df[col] == "Sim").sum()) for lbl, col in g["items"]})
        counts = counts[counts > 0]
        if counts.empty:
            continue
        fig = charts.ranked_bar(counts, g["label"])
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_ms_{i}")


def render_numeric_grid(num_vars: list[dict], key_prefix: str) -> None:
    for i in range(0, len(num_vars), 2):
        row = num_vars[i : i + 2]
        cols = st.columns(len(row))
        for j, (col, var) in enumerate(zip(cols, row)):
            series = df[var["key"]].dropna()
            if series.empty:
                continue
            with col:
                fig = charts.histogram(series, var["label"], var["unit"])
                st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_num_{i}_{j}")


def render_fun_facts(facts: list[dict]) -> None:
    cols = st.columns(min(len(facts), 4))
    for i, fact in enumerate(facts):
        with cols[i % len(cols)]:
            st.success(f"**{fact['label']}**\n\n{fact['value']} · {fact['count']}/{len(df)} produtores")


def render_section(section: str) -> None:
    key_prefix = section.replace(" ", "_")
    facts = [f for f in catalog["fun_facts"] if f["section"] == section]
    cat_vars = [v for v in catalog["categorical_vars"] if v["section"] == section]
    num_groups = [g for g in catalog["numeric_groups"].values() if g["section"] == section]
    ms_groups = [g for g in catalog["multiselect_groups"].values() if g["section"] == section]
    num_vars = [v for v in catalog["numeric_vars"] if v["section"] == section]

    if not any([facts, cat_vars, num_groups, ms_groups, num_vars]):
        st.caption("Sem dados adicionais nesta seção.")
        return

    if facts:
        st.markdown("###### ✅ Pontos em comum na amostra")
        render_fun_facts(facts)
        st.markdown("")

    if cat_vars:
        st.markdown("###### Perfil")
        render_categorical_grid(cat_vars, key_prefix)

    if num_groups:
        st.markdown("###### Composição")
        render_numeric_groups(num_groups, key_prefix)

    if ms_groups:
        st.markdown("###### Múltipla escolha")
        render_multiselect_groups(ms_groups, key_prefix)

    if num_vars:
        st.markdown("###### Indicadores numéricos")
        render_numeric_grid(num_vars, key_prefix)


# ---------------------------------------------------------------- Tabs
section_tabs = [s for s in SECTION_ORDER if s != "Amostra"]
tab_labels = ["📊 Visão Geral"] + section_tabs + ["🔍 Explorador", "🔗 Correlações"]
tabs = st.tabs(tab_labels)

with tabs[0]:
    st.markdown("###### Amostra")
    amostra_vars = [v for v in catalog["categorical_vars"] if v["section"] == "Amostra"]
    render_categorical_grid(amostra_vars, "visao_geral")

    st.markdown("###### Destaques")
    highlight_keys = {
        "Perfil do Produtor e Renda": ["Escolaridade", "Sexo"],
        "Motivação e Percepção": ["Atualmente, seu retorno financeiro na produção de leite pode ser considerado"],
    }
    highlights = []
    for section, labels in highlight_keys.items():
        for v in catalog["categorical_vars"]:
            if v["section"] == section and v["label"] in labels:
                highlights.append(v)
    render_categorical_grid(highlights, "visao_geral_destaques")

for section, tab in zip(section_tabs, tabs[1 : 1 + len(section_tabs)]):
    with tab:
        render_section(section)

with tabs[-2]:
    st.markdown("### Compare quaisquer duas variáveis da pesquisa")
    explorer_vars = []
    for v in catalog["categorical_vars"]:
        explorer_vars.append({"label": f"[{v['section']}] {v['label']}", "key": v["key"], "kind": "cat"})
    for v in catalog["numeric_vars"]:
        explorer_vars.append({"label": f"[{v['section']}] {v['label']}", "key": v["key"], "kind": "num", "unit": v["unit"]})
    explorer_vars.sort(key=lambda v: v["label"])
    labels = [v["label"] for v in explorer_vars]
    by_label = {v["label"]: v for v in explorer_vars}

    default_a = next((l for l in labels if "Produção de leite média" in l), labels[0])
    default_b = next((l for l in labels if "Tipologia" in l), labels[1] if len(labels) > 1 else labels[0])

    c1, c2 = st.columns(2)
    var_a_label = c1.selectbox("Variável A", labels, index=labels.index(default_a))
    var_b_label = c2.selectbox("Variável B", labels, index=labels.index(default_b))

    var_a, var_b = by_label[var_a_label], by_label[var_b_label]

    if var_a["kind"] == "cat" and var_b["kind"] == "cat":
        fig = charts.grouped_bar_crosstab(df, var_a["key"], var_b["key"], f"{var_a['label']} × {var_b['label']}")
    elif var_a["kind"] == "num" and var_b["kind"] == "num":
        fig = charts.scatter(df, var_a["key"], var_b["key"], f"{var_a['label']} × {var_b['label']}", var_a["label"], var_b["label"])
    else:
        num_var, cat_var = (var_a, var_b) if var_a["kind"] == "num" else (var_b, var_a)
        fig = charts.box_by_category(
            df, cat_var["key"], num_var["key"], f"{num_var['label']} por {cat_var['label']}", num_var.get("unit", "")
        )
    st.plotly_chart(fig, use_container_width=True, key="explorer_chart")

with tabs[-1]:
    st.markdown("### Correlação entre variáveis numéricas")
    st.caption("Quanto mais próximo de 1 (azul) ou -1 (vermelho), mais forte a relação entre as duas variáveis.")
    num_keys = [v["key"] for v in catalog["numeric_vars"]]
    num_labels = {v["key"]: v["label"] for v in catalog["numeric_vars"]}
    corr_df = df[num_keys].rename(columns=num_labels)
    corr = corr_df.corr(numeric_only=True)
    height = max(600, 26 * len(num_keys))
    st.plotly_chart(charts.correlation_heatmap(corr, height=height), use_container_width=True, key="corr_heatmap")

render_footer()
