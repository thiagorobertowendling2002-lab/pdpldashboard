import re
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "produtores_pdpl.xlsx"

SECTION_NAMES = {
    "1": "Propriedade Rural",
    "2": "Perfil do Produtor e Renda",
    "3": "Motivação e Percepção",
    "4": "Crédito Rural",
    "5": "Produção e Rebanho",
    "6": "Ordenha e Infraestrutura",
    "7": "Gestão da Atividade",
    "8": "Assistência Técnica",
    "9": "Tecnologia e Conforto Animal",
    "10": "Manejo Reprodutivo e Sanitário",
    "11": "Comercialização",
}
SECTION_ORDER = ["Amostra"] + [SECTION_NAMES[k] for k in sorted(SECTION_NAMES, key=int)]

EXCLUDE_COLUMNS = {"Nome"}

# Colunas com prefixo numérico errado na planilha de origem (ex: "5.7.1." em
# perguntas de perfil pessoal do produtor, no meio do bloco "Produção e
# Rebanho"). Corrigidas aqui por texto exato em vez de editar a planilha
# confidencial, e sem mexer em `current_section` pra não afetar as colunas
# seguintes que legitimamente pertencem à seção original.
SECTION_OVERRIDES = {
    "5.7.1. Possui cônjuge ou companheiro(a)?": "Perfil do Produtor e Renda",
    "Tem filhos": "Perfil do Produtor e Renda",
    "Tem filhos que trabalham na propriedade rural": "Perfil do Produtor e Renda",
}


def _section_for(text: str, current: str) -> str:
    m = re.match(r"^(\d+)\.", text.strip())
    if m and m.group(1) in SECTION_NAMES:
        return SECTION_NAMES[m.group(1)]
    return current


_QUESTION_NUMBER_RE = re.compile(r"^\d+(\.\d+)*\.?\s")


def _is_numbered_question(text: str) -> bool:
    """Item de marcar/desmarcar de um grupo de múltipla escolha nunca tem
    numeração própria no cabeçalho (é só o texto da opção, ex: "PRONAF") — só
    uma pergunta nova de verdade começa com "N." ou "N.M." (ex: "9.3. Possui
    energia elétrica..."). Serve pra não confundir uma pergunta nova que por
    coincidência também só tem 1 valor único na amostra com um item do grupo
    de múltipla escolha anterior."""
    return bool(_QUESTION_NUMBER_RE.match(text.strip()))


def _clean_label(text: str) -> str:
    text = re.sub(r"^\d+(\.\d+)*\.?\s*", "", text.strip())
    text = text.strip()
    # sufixo ".1"/".2" que o pandas adiciona a nomes de coluna duplicados
    text = re.sub(r"\.\d+$", "", text)
    # sufixo "[Item específico]" (usado nas perguntas de benfeitorias) vira ": Item específico"
    m = re.search(r"\s*\[([^\[\]]+)\]\s*$", text)
    suffix = f": {m.group(1)}" if m else ""
    if m:
        text = text[: m.start()]
    text = re.sub(r"\s*\(Pode marcar[^()]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\(Marque[^()]*\)", "", text, flags=re.IGNORECASE)
    text = text.strip()
    if text.endswith(":"):
        text = text[:-1]
    text = text.strip()
    if text.isupper() and " " in text:
        text = text.capitalize()
    return (text + suffix).strip()


@st.cache_data
def load_raw() -> pd.DataFrame:
    df = pd.read_excel(DATA_PATH, sheet_name="DADOS 1")
    # A planilha de origem tem pelo menos um valor com espaço sobrando (ex:
    # "Guiricema " em Município) — sem isso, esse município aparece com um
    # espaço extra antes de "MG" no rótulo do Ranking e é um valor
    # tecnicamente diferente de uma futura linha "Guiricema" sem espaço no
    # filtro. Aplica só a colunas de texto; não mexe em valores numéricos
    # nem no agrupamento por vírgula das colunas de múltipla escolha.
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df


@st.cache_data
def build_catalog():
    """Classifica automaticamente as 323 colunas da planilha em grupos utilizáveis
    pelo dashboard: variáveis numéricas e categóricas avulsas, grupos de composição
    (colunas numéricas que somam um total, ex: % da área própria/arrendada) e grupos
    de múltipla escolha (perguntas "marque todas que se aplicam", reconstruídas a
    partir das colunas de flag Sim/NaN que a planilha gera para cada opção).
    """
    df = load_raw()

    numeric_vars: list[dict] = []
    categorical_vars: list[dict] = []
    numeric_groups: dict[str, dict] = {}
    multiselect_groups: dict[str, dict] = {}
    fun_facts: list[dict] = []

    current_section = "Amostra"
    active_ms_group: str | None = None

    for col in df.columns:
        text = str(col)
        if text in EXCLUDE_COLUMNS:
            continue

        current_section = _section_for(text, current_section)
        section = SECTION_OVERRIDES.get(text, current_section)

        s = df[col]
        non_null = s.dropna()

        if non_null.empty:
            continue

        nunique = non_null.nunique()
        is_numeric = pd.api.types.is_numeric_dtype(s)

        # Uma pergunta nova de verdade (numeração própria no cabeçalho) nunca é
        # item de um grupo de múltipla escolha anterior, mesmo com nunique <= 1.
        if active_ms_group is not None and _is_numbered_question(text):
            active_ms_group = None

        # Colunas numéricas com "prefixo: componente" pertencem a um grupo de
        # composição independentemente do nunique (mesmo se todo mundo respondeu o
        # mesmo valor, ex: 0% — o grupo inteiro precisa desse componente pra somar).
        if is_numeric and ": " in text:
            active_ms_group = None
            prefix, _, suffix = text.rpartition(": ")
            prefix_label = _clean_label(prefix)
            comp_label = re.sub(r"\s*\(%\)\s*$", "", suffix.strip())
            is_percent = suffix.strip().endswith("(%)")
            group_key = f"{section}||{prefix_label}"
            numeric_groups.setdefault(
                group_key,
                {"section": section, "label": prefix_label, "is_percent": is_percent, "items": []},
            )
            numeric_groups[group_key]["items"].append((comp_label, col))
            continue

        if nunique <= 1 and active_ms_group is not None:
            multiselect_groups[active_ms_group]["items"].append((_clean_label(text), col))
            continue

        if nunique <= 1:
            active_ms_group = None
            fun_facts.append(
                {
                    "section": section,
                    "label": _clean_label(text),
                    "value": str(non_null.iloc[0]),
                    "count": len(non_null),
                }
            )
            continue

        # nunique > 1: nova pergunta/cabeçalho -> fecha qualquer grupo multi-seleção aberto
        active_ms_group = None

        is_multiselect = non_null.astype(str).str.contains(", ").any()
        if is_multiselect:
            label = _clean_label(text)
            active_ms_group = f"{section}||{label}"
            multiselect_groups[active_ms_group] = {
                "section": section,
                "label": label,
                "items": [],
            }
            continue

        if is_numeric:
            unit = ""
            m = re.search(r"\(([^()]+)\)\s*$", text)
            if m:
                unit = m.group(1)
            numeric_vars.append({"key": col, "label": _clean_label(text), "section": section, "unit": unit})
        else:
            categorical_vars.append({"key": col, "label": _clean_label(text), "section": section})

    numeric_groups = {k: v for k, v in numeric_groups.items() if len(v["items"]) >= 2}
    multiselect_groups = {k: v for k, v in multiselect_groups.items() if len(v["items"]) >= 1}

    return {
        "numeric_vars": numeric_vars,
        "categorical_vars": categorical_vars,
        "numeric_groups": numeric_groups,
        "multiselect_groups": multiselect_groups,
        "fun_facts": fun_facts,
    }


@st.cache_data
def build_factor_list() -> list[dict]:
    """Lista unificada de "fatores" pra análise de associação: cada variável
    numérica, cada categórica (binária ou com 3+ níveis) e cada item Sim/Não
    de múltipla escolha vira um fator comparável com os demais. `vtype` é
    "numeric", "binary" ou "categorical"."""
    catalog = build_catalog()
    raw = load_raw()
    factors: list[dict] = []
    for v in catalog["numeric_vars"]:
        factors.append({"key": v["key"], "label": v["label"], "section": v["section"], "vtype": "numeric", "flag": False})
    for v in catalog["categorical_vars"]:
        nunique = raw[v["key"]].dropna().nunique()
        vtype = "binary" if nunique == 2 else "categorical"
        factors.append({"key": v["key"], "label": v["label"], "section": v["section"], "vtype": vtype, "flag": False})
    for g in catalog["multiselect_groups"].values():
        for opt_label, col in g["items"]:
            # Colunas de item de múltipla escolha marcam "Sim" quando selecionado e
            # ficam em branco (NaN) quando não — o branco é uma resposta "Não", não
            # dado faltante de verdade. `flag=True` avisa o motor de associação pra
            # tratar NaN como "Não" em vez de excluir a linha dessa comparação.
            factors.append(
                {"key": col, "label": f"{g['label']}: {opt_label}", "section": g["section"], "vtype": "binary", "flag": True}
            )
    return factors


FILTER_COLUMNS = {
    "municipio": "Município",
    "tipologia": "TIPOLOGIA DA PRODUÇÃO DE LEITE",
    "estrato_producao": "ESTRATO DE PRODUÇÃO (L/DIA)",
    "sistema_producao": "1.5. Sistema de produção de leite cru?",
}

ESTRATO_ORDER = ["1) Até 200", "2) 201 a 500", "3) 501 a 1000", "4) 1001 a 2500", "5) Acima de 2501"]


def filter_options() -> dict[str, list[str]]:
    df = load_raw()
    options = {}
    for key, col in FILTER_COLUMNS.items():
        values = df[col].dropna().unique().tolist()
        if key == "estrato_producao":
            values = [v for v in ESTRATO_ORDER if v in values]
        else:
            values = sorted(values)
        options[key] = values
    return options


def apply_filters(df: pd.DataFrame, selections: dict[str, list[str]]) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for key, selected in selections.items():
        col = FILTER_COLUMNS[key]
        options = filter_options()[key]
        if selected and set(selected) != set(options):
            mask &= df[col].isin(selected)
    return df[mask]
