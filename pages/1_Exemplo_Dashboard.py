import numpy as np
import pandas as pd
import streamlit as st
from auth import require_login, logout_button
from branding import APP_NAME, page_icon, render_footer, render_header

st.set_page_config(page_title=f"{APP_NAME} - Exemplo", page_icon=page_icon(), layout="wide")

require_login()
logout_button()
render_header("Exemplo de Dashboard")

st.info(
    "Esta é uma página de exemplo. Substitua este arquivo pelos seus dashboards reais — "
    "cada novo arquivo em `pages/` vira automaticamente uma página no menu lateral, "
    "e o require_login() no topo garante que só usuários autenticados acessem."
)

df = pd.DataFrame(np.random.randn(20, 3), columns=["A", "B", "C"])
st.line_chart(df)

render_footer()
