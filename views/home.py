import streamlit as st
from branding import APP_NAME, is_dark_mode, render_footer, render_header

render_header(dark=is_dark_mode())

st.write(f"Bem-vindo(a), **{st.session_state.get('display_name', '')}**.")
st.markdown(
    f"""
Use o menu na barra lateral para navegar entre os dashboards do **{APP_NAME}**.
"""
)

render_footer()
