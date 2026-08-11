# Notas do projeto — PDPL/PCEPL-UFV Dashboards

## Links
- Repositório GitHub: https://github.com/thiagorobertowendling2002-lab/pdpldashboard (atualmente **público** — ver seção "Privacidade" abaixo)
- App no ar: https://dashboardpdpl.streamlit.app/

## Estrutura
- `app.py` — roteador central: faz login (`check_password()`), e só então monta o
  menu com `st.navigation()`. **Não existe mais pasta `pages/`** — Streamlit mostra
  automaticamente os nomes de tudo que está em `pages/` no menu lateral mesmo antes
  do login, então trocamos por navegação controlada manualmente (ver "Problemas
  resolvidos" abaixo).
- `auth.py` — lógica de login (bcrypt + `st.session_state`)
- `branding.py` — identidade visual (logo, cores, cabeçalho, citação de homenagem)
- `views/` — cada arquivo `.py` aqui é uma página, registrada manualmente em
  `app.py` via `st.Page(...)`. Só aparece no menu depois do login.
- `assets/logo.png` — logo do PDPL/PCEPL-UFV
- `scripts/hash_password.py` — gera hash bcrypt para novos usuários

## Como adicionar um dashboard novo
1. Criar o arquivo em `views/nome_do_dashboard.py`, seguindo o padrão de
   `views/produtores_pdpl.py`:
```python
import streamlit as st
from branding import render_footer, render_header

render_header("Nome do Dashboard")

# conteúdo aqui

render_footer()
```
   Não precisa chamar login, logout ou `st.set_page_config` — isso já é feito uma
   vez só em `app.py`.

2. Registrar a página em `app.py`, dentro da lista do `st.navigation([...])`:
```python
st.Page("views/nome_do_dashboard.py", title="Nome do Dashboard"),
```

## Dados dos dashboards
Planilhas/dados confidenciais (ex: `data/produtores_pdpl.xlsx`) ficam na pasta `data/`,
que está no `.gitignore` — nunca vai pro GitHub. Cada dashboard tem um "loader" próprio
(ex: `data_loader.py`) que lê o arquivo local e expõe funções cacheadas (`@st.cache_data`)
com os dados já limpos para as páginas usarem.

**Consequência importante**: como `data/` não vai pro git, o app publicado no Streamlit
Cloud não tem acesso a esses arquivos — só o que está versionado é deployado. Antes do
dashboard "Produtores PDPL" funcionar em produção, é preciso resolver a privacidade do
repositório (ver seção abaixo) e então comitar os dados reais dentro do repositório
privado.

## Dashboard "Produtores PDPL" — arquitetura
`views/produtores_pdpl.py` não lista colunas na mão — ele usa um motor de
classificação automática em `data_loader.py` (`build_catalog()`) que lê as 323
colunas da planilha e separa sozinho em:
- **`categorical_vars`** — perguntas de resposta única (ex: Sexo, Escolaridade)
- **`numeric_vars`** — perguntas numéricas avulsas (ex: Idade, Produção média)
- **`numeric_groups`** — colunas que somam uma composição (ex: "Distribuição da
  área: Própria/Arrendada/..."), viram um gráfico de barras de composição
- **`multiselect_groups`** — perguntas "marque todas que se aplicam" (a planilha
  gera uma coluna Sim/vazio por opção; o loader reagrupa pela pergunta original),
  viram um ranking de barras
- **`fun_facts`** — perguntas onde todo mundo respondeu a mesma coisa (ex: "100%
  usa ordenha mecânica"), viram um card de destaque em vez de gráfico

Cada item carrega a `section` (mapeada pelo prefixo numérico da pergunta, ex.
"5." → "Produção e Rebanho") usada para organizar as abas do dashboard.

`charts.py` tem as funções de gráfico (donut, ranked_bar, histogram,
composition_bar, box_by_category, scatter, correlation_heatmap, grouped_bar_crosstab),
todas usando a paleta da marca (teal/verde) e sem gráfico de pizza com muitas
cores — regras de cor/forma seguidas conforme a skill de dataviz do Claude Code.

O dashboard tem: filtros globais (município/tipologia/estrato/sistema) que
recalculam tudo, uma aba por seção do questionário, uma aba "Explorador" pra
comparar quaisquer duas variáveis (escolhe o tipo de gráfico certo sozinho:
dispersão, boxplot ou barras agrupadas conforme os tipos), e uma aba de mapa de
calor de correlação entre as variáveis numéricas.

Pra estender esse dashboard (novas seções, KPIs) não precisa mexer no motor de
classificação — só adicionar/editar helpers em `views/produtores_pdpl.py`. Se
um dashboard *novo* (diferente) precisar da mesma abordagem de "classificar
uma planilha automaticamente", dá pra reaproveitar o padrão de `data_loader.py`.

## Credenciais / Secrets
As senhas nunca ficam no código nem no GitHub — vivem em:
- **Local**: `.streamlit/secrets.toml` (gitignored)
- **Produção**: Streamlit Cloud → app → "Manage app" → Settings → Secrets

Formato:
```toml
[credentials.usuario]
name = "Nome"
password = "$2b$12$hash_gerado_por_scripts/hash_password.py"
```

Depois de editar os Secrets em produção, o app reinicia sozinho; se não pegar, forçar
"Manage app" → ⋮ → **Reboot app**.

## Privacidade do repositório
O repositório está **público** hoje porque o GitHub App do Streamlit Cloud não estava
instalado na conta e bloqueava o acesso a repositórios privados (erro 404 ao tentar
`query-repository`). Como o código não contém nenhum dado confidencial (senhas ficam em
Secrets, fora do git), isso não é um risco imediato.

**Antes de colocar dados reais/confidenciais de algum dashboard dentro do repositório**,
resolver isso e voltar para privado:
1. https://github.com/settings/installations → instalar/configurar o app "Streamlit"
   para ter acesso ao repositório `pdpldashboard`.
2. `gh repo edit thiagorobertowendling2002-lab/pdpldashboard --visibility private --accept-visibility-change-consequences`
3. Redeploy/reboot do app no Streamlit Cloud.

Mesmo com o repositório privado, o ideal é que dados confidenciais de verdade não fiquem
commitados em CSV/planilha no repositório — preferir buscar de um banco de dados ou API
externa usando credenciais guardadas em Secrets.

## Problemas resolvidos durante o setup
- **Clique não funcionava no site local**: causado por extensão/antivírus bloqueando a
  conexão WebSocket do Streamlit. Resolvido testando em aba anônima.
- **Deploy travava ao clicar em "Deploy" no Streamlit Cloud**: causado pelo GitHub App
  do Streamlit nunca ter sido instalado na conta GitHub, então as chamadas de API
  (`query-repository`, `verifyFileExists`) retornavam 404. Contornado tornando o
  repositório público (não depende do App para repos públicos).
- **Login "usuário ou senha inválidos" em produção**: Secrets não configurados no painel
  do Streamlit Cloud (arquivo local `secrets.toml` não vai pro GitHub de propósito).
- **Nome do dashboard aparecia no menu antes do login**: a pasta `pages/` do Streamlit
  gera o menu lateral automaticamente com base nos arquivos que existem ali, mesmo que
  o conteúdo de cada página exija login pra aparecer. Resolvido trocando `pages/` por
  `views/` + `st.navigation()` chamado manualmente em `app.py`, só depois de confirmar
  o login — assim o menu nem existe enquanto não autenticado.
