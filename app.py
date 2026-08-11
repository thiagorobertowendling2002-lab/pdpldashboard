import streamlit as st
from auth import check_password, logout_button
from branding import APP_NAME, page_icon

st.set_page_config(page_title=APP_NAME, page_icon=page_icon(), layout="wide", initial_sidebar_state="expanded")

if not check_password():
    st.stop()

logout_button()

pg = st.navigation(
    [
        st.Page("views/home.py", title="Início", default=True),
        st.Page("views/produtores_pdpl.py", title="Produtores PDPL"),
    ]
)
pg.run()
