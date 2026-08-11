import plotly.graph_objects as go
import streamlit as st
from branding import COLOR_PRIMARY, COLOR_SECONDARY, render_footer, render_header
from data_loader import load_producers

render_header("Produtores PDPL")


def fmt_br(value: float, decimals: int = 1) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


try:
    df = load_producers()
except FileNotFoundError:
    st.info(
        "Este dashboard ainda não tem dados publicados neste ambiente — "
        "disponível apenas rodando localmente por enquanto."
    )
    render_footer()
    st.stop()

st.caption(f"Amostra de {len(df)} produtores entrevistados pelo PDPL/PCEPL-UFV.")

row1_col1, row1_col2 = st.columns(2)
row1_col1.metric("Produtores na amostra", len(df))
row1_col2.metric("Produção média", f"{fmt_br(df['producao_media_l_dia'].mean(), 0)} L/dia")

row2_col1, row2_col2 = st.columns(2)
row2_col1.metric("Produtividade média", f"{fmt_br(df['produtividade_media_l_vaca_dia'].mean())} L/vaca/dia")
row2_col2.metric("Área média p/ gado de leite", f"{fmt_br(df['area_gado_leite_ha'].mean())} ha")

st.markdown("### Perfil da amostra")
col_a, col_b = st.columns(2)

with col_a:
    counts = df["tipologia"].value_counts()
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.55,
            marker=dict(colors=[COLOR_PRIMARY, COLOR_SECONDARY]),
            textinfo="label+percent",
        )
    )
    fig.update_layout(title="Tipologia da produção", margin=dict(t=40, b=0, l=0, r=0), height=320)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    counts = df["sistema_producao"].value_counts()
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.55,
            marker=dict(colors=[COLOR_PRIMARY, COLOR_SECONDARY]),
            textinfo="label+percent",
        )
    )
    fig.update_layout(title="Sistema de produção", margin=dict(t=40, b=0, l=0, r=0), height=320)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Distribuição geográfica")
counts = df["municipio"].value_counts().sort_values(ascending=True)
fig = go.Figure(
    go.Bar(
        x=counts.values,
        y=counts.index,
        orientation="h",
        marker=dict(color=COLOR_PRIMARY),
        text=counts.values,
        textposition="outside",
    )
)
fig.update_layout(
    title="Produtores por município",
    margin=dict(t=40, b=0, l=0, r=20),
    height=420,
    xaxis=dict(title="Produtores", showgrid=False),
    yaxis=dict(title=""),
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Estrato de produção")
counts = df["estrato_producao"].value_counts().sort_index()
shades = ["#CFEAF0", "#9BD4DF", "#67BECC", "#3AA9BB", COLOR_PRIMARY]
fig = go.Figure(
    go.Bar(
        x=counts.index.astype(str),
        y=counts.values,
        marker=dict(color=shades),
        text=counts.values,
        textposition="outside",
    )
)
fig.update_layout(
    title="Produtores por estrato de produção (L/dia)",
    margin=dict(t=40, b=0, l=0, r=0),
    height=380,
    xaxis=dict(title=""),
    yaxis=dict(title="Produtores", showgrid=False),
)
st.plotly_chart(fig, use_container_width=True)

render_footer()
