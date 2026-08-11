# Notas do projeto — PDPL/PCEPL-UFV Dashboards

## Links
- Repositório GitHub: https://github.com/thiagorobertowendling2002-lab/pdpldashboard (atualmente **público** — ver seção "Privacidade" abaixo)
- App no ar: https://dashboardpdpl.streamlit.app/

## Estrutura
- `app.py` — página inicial (exige login)
- `auth.py` — lógica de login (bcrypt + `st.session_state`)
- `branding.py` — identidade visual (logo, cores, cabeçalho, citação de homenagem)
- `pages/` — cada arquivo `.py` aqui vira uma página nova no menu lateral automaticamente
- `assets/logo.png` — logo do PDPL/PCEPL-UFV
- `scripts/hash_password.py` — gera hash bcrypt para novos usuários

## Como adicionar um dashboard novo
Copiar o padrão de `pages/1_Exemplo_Dashboard.py`:
```python
import streamlit as st
from auth import require_login, logout_button
from branding import APP_NAME, page_icon, render_footer, render_header

st.set_page_config(page_title=f"{APP_NAME} - Nome", page_icon=page_icon(), layout="wide")
require_login()
logout_button()
render_header("Nome do Dashboard")

# conteúdo aqui

render_footer()
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
