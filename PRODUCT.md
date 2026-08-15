# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Três públicos, sem um caso de uso dominante:

- Thiago (e colegas do PDPL/PCEPL-UFV) usando o dashboard como ferramenta de análise interna, explorando os dados antes ou durante a preparação de relatórios.
- Thiago (ou outro membro da equipe) pilotando o dashboard ao vivo durante reuniões de apresentação com técnicos da CONAB (Companhia Nacional de Abastecimento).
- Profissionais da CONAB e de outras áreas acessando e explorando o dashboard de forma independente, sem alguém da equipe PDPL guiando.

## Product Purpose

Hospedar e analisar os dados de uma pesquisa com 30 produtores de leite do programa PDPL/PCEPL-UFV (Universidade Federal de Viçosa), cobrindo os 323 campos do questionário aplicado. O dashboard existe para permitir explorar, filtrar, comparar e encontrar associações estatísticas entre as respostas, substituindo relatórios estáticos e planilhas por uma ferramenta interativa. Sucesso significa que os três públicos acima conseguem extrair insights corretos e defensáveis dos dados sem precisar de treinamento estatístico formal.

## Positioning

[Inferido] Primeira ferramenta digital interativa do programa PDPL/PCEPL-UFV para essa pesquisa — substitui análise manual em planilha/relatório estático por filtragem, comparação cruzada e análise de associação estatística ao vivo. Não há um produto concorrente direto a se diferenciar; a "posição" é ser a ferramenta de referência interna do programa para essa base de dados.

## Operating Context

- Aplicação Streamlit (Python) com login próprio (bcrypt), hospedada no Streamlit Community Cloud, acessada via navegador.
- Repositório GitHub público (por necessidade prática de deploy), mas o link de acesso é compartilhado só com a equipe PDPL e a CONAB — não há divulgação pública ativa.
- Dados: planilha real e confidencial de 30 produtores de leite × 323 colunas de pesquisa (nomes, renda, dados de propriedade). Uso e publicação desses dados têm autorização explícita e reiterada do dono do produto.
- Usado tanto em análise solo quanto em apresentação projetada em reunião, quanto em acesso remoto e independente por terceiros — ver Users acima.

## Capabilities and Constraints

- Amostra pequena: N=30 produtores no total, menor ainda depois de filtros aplicados — todo resultado estatístico (correlação, associação, comparação) precisa deixar isso explícito e evitar sugerir confiança que os dados não sustentam.
- 323 colunas classificadas automaticamente em variáveis numéricas, categóricas, binárias (itens Sim/Não de múltipla escolha) e grupos de composição — a classificação é heurística (baseada em padrões do nome da coluna e cardinalidade), não um schema fixo.
- Ferramenta de associação entre fatores cobre 200+ variáveis combinando os três tipos, escolhendo o método estatístico certo por par (Pearson, ponto-bisserial, Phi, razão de correlação η, Cramér's V) — nunca trata tudo como Pearson.
- Stack: Streamlit + pandas + Plotly + scipy. Sem framework de front-end tradicional — não há HTML/CSS/JS separados; CSS customizado é injetado via strings Python (`unsafe_allow_html`).

## Brand Commitments

- Nome do programa: PDPL / PCEPL-UFV (Universidade Federal de Viçosa).
- Logo: ilustração de vaca, usada no cabeçalho e como favicon.
- Cores de marca: teal `#1C9CB4` (primária, do arco/logo) e verde `#008448` (secundária, do logo).
- Frase de homenagem exibida no material: "O fácil já foi feito." — GOMES, Sebastião Teixeira.

## Evidence on Hand

- Planilha real `data/produtores_pdpl.xlsx` (30 produtores × 323 colunas) — dado de pesquisa real, não fictício, usado em produção com autorização explícita do dono do produto.
- Não há depoimentos, estudos de caso ou material de prova adicional — é uma ferramenta analítica interna, não uma peça de marketing.

## Product Principles

- Correção estatística antes de simplicidade: nunca aplicar um método errado para o tipo de variável só para ter um número único e comparável.
- Nunca esconder o tamanho pequeno da amostra — toda métrica que pode enganar sozinha (força de associação, correlação) vem acompanhada do N e, quando aplicável, do p-valor.
- Nada de emoji ou estética "gerada por IA" — ícones profissionais (SVG customizado ou Material Symbols), paleta de marca, tratamento visual institucional, adequado a uma audiência de governo federal.
- Texto sempre legível por completo — nenhuma pergunta, rótulo ou opção pode ser cortada por limitação de largura; quando o espaço não permite, abrir um diálogo largo em vez de truncar.
- Performance importa: navegação e filtros precisam responder rápido mesmo com 15+ visões e 200+ variáveis — computação pesada é cacheada e só recalculada quando os dados filtrados mudam.

## Accessibility & Inclusion

Não há requisito de acessibilidade formal estabelecido ainda pelo usuário.
