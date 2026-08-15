import re

import numpy as np
import pandas as pd
import streamlit as st

import charts
from association import compute_association_matrix, factor_ranking, strength_label
from branding import render_color_legend, render_footer, render_header, render_kpi_row, render_section_header
from data_loader import SECTION_ORDER, apply_filters, build_catalog, build_factor_list, filter_options, load_raw

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


def build_question_options(cat: dict, include_numeric: bool = False) -> list[dict]:
    """Lista de perguntas "de verdade" (sem explodir múltipla escolha em uma linha
    por opção) — usada nos seletores em cascata (filtro avançado e comparação):
    pergunta de múltipla escolha vira uma etapa a mais (escolher a opção) antes
    do Sim/Não."""
    items = []
    for v in cat["categorical_vars"]:
        items.append({"label": v["label"], "section": v["section"], "kind": "cat", "key": v["key"]})
    if include_numeric:
        for v in cat["numeric_vars"]:
            items.append(
                {"label": v["label"], "section": v["section"], "kind": "num", "key": v["key"], "unit": v["unit"]}
            )
    for g in cat["multiselect_groups"].values():
        items.append({"label": g["label"], "section": g["section"], "kind": "group", "items": g["items"]})
    items.sort(key=lambda v: v["label"])
    return items


def render_variable_picker(
    question_options: list[dict], sections_with_vars: list[str], instance_key: str
) -> dict | None:
    """Um seletor em cascata Seção -> Pergunta -> [Opção] que devolve UMA variável
    inteira (não valores pra filtrar) — usado na aba de comparação entre parâmetros."""
    section = st.selectbox("Seção", ["(nenhuma)"] + sections_with_vars, key=f"cmp_section_{instance_key}")
    if section == "(nenhuma)":
        return None

    section_qs = [q for q in question_options if q["section"] == section]
    q_labels = [q["label"] for q in section_qs]
    q_by_label = dict(zip(q_labels, section_qs))
    q_label = st.selectbox("Pergunta", ["(nenhuma)"] + q_labels, key=f"cmp_q_{instance_key}_{section}")
    if q_label == "(nenhuma)":
        return None

    question = q_by_label[q_label]
    if question["kind"] == "group":
        opt_labels = [lbl for lbl, _ in question["items"]]
        opt_by_label = dict(question["items"])
        opt_label = st.selectbox(
            "Opção", ["(nenhuma)"] + opt_labels, key=f"cmp_opt_{instance_key}_{section}_{q_label}"
        )
        if opt_label == "(nenhuma)":
            return None
        return {"label": f"{q_label}: {opt_label}", "key": opt_by_label[opt_label], "kind": "flag", "section": section}
    if question["kind"] == "num":
        return {
            "label": q_label,
            "key": question["key"],
            "kind": "num",
            "unit": question.get("unit", ""),
            "section": section,
        }
    return {"label": q_label, "key": question["key"], "kind": "cat", "section": section}


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
            "Resposta",
            ["Sim", "Não"],
            default=[],
            key=f"adv_v_{instance_key}_{section}_{q_label}_{opt_label}",
            placeholder="Escolha uma opção",
        )
    else:
        var = {"key": question["key"], "kind": "cat"}
        full_label = q_label
        value_pool = sorted(raw[question["key"]].dropna().astype(str).unique().tolist())
        values = st.multiselect(
            "Resposta",
            value_pool,
            default=[],
            key=f"adv_v_{instance_key}_{section}_{q_label}",
            placeholder="Escolha uma opção",
        )

    return (var, values, full_label) if values else None


def read_advanced_filter_state(
    question_options: list[dict], sections_with_vars: list[str], instance_key: str
) -> tuple[dict, list[str], str] | None:
    """Reconstrói um filtro avançado já configurado a partir do session_state, sem
    desenhar os widgets — usado fora do diálogo, pra manter o filtro valendo mesmo
    com o diálogo fechado."""
    section = st.session_state.get(f"adv_section_{instance_key}", "(nenhuma)")
    if section == "(nenhuma)" or section not in sections_with_vars:
        return None

    section_qs = [q for q in question_options if q["section"] == section]
    q_labels = [q["label"] for q in section_qs]
    q_by_label = dict(zip(q_labels, section_qs))
    q_label = st.session_state.get(f"adv_q_{instance_key}_{section}", "(nenhuma)")
    if q_label == "(nenhuma)" or q_label not in q_by_label:
        return None

    question = q_by_label[q_label]
    if question["kind"] == "group":
        opt_labels = [lbl for lbl, _ in question["items"]]
        opt_by_label = dict(question["items"])
        opt_label = st.session_state.get(f"adv_opt_{instance_key}_{section}_{q_label}", "(nenhuma)")
        if opt_label == "(nenhuma)" or opt_label not in opt_by_label:
            return None
        var = {"key": opt_by_label[opt_label], "kind": "flag"}
        full_label = f"{q_label}: {opt_label}"
        values = st.session_state.get(f"adv_v_{instance_key}_{section}_{q_label}_{opt_label}", [])
    else:
        var = {"key": question["key"], "kind": "cat"}
        full_label = q_label
        values = st.session_state.get(f"adv_v_{instance_key}_{section}_{q_label}", [])

    return (var, values, full_label) if values else None


def filter_mask(var: dict, values: list[str]) -> pd.Series:
    series = raw[var["key"]].fillna("Não") if var["kind"] == "flag" else raw[var["key"]].astype(str)
    return series.isin(values)


# ---------------------------------------------------------------- Filtros (barra lateral)
# Ficam na sidebar de propósito: assim dá pra ajustar um filtro e ver o resultado nos
# gráficos na hora, em qualquer parte da página, sem precisar rolar até o topo.
with st.sidebar:
    st.markdown("### :material/tune: Filtros")
    st.caption("Deixe em branco para incluir todos")
    options = filter_options()
    sel_municipio = st.multiselect("Município", options["municipio"], default=[], placeholder="Escolha uma opção")
    sel_tipologia = st.multiselect("Tipologia", options["tipologia"], default=[], placeholder="Escolha uma opção")
    sel_estrato = st.multiselect(
        "Estrato de produção", options["estrato_producao"], default=[], placeholder="Escolha uma opção"
    )
    sel_sistema = st.multiselect(
        "Sistema de produção", options["sistema_producao"], default=[], placeholder="Escolha uma opção"
    )

    question_options = build_question_options(catalog)
    sections_with_vars = [s for s in SECTION_ORDER if any(q["section"] == s for q in question_options)]

    MAX_ADV_FILTERS = 4
    if "n_adv_filters" not in st.session_state:
        st.session_state["n_adv_filters"] = 1

    @st.dialog(":material/tune: Filtro avançado", width="large", on_dismiss="rerun")
    def advanced_filter_dialog():
        st.caption("Qualquer pergunta da pesquisa, ex: Crédito Rural → PRONAF → Sim")
        n_visible = st.session_state["n_adv_filters"]
        for i in range(n_visible):
            header_col, clear_col = st.columns([6, 1])
            with header_col:
                st.markdown(f"**Filtro {i + 1}**" if n_visible > 1 else "**Filtro**")
            with clear_col:
                if st.button(
                    "",
                    icon=":material/delete:",
                    key=f"clear_adv_filter_{i}",
                    help="Descartar este filtro",
                    use_container_width=True,
                ):
                    st.session_state[f"adv_section_f{i}"] = "(nenhuma)"
                    if i == n_visible - 1 and n_visible > 1:
                        st.session_state["n_adv_filters"] -= 1
                    st.rerun(scope="fragment")
            render_advanced_filter(question_options, sections_with_vars, f"f{i}")
            if i < n_visible - 1:
                st.markdown("---")

        st.markdown("")
        col_add, col_apply = st.columns([1, 1])
        with col_add:
            if n_visible < MAX_ADV_FILTERS and st.button(
                "Adicionar outro filtro", icon=":material/add:", key="add_adv_filter", use_container_width=True
            ):
                st.session_state["n_adv_filters"] += 1
                st.rerun(scope="fragment")
        with col_apply:
            if st.button(
                "Aplicar e fechar",
                icon=":material/check:",
                key="apply_adv_filter",
                type="primary",
                use_container_width=True,
            ):
                st.rerun()

    if st.button("Filtro avançado", icon=":material/tune:", key="open_adv_filter_dialog", use_container_width=True):
        advanced_filter_dialog()

    active_filters: list[tuple[dict, list[str], str]] = []
    for i in range(st.session_state["n_adv_filters"]):
        result = read_advanced_filter_state(question_options, sections_with_vars, f"f{i}")
        if result:
            active_filters.append(result)

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
        ("users", "Produtores", str(len(df))),
        ("droplet", "Produção média", f"{fmt_br(df[PRODUCAO_COL].mean(), 0)} L/dia"),
        ("trending-up", "Produtividade média", f"{fmt_br(df[PRODUTIVIDADE_COL].mean())} L/vaca/d"),
        ("map", "Área p/ gado de leite", f"{fmt_br(df[AREA_COL].mean())} ha"),
        ("calendar", "Idade média", f"{fmt_br(df[IDADE_COL].mean(), 0)} anos"),
        ("tag", "Preço médio recebido", f"R$ {fmt_br(df[PRECO_COL].mean(), 2)}"),
        ("sprout", "Produtividade da terra", f"{fmt_br(produtividade_terra, 0)} L/ha/ano"),
        ("briefcase", "Produtividade da mão de obra", f"{fmt_br(produtividade_mao_obra, 0)} L/trab/dia"),
        ("clock", "Tempo como produtor", f"{fmt_br(df[TEMPO_PRODUTOR_COL].mean(), 0)} anos"),
        ("banknote", "Renda da pecuária leiteira", f"{fmt_br(df[RENDA_LEITE_COL].mean(), 0)}%"),
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
        render_section_header("Pontos em comum na amostra", "check-square")
        render_fun_facts(facts)

    if cat_vars:
        render_section_header("Perfil", "user")
        render_categorical_grid(cat_vars, key_prefix)

    if num_groups:
        render_section_header("Composição", "pie-chart")
        render_numeric_groups(num_groups, key_prefix)

    if ms_groups:
        render_section_header("Múltipla escolha", "check-square")
        render_multiselect_groups(ms_groups, key_prefix)

    if num_vars:
        render_section_header("Indicadores numéricos", "bar-chart")
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


# ---------------------------------------------------------------- Navegação
# Um segmented_control (em vez de st.tabs) porque só ele deixa o Python saber
# qual vista está selecionada — com st.tabs, TODAS as abas são construídas a
# cada rerun (mesmo as escondidas), o que é o motivo real da demora entre
# aplicar um filtro e os dados aparecerem quando há 15 abas com gráficos.
# Aqui, só a vista selecionada é processada, e trocar de vista fica dentro do
# fragmento (não recarrega a página inteira).
section_tabs = [s for s in SECTION_ORDER if s != "Amostra"]


def render_visao_geral(catalog: dict) -> None:
    render_section_header("Amostra", "folder")
    amostra_vars = [v for v in catalog["categorical_vars"] if v["section"] == "Amostra"]
    render_categorical_grid(amostra_vars, "visao_geral")

    render_section_header("Destaques", "star")
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


def render_explorador_tab(df: pd.DataFrame, catalog: dict) -> None:
    render_section_header("Compare quaisquer duas variáveis da pesquisa", "search")

    explorer_questions = build_question_options(catalog, include_numeric=True)
    explorer_sections = [s for s in SECTION_ORDER if any(q["section"] == s for q in explorer_questions)]

    @st.dialog("Escolher variável", width="large", on_dismiss="rerun")
    def explorer_var_dialog(instance_key: str, slot_label: str):
        st.caption(f"{slot_label} — Seção → Pergunta → Opção (se for de múltipla escolha)")
        result = render_variable_picker(explorer_questions, explorer_sections, instance_key)
        st.markdown("")
        if st.button(
            "Aplicar", icon=":material/check:", key=f"apply_explorer_{instance_key}", type="primary", use_container_width=True
        ):
            st.session_state[f"explorer_picked_{instance_key}"] = result
            st.rerun()

    if "explorer_picked_ea" not in st.session_state:
        default_a = next((q for q in explorer_questions if "Produção de leite média" in q["label"]), None)
        st.session_state["explorer_picked_ea"] = (
            {"label": default_a["label"], "key": default_a["key"], "kind": "num", "unit": default_a.get("unit", ""), "section": default_a["section"]}
            if default_a
            else None
        )
    if "explorer_picked_eb" not in st.session_state:
        default_b = next((q for q in explorer_questions if q["label"] == "Tipologia da produção de leite"), None)
        st.session_state["explorer_picked_eb"] = (
            {"label": default_b["label"], "key": default_b["key"], "kind": "cat", "section": default_b["section"]}
            if default_b
            else None
        )

    with st.container(border=True):
        st.caption(
            "Inclui perguntas de resposta única, números e cada opção de perguntas de múltipla escolha "
            "(ex: \"Se utilizou, quais as principais linhas de crédito?: PRONAF\")."
        )
        col_a, col_b = st.columns(2)
        for col, instance_key, slot_label in [(col_a, "ea", "Variável A"), (col_b, "eb", "Variável B")]:
            with col:
                st.markdown(f"**{slot_label}**")
                current = st.session_state.get(f"explorer_picked_{instance_key}")
                st.caption(current["label"] if current else "Nenhuma escolhida")
                if st.button(
                    "Trocar" if current else "Escolher",
                    icon=":material/edit:" if current else ":material/add_circle:",
                    key=f"open_explorer_{instance_key}",
                    use_container_width=True,
                ):
                    explorer_var_dialog(instance_key, slot_label)

    var_a = st.session_state.get("explorer_picked_ea")
    var_b = st.session_state.get("explorer_picked_eb")
    if not var_a or not var_b:
        st.info("Escolha as duas variáveis acima pra ver a comparação.")
        return

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


@st.cache_data(show_spinner="Calculando associações entre os fatores…")
def get_association_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Matriz de associação entre todos os 200+ fatores, calculada uma vez por
    combinação de filtros e reaproveitada — só recalcula quando os dados
    filtrados mudam (não a cada interação do usuário nesta aba)."""
    factors = build_factor_list()
    return compute_association_matrix(df, factors)


def render_factor_picker(factors: list[dict], sections: list[str], instance_key: str) -> dict | None:
    section = st.selectbox("Seção", ["(nenhuma)"] + sections, key=f"af_section_{instance_key}")
    if section == "(nenhuma)":
        return None
    section_factors = [f for f in factors if f["section"] == section]
    labels = [f["label"] for f in section_factors]
    by_label = dict(zip(labels, section_factors))
    label = st.selectbox("Fator", ["(nenhum)"] + labels, key=f"af_factor_{instance_key}_{section}")
    if label == "(nenhum)":
        return None
    return by_label[label]


def render_correlacoes_tab(df: pd.DataFrame, catalog: dict) -> None:
    render_section_header("Correlação e Associação entre Fatores", "link")
    st.caption(
        "Cada par de variáveis usa o método estatístico certo pro seu tipo — Pearson entre quantitativas, "
        "ponto-bisserial entre uma binária (Sim/Não) e uma quantitativa, Phi entre duas binárias, razão de "
        "correlação (η) entre uma categórica de 3+ níveis e uma quantitativa/binária, e Cramér's V entre "
        "duas categóricas de 3+ níveis. **Correlação/associação não implica causalidade** — um coeficiente "
        "alto não significa que um fator cause o outro, só que se movem juntos na amostra."
    )

    factors = build_factor_list()
    sections = [s for s in SECTION_ORDER if any(f["section"] == s for f in factors)]
    matrix = get_association_matrix(df)

    mode = st.segmented_control(
        "Modo de visualização",
        [":material/leaderboard: Analisar um fator", ":material/grid_on: Ver matriz completa"],
        default=":material/leaderboard: Analisar um fator",
        label_visibility="collapsed",
        key="assoc_mode",
    )

    label_of = {f["key"]: f["label"] for f in factors}
    section_of = {f["key"]: f["section"] for f in factors}

    if mode == ":material/grid_on: Ver matriz completa":
        render_association_matrix_view(matrix, factors, label_of)
        return

    @st.dialog("Selecionar fator", width="large", on_dismiss="rerun")
    def factor_dialog():
        st.caption("Escolha o fator principal — o sistema calcula a associação dele com todos os outros.")
        result = render_factor_picker(factors, sections, "main")
        st.markdown("")
        if st.button("Aplicar", icon=":material/check:", key="apply_factor", type="primary", use_container_width=True):
            st.session_state["assoc_picked_key"] = result["key"] if result else None
            st.rerun()

    picked_key = st.session_state.get("assoc_picked_key")
    col_current, col_btn = st.columns([4, 1])
    with col_current:
        if picked_key:
            st.markdown(f"**Fator selecionado:** {label_of.get(picked_key, picked_key)} · _{section_of.get(picked_key, '')}_")
        else:
            st.markdown("**Nenhum fator selecionado ainda.**")
    with col_btn:
        if st.button(
            "Trocar fator" if picked_key else "Selecionar fator",
            icon=":material/edit:" if picked_key else ":material/search:",
            key="open_factor_dialog",
            use_container_width=True,
        ):
            factor_dialog()

    if not picked_key:
        st.info("Selecione um fator acima pra ver com quais outros ele mais se associa.")
        return

    render_factor_analysis(matrix, picked_key, label_of, len(df))


def render_factor_analysis(matrix: pd.DataFrame, picked_key: str, label_of: dict, n_sample: int) -> None:
    ranking_full = factor_ranking(matrix, picked_key)
    ranking_full = ranking_full[ranking_full["other_key"].isin(label_of.keys())]

    render_section_header(f"Fatores relacionados a {label_of.get(picked_key, picked_key)}", "trending-up")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        show = c1.selectbox(
            "Mostrar",
            ["Todos", "Apenas positivas", "Apenas negativas", "Apenas fortes (|r| ≥ 0,60)", "Apenas significativas (p < 0,05)"],
            key="assoc_show_filter",
        )
        order_by = c2.selectbox(
            "Ordenar por",
            ["Maior associação", "Menor associação", "Menor p-valor"],
            key="assoc_order_by",
        )
        min_threshold = c3.slider("Limiar mínimo |r|/V/η", 0.0, 1.0, 0.0, 0.05, key="assoc_min_threshold")

    filtered = ranking_full.copy()
    filtered = filtered[filtered["value"].fillna(0) >= min_threshold]
    if show == "Apenas positivas":
        filtered = filtered[filtered["sign"] > 0]
    elif show == "Apenas negativas":
        filtered = filtered[filtered["sign"] < 0]
    elif show == "Apenas fortes (|r| ≥ 0,60)":
        filtered = filtered[filtered["value"].fillna(0) >= 0.60]
    elif show == "Apenas significativas (p < 0,05)":
        filtered = filtered[filtered["p_value"].fillna(1) < 0.05]

    if order_by == "Maior associação":
        filtered = filtered.sort_values("value", ascending=False, na_position="last")
    elif order_by == "Menor associação":
        filtered = filtered.sort_values("value", ascending=True, na_position="last")
    else:
        filtered = filtered.sort_values("p_value", ascending=True, na_position="last")

    if filtered.empty:
        st.warning("Nenhum fator atende esses filtros.")
        return

    MAX_BARS = 25
    for_chart = filtered.head(MAX_BARS)
    short_labels = []
    for k in for_chart["other_key"]:
        lbl = label_of.get(k, k)
        short_labels.append(lbl if len(lbl) <= 42 else lbl[:41].rstrip() + "…")

    with st.container(border=True):
        if len(filtered) > MAX_BARS:
            st.caption(f"Mostrando os {MAX_BARS} fatores mais fortes de {len(filtered)} que atendem os filtros — a tabela completa está abaixo.")
        fig = charts.factor_association_bar(for_chart, short_labels)
        st.plotly_chart(fig, use_container_width=True, key="assoc_bar")

    render_section_header("Tabela completa", "grid")
    with st.container(border=True):
        table = filtered.copy()
        table["Fator"] = table["other_key"].map(label_of)
        table["Coeficiente"] = table.apply(lambda r: r["r"] if pd.notna(r["r"]) else r["value"], axis=1)
        table["Sinal"] = table["sign"].map({1: "Positivo", -1: "Negativo", 0: "—"})
        table["Força"] = table["value"].apply(strength_label)
        table["p-valor"] = table["p_value"]
        table["N"] = table["n"]
        table["Método"] = table["method"]
        st.dataframe(
            table[["Fator", "Coeficiente", "Sinal", "Força", "Método", "p-valor", "N"]],
            use_container_width=True,
            height=min(480, 40 + 35 * len(table)),
            hide_index=True,
            column_config={
                "Coeficiente": st.column_config.NumberColumn(format="%.3f"),
                "p-valor": st.column_config.NumberColumn(format="%.3f"),
            },
        )
    st.caption(
        "Escala de força (valor absoluto): 0,00–0,19 muito fraca · 0,20–0,39 fraca · 0,40–0,59 moderada · "
        "0,60–0,79 forte · 0,80–1,00 muito forte. O sinal (+/-) só existe pra Pearson, ponto-bisserial e Phi — "
        "η e Cramér's V medem só magnitude, sem direção."
    )
    if n_sample < 30:
        st.caption(
            f":material/warning: Calculado sobre **{n_sample}** produtores — amostra pequena: força e "
            "significância (p-valor) devem ser lidas em conjunto, não isoladamente. Um coeficiente moderado "
            "com p-valor alto (ex: p > 0,05) não é uma evidência estatística confiável."
        )


def render_association_matrix_view(matrix: pd.DataFrame, factors: list[dict], label_of: dict) -> None:
    render_section_header("Matriz completa de associação", "grid")
    st.caption(
        "Magnitude da associação entre cada par de fatores (0 a 1, sem sinal — a matriz mistura métodos "
        "diferentes, e nem todos têm direção). Role e amplie pra explorar; passe o mouse pra ver o par "
        "completo e o valor exato."
    )
    keys = [f["key"] for f in factors]
    n = len(keys)
    idx = {k: i for i, k in enumerate(keys)}
    values = np.eye(n)
    valid = matrix.dropna(subset=["value"])
    ia = valid["key_a"].map(idx)
    ib = valid["key_b"].map(idx)
    keep = ia.notna() & ib.notna()
    ia = ia[keep].to_numpy(dtype=int)
    ib = ib[keep].to_numpy(dtype=int)
    vals = valid.loc[keep, "value"].to_numpy()
    values[ia, ib] = vals
    values[ib, ia] = vals
    labels = [label_of.get(k, k) for k in keys]
    wide = pd.DataFrame(values, index=labels, columns=labels)

    with st.container(border=True):
        height = max(700, 20 * n)
        st.plotly_chart(
            charts.full_association_heatmap(wide, height=height), use_container_width=True, key="assoc_full_heatmap"
        )


@st.fragment
def render_compare_tab(df: pd.DataFrame, catalog: dict) -> None:
    """Roda isolado do resto da página (fragmento): escolher/trocar variáveis aqui
    não reprocessa as outras 14 abas a cada clique, só este bloco."""
    compare_question_options = build_question_options(catalog, include_numeric=True)
    compare_sections = [s for s in SECTION_ORDER if any(q["section"] == s for q in compare_question_options)]

    MIN_COMPARE_VARS = 2
    MAX_COMPARE_VARS = 5
    if "n_compare_vars" not in st.session_state:
        st.session_state["n_compare_vars"] = MIN_COMPARE_VARS

    @st.dialog("Escolher variável", width="large", on_dismiss="rerun")
    def variable_picker_dialog(instance_key: str, slot_num: int):
        # Diálogo largo só pra não cortar o texto das perguntas — a mesma ideia do
        # filtro avançado: abre grande pra escolher com calma, fecha e volta ao
        # normal assim que a variável é confirmada.
        st.caption(f"Variável {slot_num} — Seção → Pergunta → Opção (se for de múltipla escolha)")
        result = render_variable_picker(compare_question_options, compare_sections, instance_key)
        st.markdown("")
        if st.button(
            "Aplicar", icon=":material/check:", key=f"apply_var_{instance_key}", type="primary", use_container_width=True
        ):
            # Guarda a escolha numa chave própria (não a do widget): o Streamlit
            # limpa o estado dos widgets do diálogo quando ele é reaberto pra outro
            # slot, então ler direto de cmp_section_* depois de fechado não é
            # confiável — só essa cópia sobrevive de forma garantida.
            st.session_state[f"compare_picked_{instance_key}"] = result
            st.rerun()

    with st.container(border=True):
        st.caption("Escolha de 2 a 5 variáveis pra comparar.")
        n_visible = st.session_state["n_compare_vars"]
        picked: list[dict] = []
        cols = st.columns(n_visible)
        for i in range(n_visible):
            instance_key = f"c{i}"
            with cols[i]:
                st.markdown(f"**Variável {i + 1}**")
                current = st.session_state.get(f"compare_picked_{instance_key}")
                st.caption(current["label"] if current else "Nenhuma escolhida")
                if current:
                    picked.append(current)
                btn_label = "Trocar" if current else "Escolher"
                btn_icon = ":material/edit:" if current else ":material/add_circle:"
                if st.button(btn_label, icon=btn_icon, key=f"open_var_{instance_key}", use_container_width=True):
                    variable_picker_dialog(instance_key, i + 1)

        if n_visible < MAX_COMPARE_VARS and st.button(
            "Adicionar variável", icon=":material/add:", key="add_compare_var"
        ):
            st.session_state["n_compare_vars"] += 1
            st.rerun(scope="fragment")

    seen_keys = set()
    chosen_vars = []
    for v in picked:
        if v["key"] not in seen_keys:
            seen_keys.add(v["key"])
            chosen_vars.append(v)
    if len(picked) != len(chosen_vars):
        st.warning("Uma variável repetida foi ignorada — escolha variáveis diferentes em cada campo.")

    if len(chosen_vars) < 2:
        st.info("Escolha pelo menos 2 variáveis pra ver a comparação.")
    else:
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
            st.caption(
                f"**Como ler:** cada faixa vertical é uma variável; cada linha colorida é um grupo de produtores "
                f"que segue o mesmo caminho entre as respostas. A espessura da linha mostra quantos produtores "
                f"seguem aquele caminho — passe o mouse pra ver o número exato. As cores seguem as categorias "
                f"de **{dim_labels[0]}** (1ª variável escolhida)."
            )
            fig, legend_items = charts.parallel_categories(df_multi, dim_cols, dim_labels)
            st.plotly_chart(fig, use_container_width=True, key="multi_parcats")
            render_color_legend(legend_items, title=f"{dim_labels[0]}:")
            if any(v["kind"] == "num" for v in chosen_vars):
                st.caption(
                    ":material/info: Variáveis numéricas são divididas em quartis da própria amostra filtrada "
                    "(25% mais baixo = \"Baixo\" ... 25% mais alto = \"Alto\") pra poder aparecer no gráfico — "
                    "não são faixas fixas definidas externamente."
                )
            if len(df_multi) < 15:
                st.caption(
                    f":material/warning: Amostra atual de **{len(df_multi)}** produtores — com poucos casos, cada "
                    "caminho no gráfico pode representar 1 ou 2 produtores; interprete padrões com cautela."
                )

        render_section_header("Tabela dos produtores filtrados", "grid")
        with st.container(border=True):
            st.caption("Cada linha é um produtor da amostra atual, com as respostas nas variáveis escolhidas.")
            table_df = df[[v["key"] for v in chosen_vars]].copy()
            table_df.columns = [v["label"] for v in chosen_vars]
            for v in chosen_vars:
                if v["kind"] == "flag":
                    table_df[v["label"]] = table_df[v["label"]].fillna("Não")
            st.dataframe(table_df, use_container_width=True, height=min(400, 40 + 35 * len(table_df)))


TOOL_OPTIONS = [
    ":material/search: Explorador",
    ":material/filter_alt: Comparação e Filtragem entre Parâmetros",
    ":material/link: Correlações",
]


@st.fragment
def render_main_nav(df: pd.DataFrame, catalog: dict, section_tabs: list[str]) -> None:
    """Um único fragmento cuida de toda a navegação principal: trocar de vista
    só reprocessa o que está aqui dentro, não a página inteira.

    Duas linhas separadas porque são dois tipos de navegação diferentes: uma
    pra percorrer as seções da própria pesquisa, outra pra ferramentas de
    análise cruzada (que não pertencem a nenhuma seção em particular)."""
    section_options = [":material/dashboard: Visão Geral"] + section_tabs

    if "active_nav_group" not in st.session_state:
        st.session_state["active_nav_group"] = "sections"
    if "nav_sections" not in st.session_state:
        st.session_state["nav_sections"] = section_options[0]

    def _use_sections():
        st.session_state["active_nav_group"] = "sections"
        st.session_state["nav_tools"] = None

    def _use_tools():
        st.session_state["active_nav_group"] = "tools"
        st.session_state["nav_sections"] = None

    st.caption("Seções da pesquisa")
    selected_section = st.segmented_control(
        "Seções da pesquisa",
        section_options,
        label_visibility="collapsed",
        key="nav_sections",
        on_change=_use_sections,
    )
    st.caption("Ferramentas de análise")
    selected_tool = st.segmented_control(
        "Ferramentas de análise",
        TOOL_OPTIONS,
        label_visibility="collapsed",
        key="nav_tools",
        on_change=_use_tools,
    )
    st.markdown("")

    if st.session_state["active_nav_group"] == "tools" and selected_tool:
        selected = selected_tool
    else:
        selected = selected_section or section_options[0]

    if selected == section_options[0]:
        render_visao_geral(catalog)
    elif selected in section_tabs:
        render_section(selected)
    elif selected == TOOL_OPTIONS[0]:
        render_explorador_tab(df, catalog)
    elif selected == TOOL_OPTIONS[1]:
        render_section_header("Comparação e Filtragem entre Parâmetros", "filter")
        render_compare_tab(df, catalog)
    elif selected == TOOL_OPTIONS[2]:
        render_correlacoes_tab(df, catalog)


render_main_nav(df, catalog, section_tabs)

render_footer()
