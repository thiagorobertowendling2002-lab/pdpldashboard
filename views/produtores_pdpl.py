import re

import pandas as pd
import streamlit as st

import charts
from branding import render_footer, render_header, render_kpi_row, render_section_header
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


def build_variable_options(cat: dict, include_numeric: bool = True) -> list[dict]:
    """Lista achatada de TODAS as perguntas da pesquisa (categóricas, numéricas e
    cada opção de perguntas de múltipla escolha), pra usar em seletores livres."""
    items = []
    for v in cat["categorical_vars"]:
        items.append(
            {"label": f"[{v['section']}] {v['label']}", "key": v["key"], "kind": "cat", "section": v["section"]}
        )
    if include_numeric:
        for v in cat["numeric_vars"]:
            items.append(
                {
                    "label": f"[{v['section']}] {v['label']}",
                    "key": v["key"],
                    "kind": "num",
                    "unit": v["unit"],
                    "section": v["section"],
                }
            )
    for g in cat["multiselect_groups"].values():
        for opt_label, col in g["items"]:
            items.append(
                {
                    "label": f"[{g['section']}] {g['label']}: {opt_label}",
                    "key": col,
                    "kind": "flag",
                    "section": g["section"],
                }
            )
    items.sort(key=lambda v: v["label"])
    return items


def build_question_options(cat: dict) -> list[dict]:
    """Lista de perguntas "de verdade" (sem explodir múltipla escolha em uma linha
    por opção) — usada no filtro avançado em cascata: pergunta de múltipla escolha
    vira uma etapa a mais (escolher a opção) antes do Sim/Não."""
    items = []
    for v in cat["categorical_vars"]:
        items.append({"label": v["label"], "section": v["section"], "kind": "cat", "key": v["key"]})
    for g in cat["multiselect_groups"].values():
        items.append({"label": g["label"], "section": g["section"], "kind": "group", "items": g["items"]})
    items.sort(key=lambda v: v["label"])
    return items


def render_advanced_filter(
    question_options: list[dict], sections_with_vars: list[str], instance_key: str
) -> tuple[dict, list[str], str] | None:
    """Um bloco Seção -> Pergunta -> [Opção] -> Resposta, empilhado verticalmente
    (pensado pra caber na barra lateral). Retorna (variável, valores escolhidos,
    rótulo completo) se o usuário completou esse filtro, senão None."""
    section = st.selectbox("Seção", ["(nenhuma)"] + sections_with_vars, key=f"adv_section_{instance_key}")
    if section == "(nenhuma)":
        return None

    section_qs = [q for q in question_options if q["section"] == section]
    q_labels = [q["label"] for q in section_qs]
    q_by_label = dict(zip(q_labels, section_qs))
    q_label = st.selectbox("Pergunta", ["(nenhuma)"] + q_labels, key=f"adv_q_{instance_key}_{section}")
    if q_label == "(nenhuma)":
        return None

    question = q_by_label[q_label]
    if question["kind"] == "group":
        opt_labels = [lbl for lbl, _ in question["items"]]
        opt_by_label = dict(question["items"])
        opt_label = st.selectbox(
            "Opção", ["(nenhuma)"] + opt_labels, key=f"adv_opt_{instance_key}_{section}_{q_label}"
        )
        if opt_label == "(nenhuma)":
            return None
        var = {"key": opt_by_label[opt_label], "kind": "flag"}
        full_label = f"{q_label}: {opt_label}"
        values = st.multiselect(
            "Resposta", ["Sim", "Não"], default=[], key=f"adv_v_{instance_key}_{section}_{q_label}_{opt_label}"
        )
    else:
        var = {"key": question["key"], "kind": "cat"}
        full_label = q_label
        value_pool = sorted(raw[question["key"]].dropna().astype(str).unique().tolist())
        values = st.multiselect("Resposta", value_pool, default=[], key=f"adv_v_{instance_key}_{section}_{q_label}")

    return (var, values, full_label) if values else None


def filter_mask(var: dict, values: list[str]) -> pd.Series:
    series = raw[var["key"]].fillna("Não") if var["kind"] == "flag" else raw[var["key"]].astype(str)
    return series.isin(values)


# ---------------------------------------------------------------- Filtros (barra lateral)
# Ficam na sidebar de propósito: assim dá pra ajustar um filtro e ver o resultado nos
# gráficos na hora, em qualquer parte da página, sem precisar rolar até o topo.
with st.sidebar:
    st.markdown("### 🔎 Filtros")
    st.caption("Deixe em branco para incluir todos")
    options = filter_options()
    sel_municipio = st.multiselect("Município", options["municipio"], default=[])
    sel_tipologia = st.multiselect("Tipologia", options["tipologia"], default=[])
    sel_estrato = st.multiselect("Estrato de produção", options["estrato_producao"], default=[])
    sel_sistema = st.multiselect("Sistema de produção", options["sistema_producao"], default=[])

    question_options = build_question_options(catalog)
    sections_with_vars = [s for s in SECTION_ORDER if any(q["section"] == s for q in question_options)]

    MAX_ADV_FILTERS = 4
    if "n_adv_filters" not in st.session_state:
        st.session_state["n_adv_filters"] = 1

    active_filters: list[tuple[dict, list[str], str]] = []
    with st.expander("⚙️ Filtro avançado"):
        st.caption("Qualquer pergunta da pesquisa, ex: Crédito Rural → PRONAF → Sim")
        n_visible = st.session_state["n_adv_filters"]
        for i in range(n_visible):
            if n_visible > 1:
                st.markdown(f"**Filtro {i + 1}**")
            result = render_advanced_filter(question_options, sections_with_vars, f"f{i}")
            if result:
                active_filters.append(result)
            if i < n_visible - 1:
                st.markdown("---")

        if n_visible < MAX_ADV_FILTERS:
            if st.button("➕ Adicionar outro filtro", key="add_adv_filter"):
                st.session_state["n_adv_filters"] += 1
                st.rerun()

    if active_filters:
        combined_mask = pd.Series(True, index=raw.index)
        parts = []
        for var, values, full_label in active_filters:
            combined_mask &= filter_mask(var, values)
            parts.append(f"{full_label} = {' ou '.join(values)}")
        n_match = int(combined_mask.sum())
        st.success(f"**{n_match}** de {len(raw)} produtores atendem:\n\n" + "\n\n**E**\n\n".join(parts))

df = apply_filters(
    raw,
    {
        "municipio": sel_municipio,
        "tipologia": sel_tipologia,
        "estrato_producao": sel_estrato,
        "sistema_producao": sel_sistema,
    },
)

for var, values, _ in active_filters:
    df = df[filter_mask(var, values).loc[df.index]]

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
MDO_COL = "MDO TOTAL (TRABALHADOR/DIA)"
TEMPO_PRODUTOR_COL = "2.2. Tempo que é produtor(a) de leite (anos)"
RENDA_LEITE_COL = "2.9. Composição da renda bruta do produtor rural: Pecuária de leite (%)"

produtividade_terra = ((df[PRODUCAO_COL] * 365) / df[AREA_COL].replace(0, pd.NA)).mean()
produtividade_mao_obra = (df[PRODUCAO_COL] / df[MDO_COL].replace(0, pd.NA)).mean()

render_kpi_row(
    [
        ("👥", "Produtores", str(len(df))),
        ("🥛", "Produção média", f"{fmt_br(df[PRODUCAO_COL].mean(), 0)} L/dia"),
        ("📈", "Produtividade média", f"{fmt_br(df[PRODUTIVIDADE_COL].mean())} L/vaca/d"),
        ("🌾", "Área p/ gado de leite", f"{fmt_br(df[AREA_COL].mean())} ha"),
        ("🎂", "Idade média", f"{fmt_br(df[IDADE_COL].mean(), 0)} anos"),
        ("💰", "Preço médio recebido", f"R$ {fmt_br(df[PRECO_COL].mean(), 2)}"),
        ("🌱", "Produtividade da terra", f"{fmt_br(produtividade_terra, 0)} L/ha/ano"),
        ("👷", "Produtividade da mão de obra", f"{fmt_br(produtividade_mao_obra, 0)} L/trab/dia"),
        ("⏳", "Tempo como produtor", f"{fmt_br(df[TEMPO_PRODUTOR_COL].mean(), 0)} anos"),
        ("💵", "Renda vinda do leite", f"{fmt_br(df[RENDA_LEITE_COL].mean(), 0)}%"),
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
            with col, st.container(border=True):
                st.markdown(f"**{var['label']}**")
                fig = charts.donut(counts) if len(counts) <= 5 else charts.ranked_bar(counts)
                st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_cat_{i}_{j}")


def render_numeric_groups(groups: list[dict], key_prefix: str) -> None:
    for i, g in enumerate(groups):
        items = [(lbl, df[col].mean()) for lbl, col in g["items"]]
        items = [(lbl, v) for lbl, v in items if pd.notna(v)]
        if not items:
            continue
        with st.container(border=True):
            st.markdown(f"**{g['label']}**")
            fig = charts.composition_bar(items, is_percent=g["is_percent"])
            st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_grp_{i}")


def render_multiselect_groups(groups: list[dict], key_prefix: str) -> None:
    for i, g in enumerate(groups):
        counts = pd.Series({lbl: int((df[col] == "Sim").sum()) for lbl, col in g["items"]})
        counts = counts[counts > 0]
        if counts.empty:
            continue
        with st.container(border=True):
            st.markdown(f"**{g['label']}**")
            fig = charts.ranked_bar(counts)
            st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_ms_{i}")


def render_numeric_grid(num_vars: list[dict], key_prefix: str) -> None:
    for i in range(0, len(num_vars), 2):
        row = num_vars[i : i + 2]
        cols = st.columns(len(row))
        for j, (col, var) in enumerate(zip(cols, row)):
            series = df[var["key"]].dropna()
            if series.empty:
                continue
            with col, st.container(border=True):
                st.markdown(f"**{var['label']}**")
                fig = charts.histogram(series, var["unit"])
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
        render_section_header("Pontos em comum na amostra", "✅")
        render_fun_facts(facts)

    if cat_vars:
        render_section_header("Perfil", "👤")
        render_categorical_grid(cat_vars, key_prefix)

    if num_groups:
        render_section_header("Composição", "🧮")
        render_numeric_groups(num_groups, key_prefix)

    if ms_groups:
        render_section_header("Múltipla escolha", "☑️")
        render_multiselect_groups(ms_groups, key_prefix)

    if num_vars:
        render_section_header("Indicadores numéricos", "📐")
        render_numeric_grid(num_vars, key_prefix)


def bin_numeric(series: pd.Series) -> pd.Series:
    """Divide uma variável numérica em faixas (quartis) pra poder cruzar com
    variáveis categóricas num diagrama de categorias paralelas."""
    non_null = series.dropna()
    result = pd.Series("Não informado", index=series.index, dtype=object)
    if non_null.empty:
        return result
    try:
        binned = pd.qcut(non_null, q=4, labels=["Baixo", "Médio-baixo", "Médio-alto", "Alto"], duplicates="drop")
    except ValueError:
        try:
            binned = pd.qcut(non_null, q=2, labels=["Baixo", "Alto"], duplicates="drop")
        except ValueError:
            binned = non_null.astype(str)
    result.loc[non_null.index] = binned.astype(str)
    return result


# ---------------------------------------------------------------- Tabs
section_tabs = [s for s in SECTION_ORDER if s != "Amostra"]
tab_labels = (
    ["📊 Visão Geral"]
    + section_tabs
    + ["🔍 Explorador", "🧩 Comparação e Filtragem entre Parâmetros", "🔗 Correlações"]
)
tabs = st.tabs(tab_labels)

with tabs[0]:
    render_section_header("Amostra", "🗂️")
    amostra_vars = [v for v in catalog["categorical_vars"] if v["section"] == "Amostra"]
    render_categorical_grid(amostra_vars, "visao_geral")

    render_section_header("Destaques", "⭐")
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

with tabs[-3]:
    render_section_header("Compare quaisquer duas variáveis da pesquisa", "🔍")
    with st.container(border=True):
        st.caption(
            "Inclui perguntas de resposta única, números **e cada opção de perguntas de múltipla escolha** "
            "(ex: \"Se utilizou, quais as principais linhas de crédito?: PRONAF\") — digite pra buscar."
        )
        explorer_vars = build_variable_options(catalog, include_numeric=True)
        labels = [v["label"] for v in explorer_vars]
        by_label = {v["label"]: v for v in explorer_vars}

        default_a = next((l for l in labels if "Produção de leite média" in l), labels[0])
        default_b = next((l for l in labels if "Tipologia" in l), labels[1] if len(labels) > 1 else labels[0])

        c1, c2 = st.columns(2)
        var_a_label = c1.selectbox("Variável A", labels, index=labels.index(default_a))
        var_b_label = c2.selectbox("Variável B", labels, index=labels.index(default_b))

    var_a, var_b = by_label[var_a_label], by_label[var_b_label]

    # perguntas de múltipla escolha (flag) viram categóricas Sim/Não; NaN = "Não" respondeu essa opção
    df_pair = df.copy()
    for v in (var_a, var_b):
        if v["kind"] == "flag":
            df_pair[v["key"]] = df_pair[v["key"]].fillna("Não")

    def is_categorical(kind: str) -> bool:
        return kind in ("cat", "flag")

    if is_categorical(var_a["kind"]) and is_categorical(var_b["kind"]):
        chart_title = f"{var_a['label']} × {var_b['label']}"
        fig = charts.grouped_bar_crosstab(df_pair, var_a["key"], var_b["key"])
    elif var_a["kind"] == "num" and var_b["kind"] == "num":
        chart_title = f"{var_a['label']} × {var_b['label']}"
        fig = charts.scatter(df_pair, var_a["key"], var_b["key"], var_a["label"], var_b["label"])
    else:
        num_var, cat_var = (var_a, var_b) if var_a["kind"] == "num" else (var_b, var_a)
        chart_title = f"{num_var['label']} por {cat_var['label']}"
        fig = charts.box_by_category(df_pair, cat_var["key"], num_var["key"], num_var.get("unit", ""))
    with st.container(border=True):
        st.markdown(f"**{chart_title}**")
        st.plotly_chart(fig, use_container_width=True, key="explorer_chart")

with tabs[-2]:
    render_section_header("Comparação e Filtragem entre Parâmetros", "🧩")
    with st.container(border=True):
        st.caption(
            "Escolha de 2 a 5 perguntas de **qualquer tipo** — qualitativas (respostas únicas, múltipla escolha) "
            "ou quantitativas (números, que são divididos em faixas Baixo/Médio/Alto) — e veja como as respostas "
            "de cada produtor fluem entre elas. Passe o mouse nas faixas do gráfico pra ver quantos produtores "
            "seguem cada caminho."
        )
        multi_vars = build_variable_options(catalog, include_numeric=True)
        multi_labels = [v["label"] for v in multi_vars]
        multi_by_label = {v["label"]: v for v in multi_vars}

        default_multi = []
        for hint in ["Para os próximos 5 anos", "linhas de crédito?: Pronaf", "Tipologia", "Estrato"]:
            match = next((l for l in multi_labels if hint.lower() in l.lower()), None)
            if match and match not in default_multi:
                default_multi.append(match)

        chosen_labels = st.multiselect(
            "Variáveis (escolha de 2 a 5)",
            multi_labels,
            default=default_multi[:4],
            max_selections=5,
            key="multi_param_vars",
        )

    if len(chosen_labels) < 2:
        st.info("Escolha pelo menos 2 variáveis pra ver a comparação.")
    else:
        chosen_vars = [multi_by_label[l] for l in chosen_labels]
        df_multi = df.copy()
        dim_cols, dim_labels = [], []
        for v in chosen_vars:
            col = v["key"]
            if v["kind"] == "num":
                bin_col = f"__bin__{col}"
                df_multi[bin_col] = bin_numeric(df_multi[col])
                dim_cols.append(bin_col)
            else:
                if v["kind"] == "flag":
                    df_multi[col] = df_multi[col].fillna("Não")
                dim_cols.append(col)
            short_label = re.sub(r"^\[[^\]]+\]\s*", "", v["label"])
            if len(short_label) > 32:
                short_label = short_label[:31].rstrip() + "…"
            dim_labels.append(short_label)

        with st.container(border=True):
            fig = charts.parallel_categories(df_multi, dim_cols, dim_labels)
            st.plotly_chart(fig, use_container_width=True, key="multi_parcats")

        render_section_header("Tabela dos produtores filtrados", "📋")
        with st.container(border=True):
            st.caption("Cada linha é um produtor da amostra atual, com as respostas nas variáveis escolhidas.")
            table_df = df[[v["key"] for v in chosen_vars]].copy()
            table_df.columns = [v["label"] for v in chosen_vars]
            for v in chosen_vars:
                if v["kind"] == "flag":
                    table_df[v["label"]] = table_df[v["label"]].fillna("Não")
            st.dataframe(table_df, use_container_width=True, height=min(400, 40 + 35 * len(table_df)))

with tabs[-1]:
    render_section_header("Correlação entre variáveis numéricas", "🔗")
    st.caption("Quanto mais próximo de 1 (azul) ou -1 (vermelho), mais forte a relação entre as duas variáveis.")
    num_keys = [v["key"] for v in catalog["numeric_vars"]]
    num_labels = {v["key"]: v["label"] for v in catalog["numeric_vars"]}
    corr_df = df[num_keys].rename(columns=num_labels)
    corr = corr_df.corr(numeric_only=True)
    height = max(600, 26 * len(num_keys))
    with st.container(border=True):
        st.plotly_chart(charts.correlation_heatmap(corr, height=height), use_container_width=True, key="corr_heatmap")

render_footer()
