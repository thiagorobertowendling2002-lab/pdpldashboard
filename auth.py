import streamlit as st
import bcrypt

from branding import APP_NAME, COLOR_TEXT, inject_css, logo_data_uri, render_login_background, render_quote


def _verify(username: str, password: str) -> dict | None:
    users = st.secrets.get("credentials", {})
    user = users.get(username)
    if not user:
        return None
    if bcrypt.checkpw(password.encode(), str(user["password"]).encode()):
        return user
    return None


def check_password() -> bool:
    """Mostra o formulário de login se necessário. Retorna True se autenticado."""
    if st.session_state.get("authenticated"):
        return True

    inject_css()
    render_login_background()

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        render_quote()
        st.markdown(
            f"""
            <div style='text-align:center;'>
                <img src="{logo_data_uri()}" width="220" alt="logo">
                <h2 style='color:{COLOR_TEXT}; margin:12px 0 0 0;'>{APP_NAME}</h2>
                <p style='color:{COLOR_TEXT}; opacity:0.65; margin-top:4px;'>Acesso aos Dashboards</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")

        if submitted:
            user = _verify(username, password)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["display_name"] = user.get("name", username)
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

    return False


def logout_button() -> None:
    if st.sidebar.button("Sair"):
        for key in ("authenticated", "username", "display_name"):
            st.session_state.pop(key, None)
        st.rerun()
