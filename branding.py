import base64
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

APP_NAME = "PDPL - UFV"

HOMAGE_QUOTE = "O fácil já foi feito."
HOMAGE_AUTHOR = "GOMES, Sebastião Teixeira."

COLOR_PRIMARY = "#1C9CB4"  # teal do arco/logo PDPL
# Mesmo matiz do COLOR_PRIMARY mas escurecido: texto branco sobre COLOR_PRIMARY
# dá só 3.25:1 de contraste (abaixo do mínimo AA de 4.5:1) — usado só onde tem
# texto/ícone branco por cima (fundo de botão, aba ativa), nunca como acento
# decorativo puro (onde COLOR_PRIMARY original continua valendo).
COLOR_PRIMARY_ACCESSIBLE = "#157B8F"
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


def _pictogram_cow_svg(color: str, size: int) -> str:
    """Cabeça de vaca em silhueta sólida (preenchida, não outline como os ICONS
    normais) — usada repetida em massa nos pictogramas tipo isotype, uma por
    unidade da amostra."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" style="flex-shrink:0;">'
        f'<ellipse cx="4.6" cy="9" rx="2.6" ry="3.6" transform="rotate(-28 4.6 9)" fill="{color}"/>'
        f'<ellipse cx="19.4" cy="9" rx="2.6" ry="3.6" transform="rotate(28 19.4 9)" fill="{color}"/>'
        f'<ellipse cx="12" cy="10.5" rx="6.4" ry="5.6" fill="{color}"/>'
        f'<ellipse cx="12" cy="17" rx="7.6" ry="4.8" fill="{color}"/>'
        f'<ellipse cx="9.3" cy="17.3" rx="1.05" ry="1.4" fill="white" opacity="0.88"/>'
        f'<ellipse cx="14.7" cy="17.3" rx="1.05" ry="1.4" fill="white" opacity="0.88"/>'
        "</svg>"
    )


def _largest_remainder_pct(raw_counts: list[int], total: int) -> list[int]:
    """Converte contagens em porcentagens inteiras que somam exatamente 100
    (método dos maiores restos) — pra sempre desenhar 100 ícones no total,
    independente de N variar conforme os filtros aplicados."""
    exact = [c * 100 / total for c in raw_counts]
    floors = [int(x) for x in exact]
    leftover = 100 - sum(floors)
    order = sorted(range(len(raw_counts)), key=lambda i: exact[i] - floors[i], reverse=True)
    for i in order[:leftover]:
        floors[i] += 1
    return floors


def render_pictogram(counts: pd.Series, category_order: list[str], colors: list[str], icon_size: int = 24) -> None:
    """Pictograma tipo isotype no formato de porcentagem (sempre 100 ícones ao
    todo, 1 ícone = 1%, como os infográficos do IBGE) — cada categoria vira um
    bloco de vaquinhas coloridas na ordem lógica da variável (não por
    frequência), com os rótulos de porcentagem posicionados ao redor do
    pictograma (alternando esquerda/direita), alinhados na altura do bloco de
    cor correspondente — igual ao layout de referência do IBGE, em vez de uma
    legenda solta embaixo."""
    ordered = [(cat, int(counts[cat])) for cat in category_order if cat in counts.index and counts[cat] > 0]
    total = sum(n for _, n in ordered)
    if total == 0:
        return
    pcts = _largest_remainder_pct([n for _, n in ordered], total)

    per_row = 10
    gap = 3
    cell = icon_size + gap
    grid_w = cell * per_row - gap
    grid_h = cell * ((100 + per_row - 1) // per_row) - gap
    label_w = 132

    icons_html = "".join(_pictogram_cow_svg(color, icon_size) * pct for pct, color in zip(pcts, colors))
    grid_html = (
        f'<div style="display:grid;grid-template-columns:repeat({per_row}, {icon_size}px);gap:{gap}px;">'
        f"{icons_html}</div>"
    )

    left_labels, right_labels = [], []
    cursor = 0
    for idx, ((cat, n), pct, color) in enumerate(zip(ordered, pcts, colors)):
        mid_row = (cursor + pct / 2) / per_row
        cursor += pct
        top_px = max(0, mid_row * cell - 15)
        clean_label = re.sub(r"^\d+\)\s*", "", cat)
        is_left = idx % 2 == 0
        align_style = "right:0;text-align:right;" if is_left else "left:0;text-align:left;"
        label_html = (
            f'<div style="position:absolute;top:{top_px:.0f}px;{align_style}width:{label_w}px;font-size:0.76rem;'
            f'line-height:1.2;color:{color};">'
            f'<span style="font-weight:700;font-size:1.05rem;color:{color};">{pct}%</span><br>{clean_label}'
            "</div>"
        )
        (left_labels if is_left else right_labels).append(label_html)

    left_html = f'<div style="position:relative;">{"".join(left_labels)}</div>'
    right_html = f'<div style="position:relative;">{"".join(right_labels)}</div>'

    st.markdown(
        f'<div style="display:grid;grid-template-columns:{label_w}px {grid_w}px {label_w}px;'
        f'column-gap:16px;align-items:start;width:fit-content;margin:0.4rem auto 0.9rem auto;'
        f'min-height:{grid_h}px;">'
        f"{left_html}{grid_html}{right_html}</div>",
        unsafe_allow_html=True,
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
            background-color: {COLOR_PRIMARY_ACCESSIBLE};
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
        }}
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {{
            background-color: {COLOR_SECONDARY};
            color: white;
        }}
        /* Botão fechar (X) dos diálogos: ícone de 10px num alvo clicável de só
           24x24 — abaixo do mínimo de 44x44 recomendado (WCAG 2.5.5). Aumenta
           a área clicável via padding sem mudar o tamanho visual do ícone.
           Posição também é forçada explicitamente (canto superior direito do
           painel de 560px) — sem isso ele pode ficar ancorado num ancestral
           errado e flutuar longe do painel em telas largas. */
        div[data-testid="stDialog"] button[aria-label="Close"] {{
            width: 44px !important;
            height: 44px !important;
            position: absolute !important;
            top: 14px !important;
            right: 14px !important;
            left: auto !important;
        }}
        .brand-header {{
            position: relative;
            overflow: hidden;
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
        /* Grade sutil desvanecendo do centro pra fora, só decorativa (atrás do
           logo/título) — por isso fica num ::before isolado com z-index abaixo
           do conteúdo, em vez de background direto no .brand-header. */
        .brand-header::before {{
            content: "";
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(to right, rgba(79,79,79,0.18) 2px, transparent 2px),
                linear-gradient(to bottom, rgba(79,79,79,0.18) 1px, transparent 1px);
            background-size: 14px 24px;
            -webkit-mask-image: radial-gradient(ellipse 80% 50% at 50% 0%, #000 70%, transparent 110%);
            mask-image: radial-gradient(ellipse 80% 50% at 50% 0%, #000 70%, transparent 110%);
            pointer-events: none;
        }}
        .brand-header img, .brand-header h1 {{
            position: relative;
            z-index: 1;
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
        /* 5 colunas fixas (10 cards = 2 linhas parelhas) em vez de auto-fit —
           auto-fit recalculava quantas cabiam pela largura disponível, o que
           dava linhas desiguais (6+4, 7+3...) e mudava toda vez que a sidebar
           era recolhida/expandida. */
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 0.75rem;
            margin-bottom: 1.25rem;
        }}
        @media (max-width: 900px) {{
            .kpi-row {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        /* Navegação "Seções da pesquisa" (12 botões): mesmo raciocínio do
           .kpi-row acima — sem isso o segmented_control nativo quebra linha por
           largura disponível (flex-wrap), o que dava 8 em cima / 4 embaixo e
           mudava conforme a sidebar era aberta/fechada. Grid fixo de 6 colunas
           força sempre 6+6; `.st-key-nav_sections` é a classe que o Streamlit
           gera a partir do `key="nav_sections"` do widget, então só afeta esse
           segmented_control (não o de "Ferramentas de análise", que tem só 3
           opções e não precisa disso). */
        .st-key-nav_sections div[role="radiogroup"] {{
            display: grid !important;
            grid-template-columns: repeat(6, 1fr) !important;
            gap: 0.4rem !important;
        }}
        .st-key-nav_sections div[role="radiogroup"] button {{
            width: 100% !important;
            height: auto !important;
            min-height: 38px !important;
        }}
        /* Largura da coluna corta os rótulos mais longos ("Tecnologia e
           Conforto Animal", "Manejo Reprodutivo e Sanitário") com reticências
           por padrão — permite quebrar em 2 linhas em vez de truncar. */
        .st-key-nav_sections div[role="radiogroup"] button p {{
            white-space: normal !important;
            line-height: 1.2 !important;
        }}
        @media (max-width: 900px) {{
            .st-key-nav_sections div[role="radiogroup"] {{
                grid-template-columns: repeat(4, 1fr) !important;
            }}
        }}
        .kpi-card {{
            background-color: white;
            border-radius: 12px;
            padding: 1rem 1.1rem;
            border: 1px solid rgba(0,0,0,0.06);
            border-top: 3px solid {COLOR_PRIMARY_ACCESSIBLE};
            box-shadow: 0 3px 10px rgba(15,60,70,0.08);
        }}
        .kpi-card .kpi-label {{
            font-size: 0.78rem;
            line-height: 1.25;
            font-weight: 700;
            /* Reserva altura de 2 linhas sempre, mesmo quando o rótulo cabe em
               1 — sem isso, a linha de cards com um rótulo mais longo (ex:
               "Produtividade da mão de obra") ficava ~38% mais alta que a
               outra linha, já que todo card na mesma linha do grid estica
               junto (align-items:stretch) até o mais alto dela. */
            min-height: 1.95rem;
            color: {COLOR_PRIMARY_ACCESSIBLE};
            margin: 0 0 4px 0;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .kpi-card .kpi-value {{
            font-size: 1.55rem;
            font-weight: 700;
            color: {COLOR_TEXT};
            margin: 0;
            line-height: 1.2;
            white-space: nowrap;
            word-break: break-word;
        }}
        .kpi-card .kpi-icon-badge {{
            width: 34px;
            height: 34px;
            border-radius: 9px;
            background: {COLOR_PRIMARY_ACCESSIBLE};
            color: white;
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
            /* Fundo do resto da tela (fora do painel de 560px, em qualquer
               diálogo — Filtro avançado, Explorador, Comparação, Correlações,
               que compartilham esse mesmo CSS): véu translúcido — dá pra ver
               o dashboard por trás (dimmed), mas não dá pra ler o texto. O
               painel branco em si (regra abaixo) continua 100% sólido. */
            background: rgba(10, 30, 35, 0.6) !important;
        }}
        div[data-testid="stDialog"] [role="dialog"] {{
            position: relative !important;
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

        /* Botão ativo do segmented_control (seções/ferramentas de navegação):
           o padrão do tema (fundo teal bem diluído + texto teal) mede só
           2.75:1 de contraste — abaixo do mínimo AA de 4.5:1 — e além disso é
           uma pista visual fraca (fácil de não notar qual está selecionado
           entre várias opções do mesmo tamanho). Fundo sólido resolve os dois
           problemas de uma vez. */
        button[data-testid="stBaseButton-segmented_controlActive"] {{
            background-color: {COLOR_PRIMARY_ACCESSIBLE} !important;
            color: white !important;
        }}
        button[data-testid="stBaseButton-segmented_controlActive"] span[data-testid="stIconMaterial"] {{
            color: white !important;
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
