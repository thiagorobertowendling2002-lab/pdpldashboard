import base64
from pathlib import Path

import streamlit as st
from PIL import Image

APP_NAME = "PDPL - UFV"

HOMAGE_QUOTE = "O fácil já foi feito."
HOMAGE_AUTHOR = "GOMES, Sebastião Teixeira."

COLOR_PRIMARY = "#1C9CB4"  # teal do arco/logo PDPL
COLOR_SECONDARY = "#008448"  # verde do logo PDPL
COLOR_TEXT = "#181818"  # preto dos traços/texto do logo
COLOR_BG = "#F5F8F9"

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"


def _logo_b64() -> str:
    return base64.b64encode(LOGO_PATH.read_bytes()).decode()


def logo_data_uri() -> str:
    return f"data:image/png;base64,{_logo_b64()}"


def page_icon() -> Image.Image:
    return Image.open(LOGO_PATH)


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css?family=Poppins:300,400,500,700|Montserrat:500');

        html, body, [class*="css"] {{
            font-family: 'Poppins', sans-serif;
        }}
        .stApp {{
            background-color: {COLOR_BG};
        }}
        .block-container {{
            max-width: 99vw !important;
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
        }}
        [data-baseweb="select"] div {{
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: unset !important;
            font-size: 0.82rem !important;
        }}
        /* O controle do select é flex com altura fixa por padrão, então texto
           selecionado que quebra em várias linhas fica sobreposto ao próximo
           elemento em vez de empurrá-lo — forçamos altura automática em toda
           a cadeia de wrappers internos pra crescer junto com o texto. */
        [data-baseweb="select"], [data-baseweb="select"] > div, [data-baseweb="select"] > div > div {{
            height: auto !important;
            min-height: 38px !important;
        }}
        ul[data-testid="stSelectboxVirtualDropdown"] li div {{
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: unset !important;
            font-size: 0.8rem !important;
            line-height: 1.15 !important;
        }}
        h1, h2, h3, h4 {{
            color: {COLOR_TEXT} !important;
        }}
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button {{
            background-color: {COLOR_PRIMARY};
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
        }}
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {{
            background-color: {COLOR_SECONDARY};
            color: white;
        }}
        .brand-header {{
            background-color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            border-bottom: 4px solid {COLOR_PRIMARY};
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .brand-header img {{
            height: 56px;
        }}
        .brand-header h1 {{
            color: {COLOR_TEXT} !important;
            font-size: 1.4rem;
            margin: 0;
            font-family: 'Montserrat', sans-serif;
        }}
        .brand-header .accent {{
            color: {COLOR_SECONDARY};
        }}
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.75rem;
            margin-bottom: 1.25rem;
        }}
        .kpi-card {{
            background-color: white;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            border-top: 3px solid {COLOR_PRIMARY};
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        }}
        .kpi-card .kpi-label {{
            font-size: 0.78rem;
            color: {COLOR_TEXT};
            opacity: 0.65;
            margin: 0 0 4px 0;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }}
        .kpi-card .kpi-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {COLOR_TEXT};
            margin: 0;
            line-height: 1.2;
            word-break: break-word;
        }}
        .kpi-card .kpi-icon {{
            font-size: 1.3rem;
            margin-bottom: 2px;
        }}

        /* Sidebar mais larga pra caber perguntas longas do filtro sem cortar */
        [data-testid="stSidebar"] {{
            min-width: 430px !important;
            max-width: 480px !important;
            background-color: white;
            border-right: 1px solid rgba(0,0,0,0.06);
        }}

        /* Cabeçalho de seção com barra de destaque */
        .section-header {{
            border-left: 5px solid {COLOR_PRIMARY};
            padding: 0.3rem 0 0.3rem 0.8rem;
            margin: 1.4rem 0 0.8rem 0;
            font-size: 1.05rem;
            font-weight: 700;
            color: {COLOR_TEXT};
        }}

        /* Cada gráfico ganha um "cartão" branco com sombra sutil */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: white;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}

        /* Filtro avançado como painel lateral deslizante (evita o corte de texto
           que acontecia dentro da sidebar estreita) */
        div[data-testid="stDialog"] > div {{
            justify-content: flex-start !important;
        }}
        div[data-testid="stDialog"] [role="dialog"] {{
            width: 560px !important;
            max-width: 94vw !important;
            height: 100vh !important;
            max-height: 100vh !important;
            margin: 0 !important;
            border-radius: 0 18px 18px 0 !important;
            box-shadow: 8px 0 32px rgba(0,0,0,0.22);
            animation: pdplDrawerIn 0.32s cubic-bezier(0.22, 1, 0.36, 1);
        }}
        @keyframes pdplDrawerIn {{
            from {{ transform: translateX(-100%); opacity: 0.5; }}
            to   {{ transform: translateX(0); opacity: 1; }}
        }}

        /* Legenda de cores customizada (ex: gráfico de categorias paralelas) */
        .legend-row {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.5rem 1.1rem;
            padding: 0.3rem 0 0.6rem 0;
            font-size: 0.82rem;
            color: {COLOR_TEXT};
        }}
        .legend-title {{
            font-weight: 600;
            opacity: 0.75;
            margin-right: 0.2rem;
        }}
        .legend-swatch {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            white-space: nowrap;
        }}
        .legend-dot {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 3px;
            flex-shrink: 0;
        }}

        /* Abas com destaque mais forte na ativa */
        button[data-baseweb="tab"] {{
            font-weight: 600;
            font-size: 0.92rem;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {COLOR_PRIMARY} !important;
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: {COLOR_PRIMARY} !important;
            height: 3px !important;
        }}
        div[data-baseweb="tab-border"] {{
            background-color: rgba(0,0,0,0.08) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(items: list[tuple[str, str]] | list[tuple[str, str, str]]) -> None:
    """items: lista de (label, valor) ou (icone, label, valor) já formatados como texto."""
    cards = []
    for item in items:
        icon, label, value = ("", item[0], item[1]) if len(item) == 2 else item
        icon_html = f'<div class="kpi-icon">{icon}</div>' if icon else ""
        cards.append(f'<div class="kpi-card">{icon_html}<p class="kpi-label">{label}</p><p class="kpi-value">{value}</p></div>')
    st.markdown(f'<div class="kpi-row">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_color_legend(items: list[tuple[str, str]], title: str = "") -> None:
    """items: lista de (categoria, cor em hex). Usada onde o Plotly não dá pra
    desenhar uma legenda discreta nativa (ex: linha colorida do Parcats)."""
    title_html = f'<span class="legend-title">{title}</span>' if title else ""
    swatches = "".join(
        f'<span class="legend-swatch"><span class="legend-dot" style="background:{color}"></span>{label}</span>'
        for label, color in items
    )
    st.markdown(f'<div class="legend-row">{title_html}{swatches}</div>', unsafe_allow_html=True)


def render_section_header(text: str, icon: str = "") -> None:
    prefix = f"{icon} " if icon else ""
    st.markdown(f'<div class="section-header">{prefix}{text}</div>', unsafe_allow_html=True)


def render_header(subtitle: str | None = None) -> None:
    inject_css()
    title_html = APP_NAME
    if subtitle:
        title_html = f"{APP_NAME} <span class='accent'>·</span> {subtitle}"
    st.markdown(
        f"""
        <div class="brand-header">
            <img src="{logo_data_uri()}" alt="logo">
            <h1>{title_html}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quote() -> None:
    st.markdown(
        f"""
        <div style="border-left: 3px solid {COLOR_PRIMARY}; padding: 0.6rem 1rem; margin: 0 0 1.5rem 0; font-style: italic; color: {COLOR_TEXT};">
            "{HOMAGE_QUOTE}"
            <div style="text-align:right; font-style: normal; font-weight: 500; margin-top:4px; opacity:0.75;">— {HOMAGE_AUTHOR}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown("---")
    st.caption(f"{APP_NAME} — Universidade Federal de Viçosa")
