"""Gera o hash bcrypt de uma senha para colocar em .streamlit/secrets.toml."""
import getpass

import bcrypt


def main() -> None:
    password = getpass.getpass("Digite a senha a ser hasheada: ")
    confirm = getpass.getpass("Confirme a senha: ")
    if password != confirm:
        print("As senhas não coincidem.")
        return
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    print("\nAdicione isto em .streamlit/secrets.toml (ou nos Secrets do Streamlit Cloud):\n")
    print(f'password = "{hashed}"')


if __name__ == "__main__":
    main()
