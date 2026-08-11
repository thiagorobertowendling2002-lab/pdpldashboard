from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "produtores_pdpl.xlsx"

# Colunas usadas no dashboard, selecionadas pela posição na planilha "DADOS 1"
# (evita depender da acentuação exata dos nomes originais das colunas).
_COLUMNS_BY_POSITION = {
    1: "municipio",
    2: "tipologia",
    3: "estrato_producao",
    5: "sistema_producao",
    107: "producao_media_l_dia",
    110: "produtividade_media_l_vaca_dia",
    118: "area_propria_total_ha",
    119: "area_gado_leite_ha",
}

_ESTRATO_ORDER = [
    "1) Até 200",
    "2) 201 a 500",
    "3) 501 a 1000",
    "4) 1001 a 2500",
    "5) Acima de 2501",
]


@st.cache_data
def load_producers() -> pd.DataFrame:
    raw = pd.read_excel(DATA_PATH, sheet_name="DADOS 1")
    positions = list(_COLUMNS_BY_POSITION.keys())
    df = raw.iloc[:, positions].copy()
    df.columns = list(_COLUMNS_BY_POSITION.values())

    df["estrato_producao"] = pd.Categorical(
        df["estrato_producao"], categories=_ESTRATO_ORDER, ordered=True
    )
    return df
