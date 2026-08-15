"""Motor de associação entre variáveis mistas (quantitativas, binárias e
categóricas com 3+ níveis). Cada par de fatores usa o método estatístico
correto pro tipo das duas variáveis, em vez de forçar Pearson em tudo:

- quantitativa × quantitativa              -> Pearson
- binária × quantitativa                   -> ponto-bisserial
- binária × binária                        -> Phi
- categórica (3+) × quantitativa ou binária -> razão de correlação (η)
- categórica (3+) × categórica (3+)         -> Cramér's V

Pearson/ponto-bisserial/Phi são, matematicamente, a mesma conta (Pearson
sobre as variáveis binárias codificadas 0/1) — por isso esse bloco inteiro
(quantitativas + binárias) é calculado de uma vez com `.corr()` vetorizado.
A razão de correlação (η) contra uma categórica também é calculada de uma
vez só por fator categórico (um groupby cobrindo todas as colunas
numéricas/binárias simultaneamente), em vez de par a par — só o bloco
categórica × categórica (bem menor) roda par a par. É isso que torna
viável ter 200+ fatores sem o cálculo levar dezenas de segundos.
"""

import numpy as np
import pandas as pd
from scipy import stats

STRENGTH_BINS = [
    (0.20, "Muito fraca"),
    (0.40, "Fraca"),
    (0.60, "Moderada"),
    (0.80, "Forte"),
    (1.01, "Muito forte"),
]


def strength_label(abs_value: float) -> str:
    if pd.isna(abs_value):
        return "—"
    for upper, label in STRENGTH_BINS:
        if abs_value < upper:
            return label
    return "Muito forte"


def _binary_levels(series: pd.Series) -> tuple[str, str] | None:
    """(rótulo do 0, rótulo do 1). "Não"/negativa vira 0; sem uma negativa
    clara, ordem alfabética decide (critério neutro e documentado)."""
    non_null = series.dropna().astype(str)
    levels = sorted(non_null.unique())
    if len(levels) != 2:
        return None
    a, b = levels
    a_neg = "não" in a.lower() or "nao" in a.lower()
    b_neg = "não" in b.lower() or "nao" in b.lower()
    if a_neg and not b_neg:
        return a, b
    if b_neg and not a_neg:
        return b, a
    return a, b


def _encode_binary(series: pd.Series, is_flag: bool) -> pd.Series:
    """Codifica uma variável de 2 níveis como 0/1. Itens de múltipla escolha
    (`is_flag=True`) ficam em branco quando NÃO marcados — isso é uma
    resposta "Não", não dado faltante, então preenchemos antes de olhar os
    níveis. Pra categóricas binárias "de verdade", NaN continua sendo dado
    faltante de fato e é excluído do par."""
    s = series.fillna("Não") if is_flag else series
    levels = _binary_levels(s)
    if levels is None:
        return pd.to_numeric(s, errors="coerce")
    zero, one = levels
    mapped = s.astype(str).map({zero: 0, one: 1})
    return mapped.where(s.notna())


def cramers_v(a: pd.Series, b: pd.Series) -> tuple[float, float, int]:
    """Cramér's V: associação entre duas variáveis categóricas com 3+
    níveis, baseada no qui-quadrado. Sem sinal — só magnitude."""
    paired = pd.DataFrame({"a": a.astype(str), "b": b.astype(str)}).dropna()
    n = len(paired)
    if n < 3:
        return float("nan"), float("nan"), n
    table = pd.crosstab(paired["a"], paired["b"])
    if table.shape[0] < 2 or table.shape[1] < 2:
        return float("nan"), float("nan"), n
    chi2, p, _, _ = stats.chi2_contingency(table)
    r, k = table.shape
    denom = min(r - 1, k - 1)
    if denom <= 0:
        return float("nan"), float("nan"), n
    v = (chi2 / n / denom) ** 0.5
    return v, p, n


def _method_label(vtype_a: str, vtype_b: str) -> str:
    types = {vtype_a, vtype_b}
    if types == {"numeric"}:
        return "Pearson"
    if types == {"numeric", "binary"}:
        return "Ponto-bisserial"
    if types == {"binary"}:
        return "Phi"
    return "?"


def _eta_block(df: pd.DataFrame, cat_key: str, encoded: pd.DataFrame) -> pd.DataFrame:
    """Razão de correlação (η) e p-valor (ANOVA) de UM fator categórico
    contra TODAS as colunas de `encoded` (numéricas/binárias já codificadas)
    de uma vez, via groupby vetorizado — em vez de um loop por coluna."""
    sub = encoded.copy()
    sub["__cat__"] = df[cat_key].astype(str).where(df[cat_key].notna())
    sub = sub.dropna(subset=["__cat__"])
    cols = [c for c in encoded.columns]

    grouped = sub.groupby("__cat__")
    group_means = grouped[cols].mean()
    group_counts = grouped[cols].count()
    overall_mean = sub[cols].mean()

    ss_between = ((group_means.sub(overall_mean, axis=1)) ** 2 * group_counts).sum(axis=0)
    ss_total = ((sub[cols].sub(overall_mean, axis=1)) ** 2).sum(axis=0)
    n_valid = sub[cols].notna().sum(axis=0)
    n_groups = group_counts.gt(0).sum(axis=0)

    with np.errstate(divide="ignore", invalid="ignore"):
        eta2 = ss_between / ss_total
        eta = np.sqrt(eta2)
        df_between = (n_groups - 1).clip(lower=0)
        df_within = (n_valid - n_groups).clip(lower=0)
        f_stat = (ss_between / df_between.replace(0, np.nan)) / ((ss_total - ss_between) / df_within.replace(0, np.nan))
        p_val = stats.f.sf(f_stat, df_between, df_within)

    p_val = pd.Series(p_val, index=cols)
    invalid = (n_valid < 3) | (n_groups < 2) | (ss_total <= 0)
    eta = eta.where(~invalid)
    p_val = p_val.where(~invalid)

    return pd.DataFrame({"key_b": cols, "value": eta.values, "p_value": p_val.values, "n": n_valid.values})


def compute_association_matrix(df: pd.DataFrame, factors: list[dict]) -> pd.DataFrame:
    """Devolve um DataFrame "longo": uma linha por par único de fatores, com
    coeficiente (com sinal quando fizer sentido), força, método, p-valor e N
    de observações válidas usadas nesse par especificamente (pairwise, sem
    descartar a linha inteira por causa de 1 variável vazia)."""
    numeric_binary = [f for f in factors if f["vtype"] in ("numeric", "binary")]
    categorical = [f for f in factors if f["vtype"] == "categorical"]

    encoded = pd.DataFrame(
        {
            f["key"]: (
                pd.to_numeric(df[f["key"]], errors="coerce")
                if f["vtype"] == "numeric"
                else _encode_binary(df[f["key"]], f.get("flag", False))
            )
            for f in numeric_binary
        }
    )
    keys = np.array(encoded.columns)
    vtype_of = {f["key"]: f["vtype"] for f in factors}

    corr = encoded.corr().to_numpy()
    valid = encoded.notna().to_numpy(dtype=float)
    n_matrix = valid.T @ valid

    iu = np.triu_indices(len(keys), k=1)
    r_arr = corr[iu]
    n_arr = n_matrix[iu]

    with np.errstate(divide="ignore", invalid="ignore"):
        t_arr = r_arr * np.sqrt((n_arr - 2) / (1 - r_arr**2))
        p_arr = 2 * stats.t.sf(np.abs(t_arr), df=np.maximum(n_arr - 2, 1))
    p_arr = np.where(n_arr < 3, np.nan, p_arr)

    key_a_arr = keys[iu[0]]
    key_b_arr = keys[iu[1]]
    sign_arr = np.where(np.isnan(r_arr), 0, np.sign(r_arr)).astype(int)
    method_arr = [_method_label(vtype_of[a], vtype_of[b]) for a, b in zip(key_a_arr, key_b_arr)]

    block1 = pd.DataFrame(
        {
            "key_a": key_a_arr,
            "key_b": key_b_arr,
            "r": r_arr,
            "value": np.abs(r_arr),
            "sign": sign_arr,
            "method": method_arr,
            "p_value": p_arr,
            "n": n_arr.astype(int),
        }
    )

    eta_parts = []
    for fa in categorical:
        eta_df = _eta_block(df, fa["key"], encoded)
        eta_df.insert(0, "key_a", fa["key"])
        eta_parts.append(eta_df)
    block2 = pd.concat(eta_parts, ignore_index=True) if eta_parts else pd.DataFrame(
        columns=["key_a", "key_b", "value", "p_value", "n"]
    )
    block2["r"] = float("nan")
    block2["sign"] = 0
    block2["method"] = "Razão de correlação (η)"

    rows = []
    for idx, fa in enumerate(categorical):
        for fb in categorical[idx + 1 :]:
            v, p, n = cramers_v(df[fa["key"]], df[fb["key"]])
            rows.append((fa["key"], fb["key"], float("nan"), v, 0, "Cramér's V", p, n))
    block3 = pd.DataFrame(rows, columns=["key_a", "key_b", "r", "value", "sign", "method", "p_value", "n"])

    result = pd.concat([block1, block2, block3], ignore_index=True)
    result["r"] = result["r"].clip(-1, 1)
    result["value"] = result["value"].clip(0, 1)
    return result


def factor_ranking(matrix: pd.DataFrame, key: str) -> pd.DataFrame:
    """Todas as associações envolvendo `key`, numa tabela de mão única
    (other_key no lugar de key_a/key_b), ordenada por força decrescente."""
    a_side = matrix[matrix["key_a"] == key].rename(columns={"key_b": "other_key"}).drop(columns=["key_a"])
    b_side = matrix[matrix["key_b"] == key].rename(columns={"key_a": "other_key"}).drop(columns=["key_b"])
    combined = pd.concat([a_side, b_side], ignore_index=True)
    return combined.sort_values("value", ascending=False, na_position="last").reset_index(drop=True)
