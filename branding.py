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

# Ícones em linha (estilo Feather) usados nos cards de KPI e cabeçalhos de seção,
# no lugar de emoji — mais consistente e profissional num dashboard institucional.
# Cada valor é o conteúdo interno de um <svg>; a cor vem de "currentColor" (CSS).
ICONS = {
    "users": '<circle cx="9" cy="7" r="4"/><path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/>'
    '<circle cx="17" cy="7" r="3"/><path d="M21 21v-2a4 4 0 0 0-3-3.87"/>',
    "droplet": '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
    "trending-up": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "map": '<polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>'
    '<line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>'
    '<line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "tag": '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>'
    '<line x1="7" y1="7" x2="7.01" y2="7"/>',
    "sprout": '<path d="M12 22v-7"/><path d="M12 15c-4 0-7-3-7-7 4 0 7 3 7 7z"/>'
    '<path d="M12 15c4 0 7-3 7-7-4 0-7 3-7 7z"/>',
    "briefcase": '<rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>'
    '<path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "banknote": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/>'
    '<path d="M6 12h.01M18 12h.01"/>',
    "folder": '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
    "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "user": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "pie-chart": '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
    "check-square": '<polyline points="9 11 12 14 22 4"/>'
    '<path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    "bar-chart": '<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/>'
    '<line x1="6" y1="20" x2="6" y2="16"/>',
    "grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>'
    '<rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>',
    "filter": '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "link": '<path d="M15 7h3a5 5 0 0 1 5 5 5 5 0 0 1-5 5h-3m-6 0H6a5 5 0 0 1-5-5 5 5 0 0 1 5-5h3"/>'
    '<line x1="8" y1="12" x2="16" y2="12"/>',
}


def render_icon(name: str, size: int = 20) -> str:
    """SVG inline (string) pra embutir em HTML customizado — cor herda do
    elemento pai via currentColor, então basta definir `color` no CSS."""
    inner = ICONS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{inner}</svg>"
    )


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
            border-radius: 12px;
            padding: 1rem 1.1rem;
            border: 1px solid rgba(0,0,0,0.06);
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
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
        .kpi-card .kpi-icon-badge {{
            width: 34px;
            height: 34px;
            border-radius: 9px;
            background: rgba(28,156,180,0.10);
            color: {COLOR_PRIMARY};
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.6rem;
        }}

        /* Sidebar mais larga pra caber perguntas longas do filtro sem cortar —
           só quando expandida. Se forçarmos a largura também com a sidebar
           recolhida (aria-expanded="false"), o Streamlit desloca o conteúdo pra
           fora da tela mas a "fatia" no layout flex continua reservada, deixando
           um vão vazio e o dashboard desalinhado. */
        [data-testid="stSidebar"] {{
            background-color: white;
            border-right: 1px solid rgba(0,0,0,0.06);
        }}
        [data-testid="stSidebar"][aria-expanded="true"] {{
            min-width: 430px !important;
            max-width: 480px !important;
        }}
        [data-testid="stSidebar"][aria-expanded="false"] {{
            min-width: 0 !important;
            width: 0 !important;
        }}

        /* Cabeçalho de seção com barra de destaque */
        .section-header {{
            border-left: 5px solid {COLOR_PRIMARY};
            padding: 0.3rem 0 0.3rem 0.8rem;
            margin: 1.4rem 0 0.8rem 0;
            font-size: 1.05rem;
            font-weight: 700;
            color: {COLOR_TEXT};
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .section-header-icon {{
            display: inline-flex;
            color: {COLOR_PRIMARY};
            flex-shrink: 0;
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
            /* Com vários filtros o conteúdo pode passar da altura da tela — sem
               isso o botão "Aplicar e fechar" simplesmente some, sem como rolar
               até ele. */
            overflow-y: auto !important;
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
    """items: lista de (label, valor) ou (chave_do_icone, label, valor)."""
    cards = []
    for item in items:
        icon, label, value = ("", item[0], item[1]) if len(item) == 2 else item
        icon_html = f'<div class="kpi-icon-badge">{render_icon(icon, 18)}</div>' if icon else ""
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
    icon_html = f'<span class="section-header-icon">{render_icon(icon, 18)}</span>' if icon else ""
    st.markdown(f'<div class="section-header">{icon_html}{text}</div>', unsafe_allow_html=True)


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
