import pandas as pd
import os

def _load_credentials_db(auth_csv_path):
    """Carrega o banco de dados de credenciais ou cria um novo."""
    if not os.path.exists(auth_csv_path):
        # Cria o arquivo se não existir
        df = pd.DataFrame(columns=["userId", "username", "password"])
        df.to_csv(auth_csv_path, index=False)
        return df
    try:
        return pd.read_csv(auth_csv_path)
    except pd.errors.EmptyDataError:
        # Se o arquivo existir mas estiver vazio
        df = pd.DataFrame(columns=["userId", "username", "password"])
        df.to_csv(auth_csv_path, index=False)
        return df

def _get_new_user_id(ratings_csv_path, auth_csv_path):
    """
    Encontra o maior userId em AMBOS os arquivos (ratings e auth)
    para que o novo usuário seja o próximo número.
    """
    max_ratings_id = 0
    max_auth_id = 0
    
    try:
        # 1. Verifica o 'usuarios.csv' (ratings)
        if os.path.exists(ratings_csv_path) and os.path.getsize(ratings_csv_path) > 0:
            df_ratings = pd.read_csv(ratings_csv_path)
            if 'userId' in df_ratings.columns and not df_ratings.empty:
                max_ratings_id = df_ratings['userId'].max()
                
        # 2. Verifica o 'user_credentials.csv' (auth)
        if os.path.exists(auth_csv_path) and os.path.getsize(auth_csv_path) > 0:
            df_auth = pd.read_csv(auth_csv_path)
            if 'userId' in df_auth.columns and not df_auth.empty:
                max_auth_id = df_auth['userId'].max()
                
    except Exception as e:
        print(f"Erro ao ler CSVs para novo ID: {e}")
        
    # O novo ID é o maior dos dois + 1
    return max(max_ratings_id, max_auth_id) + 1

def login_user(username, password, auth_csv_path):
    """
    Verifica o login (SENHA EM TEXTO PURO).
    Retorna o userId em caso de sucesso, None em caso de falha.
    """
    auth_db = _load_credentials_db(auth_csv_path)
    if auth_db.empty:
        return None
    
    # Busca pelo username (ignorando maiúsculas/minúsculas)
    user_data = auth_db[auth_db['username'].str.lower() == username.lower()]
    
    if not user_data.empty:
        user_row = user_data.iloc[0]
        password_saved = user_row['password']
        
        # Compara a senha em texto puro
        if password == password_saved:
            return int(user_row['userId']) # Sucesso
            
    return None # Falha

def register_user(username, password, auth_csv_path, ratings_csv_path):
    """
    Cadastra um novo usuário (SENHA EM TEXTO PURO).
    Retorna o novo userId em caso de sucesso.
    Retorna "EXISTS" se o usuário já existir.
    Retorna None em caso de falha.
    """
    auth_db = _load_credentials_db(auth_csv_path)
    
    # Verifica se o usuário já existe
    if not auth_db[auth_db['username'].str.lower() == username.lower()].empty:
        return "EXISTS"
        
    try:
        # Pega o próximo ID disponível
        new_user_id = _get_new_user_id(ratings_csv_path, auth_csv_path)
        
        # Cria o novo registro
        new_user_df = pd.DataFrame([{
            "userId": new_user_id,
            "username": username,
            "password": password # Salva a senha em texto puro
        }])
        
        # Salva (append) no user_credentials.csv
        new_user_df.to_csv(auth_csv_path, mode='a', header=not os.path.exists(auth_csv_path) or os.path.getsize(auth_csv_path) == 0, index=False)
        
        print(f"Usuário {username} (ID: {new_user_id}) registrado com sucesso.")
        return new_user_id # Sucesso
        
    except Exception as e:
        print(f"Erro ao registrar usuário: {e}")
        return None # Falha