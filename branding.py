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
    unidade da amostra. width/height em 100% (não em px fixo) de propósito:
    o tamanho de verdade vem da célula do grid que envolve cada ícone, então
    o mesmo SVG serve pro grid de largura fixa (desktop) e pro de "1fr"
    (celular) sem duplicar nada — só encolhe junto com a célula."""
    return (
        f'<svg width="100%" height="100%" viewBox="0 0 24 24" '
        f'style="display:block;max-width:{size}px;max-height:{size}px;">'
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


def render_login_background() -> None:
    """Fundo em gradiente radial (teal -> branco -> verde, cores da marca)
    com um leve desfoque, só na tela de login — injetado à parte de
    `inject_css()` (CSS compartilhado com o dashboard) pra não vazar pra lá."""
    st.markdown(
        """
        <style>
        /* Direto no background do .stApp (não um ::before com position:fixed
           + z-index negativo) — essa combinação escapa do stacking context
           do elemento e disputa posição lá no nível raiz da página, e nos
           testes acabava cobrindo o conteúdo real por cima. Background puro
           nunca tem esse problema: sempre pinta atrás do conteúdo, garantido
           pela própria definição da propriedade. */
        .stApp {
            background-image: radial-gradient(circle at bottom, #2d788b 12%, #ffffff 43%, #2f6f42 97%);
            background-attachment: fixed;
            background-size: cover;
        }
        /* Antes do login não tem por que expor a navegação (nomes dos
           dashboards sigilosos) pra quem ainda não autenticou — esconde a
           sidebar inteira e o botão de recolher/expandir dela. */
        [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    clean_labels = [re.sub(r"^\d+\)\s*", "", cat) for cat, _ in ordered]
    # Resumo textual pro leitor de tela — os rótulos ao redor/na legenda já
    # são texto real, mas cada um sozinho não diz o total; isso junta tudo
    # numa única frase, igual o card de KPI faz com rótulo+valor.
    aria_summary = "; ".join(f"{lbl}: {pct}%" for lbl, pct in zip(clean_labels, pcts))

    per_row = 10
    gap = 3
    cell = icon_size + gap
    grid_w = cell * per_row - gap
    grid_h = cell * ((100 + per_row - 1) // per_row) - gap
    label_w = 132

    icons_html = "".join(_pictogram_cow_svg(color, icon_size) * pct for pct, color in zip(pcts, colors))
    # aria-hidden: as 100 vaquinhas repetidas são só decoração do percentual
    # já anunciado pelo aria-label do wrapper — sem isso um leitor de tela
    # tenta descrever cada uma das 100 (ou passar por 100 nós sem nome).
    grid_html = (
        f'<div aria-hidden="true" style="display:grid;grid-template-columns:repeat({per_row}, {icon_size}px);gap:{gap}px;">'
        f"{icons_html}</div>"
    )

    left_labels, right_labels = [], []
    cursor = 0
    for idx, ((cat, n), pct, color, clean_label) in enumerate(zip(ordered, pcts, colors, clean_labels)):
        mid_row = (cursor + pct / 2) / per_row
        cursor += pct
        top_px = max(0, mid_row * cell - 15)
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
    around_width = label_w * 2 + grid_w + 32

    # Legenda "ao redor" (estilo IBGE) precisa de ~560px de largura pra caber
    # rótulo + grid + rótulo lado a lado — não cabe numa tela de celular (nem
    # numa metade de card num tablet com a sidebar aberta). Gera as duas
    # versões e deixa o @container escolher: célula larga mostra a de
    # relance ao redor, célula estreita esconde ela e mostra a versão
    # empilhada (grid centralizado + legenda simples embaixo) em vez de
    # espremer/cortar a de relance.
    stacked_legend_items = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:0.35rem;font-size:0.78rem;'
        f'color:{COLOR_TEXT};white-space:nowrap;">'
        f'<span style="width:10px;height:10px;border-radius:3px;background:{color};flex-shrink:0;"></span>'
        f"{clean_label} — {pct}%</span>"
        for clean_label, pct, color in zip(clean_labels, pcts, colors)
    )

    st.markdown(
        f'<div class="pictogram-wrap" role="img" aria-label="{aria_summary}" '
        f'style="container-type:inline-size;margin:0.4rem 0 0.9rem 0;">'
        f'<div class="pictogram-around" style="display:grid;'
        f"grid-template-columns:{label_w}px {grid_w}px {label_w}px;"
        f'column-gap:16px;align-items:start;width:{around_width}px;max-width:100%;margin:0 auto;'
        f'min-height:{grid_h}px;">'
        f"{left_html}{grid_html}{right_html}</div>"
        f'<div class="pictogram-stacked" style="display:none;flex-direction:column;align-items:center;gap:0.6rem;">'
        f'<div aria-hidden="true" style="display:grid;grid-template-columns:repeat({per_row}, 1fr);gap:{gap}px;'
        f"max-width:{grid_w}px;width:100%;\">{icons_html}</div>"
        f'<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:0.3rem 0.7rem;">'
        f"{stacked_legend_items}</div></div></div>"
        f"<style>"
        f"@container (max-width: {around_width - 1}px) {{"
        f" .pictogram-around {{ display: none !important; }}"
        f" .pictogram-stacked {{ display: flex !important; }}"
        f"}}"
        f"</style>",
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
        /* Mesmo gradiente da tela de login (teal -> branco -> verde, cores da
           marca), estendido pro dashboard depois de autenticar — fixo em
           relação à janela (não rola junto com o conteúdo), então uma
           página comprida não repete nem corta o gradiente no meio. */
        .stApp {{
            background-image: radial-gradient(circle at bottom, #2d788b 12%, #ffffff 43%, #2f6f42 97%);
            background-attachment: fixed;
            background-size: cover;
        }}
        .block-container {{
            max-width: 99vw !important;
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
            /* Container query em vez de media query pro grid de navegação
               abaixo — o que importa é o espaço real disponível AQUI (que
               muda com a sidebar aberta/fechada), não a largura da janela
               toda, que é o que uma @media mede. */
            container-type: inline-size;
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
            min-height: 44px !important;
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
            min-height: 44px;
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
        @container (max-width: 900px) {{
            .kpi-row {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        /* Navegação "Seções da pesquisa" (12 botões) e "Ferramentas de
           análise" (4 botões): mesmo raciocínio do .kpi-row acima — sem isso
           o segmented_control nativo quebra linha por largura disponível
           (flex-wrap), o que dava contagens desiguais por linha e mudava
           conforme a sidebar era aberta/fechada. Grid fixo força sempre a
           mesma contagem de colunas por fileira nas duas navegações — ambas
           usam o mesmo widget lado a lado, então precisam do mesmo
           tratamento pra não destoar uma da outra (uma em grid compacto, a
           outra empilhada em 1 coluna). `.st-key-nav_sections`/`nav_tools`
           são as classes que o Streamlit gera a partir do `key=` do widget. */
        .st-key-nav_sections div[role="radiogroup"],
        .st-key-nav_tools div[role="radiogroup"] {{
            display: grid !important;
            gap: 0.4rem !important;
        }}
        .st-key-nav_sections div[role="radiogroup"] {{
            grid-template-columns: repeat(6, 1fr) !important;
        }}
        .st-key-nav_tools div[role="radiogroup"] {{
            grid-template-columns: repeat(4, 1fr) !important;
        }}
        .st-key-nav_sections div[role="radiogroup"] button,
        .st-key-nav_tools div[role="radiogroup"] button {{
            width: 100% !important;
            height: auto !important;
            min-height: 44px !important;
        }}
        /* Largura da coluna corta os rótulos mais longos ("Tecnologia e
           Conforto Animal", "Comparação e Filtragem entre Parâmetros") com
           reticências por padrão — permite quebrar em 2 linhas em vez de
           truncar. */
        .st-key-nav_sections div[role="radiogroup"] button p,
        .st-key-nav_tools div[role="radiogroup"] button p {{
            white-space: normal !important;
            line-height: 1.2 !important;
        }}
        /* 3 níveis em vez de 1 — uma @media(900px) sozinha não sabia que a
           sidebar aberta já come 430-480px do espaço real, então em 900px de
           janela com a sidebar expandida ainda tentava caber 4 colunas em
           ~450px de conteúdo de verdade, quebrando palavra no meio
           ("Infraestrutu-ra") sem hífen. @container mede o espaço real. */
        @container (max-width: 1000px) {{
            .st-key-nav_sections div[role="radiogroup"] {{
                grid-template-columns: repeat(4, 1fr) !important;
            }}
        }}
        @container (max-width: 700px) {{
            .st-key-nav_sections div[role="radiogroup"] {{
                grid-template-columns: repeat(3, 1fr) !important;
            }}
            .st-key-nav_tools div[role="radiogroup"] {{
                grid-template-columns: repeat(2, 1fr) !important;
            }}
        }}
        @container (max-width: 480px) {{
            .st-key-nav_sections div[role="radiogroup"] {{
                grid-template-columns: repeat(2, 1fr) !important;
            }}
            .st-key-nav_tools div[role="radiogroup"] {{
                grid-template-columns: repeat(1, 1fr) !important;
            }}
        }}
        /* Mesmo movimento de hover dos cards de KPI (leve elevação + sombra),
           só a transição — sem tint de cor nem trocar a cor que os botões já
           têm (branco / teal na aba ativa continuam do jeito que estão). */
        .st-key-nav_sections div[role="radiogroup"] button,
        .st-key-nav_tools div[role="radiogroup"] button {{
            transition: transform 180ms ease, box-shadow 180ms ease;
        }}
        @media (hover: hover) and (pointer: fine) {{
            .st-key-nav_sections div[role="radiogroup"] button:hover,
            .st-key-nav_tools div[role="radiogroup"] button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 14px -6px rgba(15,60,70,0.25);
            }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            .st-key-nav_sections div[role="radiogroup"] button:hover,
            .st-key-nav_tools div[role="radiogroup"] button:hover {{
                transform: none;
            }}
        }}
        /* Cada card define sua cor de destaque via --accent (uma por categoria,
           ver _KPI_CATEGORY_COLORS em render_kpi_row) — usada no tint estático,
           no glow de hover, na linha de acento e no badge do ícone, tudo com
           color-mix() em vez de repetir a mesma cor em rgba() fixo. */
        .kpi-card {{
            position: relative;
            overflow: hidden;
            background-color: white;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            border: 1px solid rgba(0,0,0,0.07);
            box-shadow: 0 2px 8px rgba(15,60,70,0.05);
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
        }}
        /* Tint estático (sempre visível, bem sutil) + glow que intensifica no
           hover — duas camadas, mesma origem, só a opacidade muda. */
        .kpi-card::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(ellipse at 18% 18%, var(--accent) 0%, transparent 65%);
            opacity: 0.05;
            transition: opacity 180ms ease;
            pointer-events: none;
        }}
        @media (hover: hover) and (pointer: fine) {{
            .kpi-card:hover {{
                transform: perspective(700px) rotateX(-2deg) rotateY(2deg) translateY(-2px);
                border-color: color-mix(in srgb, var(--accent) 35%, rgba(0,0,0,0.07));
                box-shadow: 0 10px 20px -10px color-mix(in srgb, var(--accent) 45%, transparent);
            }}
            .kpi-card:hover::before {{
                opacity: 0.14;
            }}
            .kpi-card:hover .kpi-accent-line {{
                width: 100%;
            }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            .kpi-card {{
                transition: box-shadow 180ms ease, border-color 180ms ease;
            }}
            .kpi-card:hover {{
                transform: none;
            }}
        }}
        .kpi-card .kpi-accent-line {{
            position: absolute;
            bottom: 0;
            left: 0;
            height: 2px;
            width: 0;
            background: linear-gradient(to right, var(--accent), transparent);
            transition: width 300ms ease;
        }}
        .kpi-card .kpi-label {{
            position: relative;
            font-size: 0.78rem;
            line-height: 1.25;
            font-weight: 700;
            /* Reserva altura de 2 linhas sempre, mesmo quando o rótulo cabe em
               1 — sem isso, a linha de cards com um rótulo mais longo (ex:
               "Produtividade da mão de obra") ficava ~38% mais alta que a
               outra linha, já que todo card na mesma linha do grid estica
               junto (align-items:stretch) até o mais alto dela. */
            min-height: 1.95rem;
            color: var(--accent);
            margin: 0 0 4px 0;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .kpi-card .kpi-value {{
            position: relative;
            font-size: 1.55rem;
            font-weight: 700;
            color: {COLOR_TEXT};
            margin: 0;
            line-height: 1.2;
            /* nowrap+break-word juntos eram contraditórios (nowrap sempre
               ganha, break-word nunca rodava) — em card estreito (tela de
               celular, grid de 2 colunas) um valor comprido tipo "178.641
               L/ha/ano" cortava sem aviso. Agora quebra por palavra normal, e
               overflow-wrap só força quebra no meio se uma palavra sozinha
               ainda não couber. */
            white-space: normal;
            overflow-wrap: break-word;
        }}
        .kpi-card .kpi-icon-badge {{
            position: relative;
            width: 34px;
            height: 34px;
            border-radius: 9px;
            background: color-mix(in srgb, var(--accent) 16%, white);
            box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 30%, transparent);
            color: var(--accent);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.6rem;
        }}

        /* Toggle de recolher/expandir sidebar — sem tamanho próprio no
           Streamlit nativo, fica bem abaixo de 44x44. É o botão mais usado no
           fluxo mobile (abre/fecha a gaveta de filtros), então o alvo de
           toque aqui importa mais que na maioria dos outros. */
        [data-testid="stSidebarCollapseButton"] button {{
            width: 44px !important;
            height: 44px !important;
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
        /* Abaixo de 900px (tablet retrato / celular) a sidebar vira um painel
           sobreposto (position:fixed) em vez de espremer o conteúdo ao lado —
           430-480px fixos não cabem nem perto de uma tela de celular (~375-
           430px de largura TOTAL). Sem isso, a sidebar sozinha já era mais
           larga que a tela inteira. Virando overlay, o conteúdo principal
           ganha a largura toda por baixo, e a sidebar flutua por cima só
           quando aberta — padrão nativo de app mobile. */
        @media (max-width: 900px) {{
            [data-testid="stSidebar"] {{
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                bottom: 0 !important;
                height: 100vh !important;
                z-index: 999 !important;
            }}
            [data-testid="stSidebar"][aria-expanded="true"] {{
                width: 85vw !important;
                min-width: 0 !important;
                max-width: 380px !important;
                box-shadow: 8px 0 24px rgba(0,0,0,0.18);
            }}
            [data-testid="stSidebar"][aria-expanded="false"] {{
                width: 0 !important;
                min-width: 0 !important;
            }}
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
        /* Mesma família visual dos .kpi-card (raio de canto e borda sutil) —
           o padrão do Streamlit pra st.container(border=True) é uma borda
           cinza bem mais forte (~20% opacidade) e canto reto (8px), destoando
           dos cards de KPI ao lado (6-7% opacidade, 14px). Aplicado direto em
           todo stVerticalBlock (não só nos com borda) porque é seguro: um
           bloco sem borda tem border-width:0, então mudar só a cor/raio da
           borda não desenha nada nele. Fica neutro (sem tint de cor) de
           propósito: aqui dentro já tem gráfico colorido, cor a mais no
           contorno competiria com o dado em vez de só emoldurar. */
        [data-testid="stVerticalBlock"] {{
            border-radius: 14px !important;
            border-color: rgba(0,0,0,0.07) !important;
        }}
        /* Fundo branco sólido só nos cartões que mostram RESULTADO (gráfico
           Plotly, tabela ou pictograma) — identificados pelo que carregam
           dentro, não por classe/borda (o mesmo testid stVerticalBlock serve
           tanto pro cartão com borda quanto pro bloco de layout sem borda ao
           redor dele, sem diferença de classe entre os dois). Cartões de
           CONTROLE (filtros, seletores de variável) ficam de fora de
           propósito, deixando o gradiente de fundo aparecer neles também —
           só o que carrega dado precisa de fundo opaco pra continuar
           legível por cima do gradiente. */
        [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .js-plotly-plot),
        [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] [data-testid="stDataFrame"]),
        [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .pictogram-wrap) {{
            background-color: white !important;
        }}

        /* Todo diálogo (Filtro avançado, Explorador, Comparação, Correlações)
           ganha painel 100% opaco e véu de fundo translúcido — dá pra ver o
           dashboard atrás (dimmed), mas não dá pra ler, sem misturar com o
           conteúdo do painel. */
        /* transition/animation: none nas duas camadas (véu + painel) mata o
           fade de opacidade que o próprio BaseWeb aplica ao montar o modal —
           um mecanismo diferente da nossa animação de deslizar (já removida
           antes), só que com o mesmo sintoma visual: painel já na posição
           final mas semitransparente por ~650-850ms, com a sidebar visível
           por trás. Sem transição pra interpolar, o opacity:1 abaixo passa a
           valer desde o primeiro frame, não só no final de uma animação. */
        div[data-testid="stDialog"] > div {{
            background: rgba(10, 30, 35, 0.6) !important;
            opacity: 1 !important;
            transition: none !important;
            animation: none !important;
        }}
        div[data-testid="stDialog"] [role="dialog"] {{
            position: relative !important;
            background-color: white !important;
            opacity: 1 !important;
            transition: none !important;
            animation: none !important;
        }}
        /* Só o Filtro avançado (marcado via st.container(key="adv_filter_panel")
           — :has() localiza o diálogo certo sem precisar de mais nada do lado
           do Python) vira painel lateral deslizante; ele é o único diálogo
           complexo o bastante (até 4 filtros em cascata) pra justificar isso.
           Explorador/Comparação/Correlações são só 2-3 campos e ficam com o
           modal central padrão do Streamlit — mais leve e do tamanho certo. */
        div[data-testid="stDialog"] > div:has(.st-key-adv_filter_panel) {{
            justify-content: flex-start !important;
        }}
        div[data-testid="stDialog"] [role="dialog"]:has(.st-key-adv_filter_panel) {{
            width: 560px !important;
            max-width: 94vw !important;
            height: 100vh !important;
            max-height: 100vh !important;
            margin: 0 !important;
            border-radius: 0 18px 18px 0 !important;
            box-shadow: 8px 0 32px rgba(0,0,0,0.22);
            /* Sem animação de deslizar aqui de propósito (era um translateX
               saindo de fora da tela) — o diálogo só ganha essa marcação
               (:has(.st-key-adv_filter_panel)) depois que o conteúdo já
               carregou, e nesse intervalo entre o modal padrão nascer e o CSS
               de painel lateral aplicar, a animação ficava visível a meio
               caminho, fora da tela, com a sidebar por trás aparecendo sem o
               véu escuro por cima. Sem animação, o painel já nasce no lugar
               certo, sem estado intermediário pra vazar. */
            /* Com vários filtros o conteúdo pode passar da altura da tela — sem
               isso o botão "Aplicar e fechar" simplesmente some, sem como rolar
               até ele. */
            overflow-y: auto !important;
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


# Uma cor de destaque por card (não uma paleta sequencial — os KPIs não têm
# ordem lógica entre si, cada um é uma métrica independente, então cores bem
# 3 cores com significado (não 10 soltas): cada KPI pertence a uma categoria
# real, e a cor comunica isso de relance em vez de só diferenciar cards.
# Todas as 3 passam WCAG AA (4.5:1+) como texto sobre fundo branco.
_KPI_CATEGORY_COLORS = {
    "producao": COLOR_PRIMARY_ACCESSIBLE,  # #157B8F — 4.93:1
    "perfil": COLOR_SECONDARY,  # #008448 — 4.78:1
    "financeiro": "#8A6A1F",  # dourado escurecido — 5.05:1 (o #C99A2E original dava só 2.58:1)
}


def render_kpi_row(items: list[tuple[str, str, str, str]]) -> None:
    """items: lista de (chave_do_ícone, label, valor, categoria), categoria em
    "producao" | "perfil" | "financeiro"."""
    cards = []
    for icon, label, value, category in items:
        accent = _KPI_CATEGORY_COLORS[category]
        icon_html = f'<div class="kpi-icon-badge">{render_icon(icon, 18)}</div>' if icon else ""
        # role="group" + aria-label: o valor e o rótulo já são texto visível,
        # mas sem isso um leitor de tela lê os dois como dois nós soltos,
        # sem deixar claro que "L/dia" ali é o valor DESTE rótulo específico
        # — junta os dois numa única unidade anunciada de uma vez.
        cards.append(
            f'<div class="kpi-card" style="--accent:{accent}" role="group" aria-label="{label}: {value}">{icon_html}'
            f'<p class="kpi-label">{label}</p><p class="kpi-value">{value}</p>'
            f'<div class="kpi-accent-line"></div></div>'
        )
    st.markdown(f'<div class="kpi-row">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_sr_only(text: str) -> None:
    """Texto só pra leitor de tela (tecnica "sr-only" padrão: encolhido a 1px
    e cortado, mas sem display:none, que teria feito o leitor de tela ignorar
    também) — descreve o conteúdo de um gráfico Plotly ou pictograma, que não
    tem alternativa textual nativa nenhuma por padrão."""
    st.markdown(
        f'<span style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;'
        f'overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;">{text}</span>',
        unsafe_allow_html=True,
    )


def render_kpi_legend() -> None:
    """Legenda das 3 categorias de KPI — cor sozinha nunca deve ser o único
    jeito de comunicar significado (WCAG 1.4.1), então isso deixa explícito
    por texto o que cada cor de render_kpi_row representa."""
    render_color_legend(
        [
            ("Produção/operação", _KPI_CATEGORY_COLORS["producao"]),
            ("Perfil do produtor", _KPI_CATEGORY_COLORS["perfil"]),
            ("Financeiro", _KPI_CATEGORY_COLORS["financeiro"]),
        ]
    )


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
