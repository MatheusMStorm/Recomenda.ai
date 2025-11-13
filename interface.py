import streamlit as st
import time

# Configuração da página
st.set_page_config(page_title="Recomenda Ai", layout="centered")

# --- Inicialização da Memória (Session State) ---

# 1. Guarda o usuário LOGADO ATUALMENTE
if "user" not in st.session_state:
    st.session_state.user = None

# 2. Guarda o histórico do chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Simula um "banco de dados" de usuários
# (Em um app real, isso seria um banco de dados externo)
if "user_db" not in st.session_state:
    # Vamos adicionar um usuário admin para facilitar o teste do login
    st.session_state.user_db = {
        "admin": {"email": "admin@recomenda.ai", "senha": "123"}
    }

st.title("🤖 Recomenda Ai")

# --- LÓGICA DE AUTENTICAÇÃO ---
# Se o usuário NÃO está logado, mostre as abas de Login/Cadastro
if st.session_state.user is None:
    
    # Goal 1: Inverter a ordem das abas (Cadastro primeiro)
    tab_cadastro, tab_login = st.tabs(["👤 Cadastro", "🔑 Login"])

    # --- Aba de Cadastro ---
    with tab_cadastro:
        st.header("Crie sua conta")
        
        with st.form("cadastro_form"):
            nome_cad = st.text_input("Nome (será seu login)")
            email_cad = st.text_input("Email")
            senha_cad = st.text_input("Senha", type="password")
            submitted_cad = st.form_submit_button("Cadastrar")
            
            if submitted_cad:
                if not nome_cad or not email_cad or not senha_cad:
                    st.error("Por favor, preencha todos os campos.")
                # Verifica se o usuário já existe no nosso "banco de dados"
                elif nome_cad in st.session_state.user_db:
                    st.error(f"O usuário '{nome_cad}' já existe. Tente fazer login.")
                else:
                    # Adiciona o novo usuário ao "banco de dados"
                    st.session_state.user_db[nome_cad] = {
                        "email": email_cad, 
                        "senha": senha_cad
                    }
                    
                    # Goal 2: Loga o usuário automaticamente após o cadastro
                    st.session_state.user = {"nome": nome_cad, "email": email_cad}
                    st.success(f"Usuário {nome_cad} cadastrado! Redirecionando para o chat...")
                    
                    # Pausa de 1.5s para o usuário ler a msg
                    time.sleep(1.5) 
                    
                    # Recarrega a página. Como st.session_state.user agora existe,
                    # o app vai pular o 'if' e ir direto para o 'else' (o chat)
                    st.rerun() 

    # --- Aba de Login ---
    with tab_login:
        st.header("Login")
        
        with st.form("login_form"):
            nome_login = st.text_input("Nome de usuário")
            senha_login = st.text_input("Senha", type="password")
            submitted_login = st.form_submit_button("Entrar")
            
            if submitted_login:
                # Procura o usuário no "banco de dados"
                user_data = st.session_state.user_db.get(nome_login)
                
                # Verifica se o usuário existe E se a senha bate
                if user_data and user_data["senha"] == senha_login:
                    # Loga o usuário
                    st.session_state.user = {"nome": nome_login, "email": user_data["email"]}
                    st.success("Login bem-sucedido! Redirecionando...")
                    time.sleep(1.5)
                    st.rerun()
                
                elif user_data:
                    # Usuário existe, mas senha está errada
                    st.error("Senha incorreta.")
                else:
                    # Goal 4: Se não houver login, peça para ir ao cadastro
                    st.error(f"Usuário '{nome_login}' não encontrado. Por favor, cadastre-se na aba 'Cadastro'.")

# --- LÓGICA DO CHAT ---
# Se o usuário ESTÁ logado, mostre a interface do chat
else:
    st.header(f"Chatbot - Bem-vindo, {st.session_state.user['nome']}!")
    
    # Botão de Logout
    if st.sidebar.button("Sair (Logout)"):
        st.session_state.user = None
        st.session_state.messages = [] # Limpa o chat ao sair
        st.rerun()

    # Exibe o histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input do chat
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Adiciona a mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # --- Lógica do Chatbot (Eco) ---
        response = f"O chatbot recebeu: '{prompt}'"
        # --------------------------------

        # Adiciona a resposta do bot ao histórico
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)