import streamlit as st
from auth import require_login, logout_button
from branding import APP_NAME, page_icon, render_footer, render_header

st.set_page_config(page_title=APP_NAME, page_icon=page_icon(), layout="wide", initial_sidebar_state="expanded")

require_login()
logout_button()
render_header()

st.write(f"Bem-vindo(a), **{st.session_state.get('display_name', '')}**.")
st.markdown(
    f"""
Use o menu na barra lateral para navegar entre os dashboards do **{APP_NAME}**.

Este é o ponto de entrada do site — todas as páginas dentro de `pages/` também
exigem login antes de exibir qualquer conteúdo.
"""
)

render_footer()
