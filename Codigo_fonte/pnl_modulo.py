import pandas as pd
import re #  buscar ou extrair padrões"""
import nltk # biblioteca PNL"""
from nltk.corpus import stopwords # reduz os ruidos das frases"""
from nltk.stem import RSLPStemmer # reduz palavras para o entendimento"""
from sklearn.feature_extraction.text import TfidfVectorizer # transforma os textos em vetor"""
from sklearn.metrics.pairwise import cosine_similarity # Para calcular a similaridade
import pickle # Para salvar o modelo
import os # Para lidar com caminhos de arquivo
import string #  manipulação dos textos"""
import numpy as np #  manipução numerica"""


DATA_FILE = os.path.join("Data", "filmes.csv") #Modelo
MODEL_FILE = os.path.join("Modelos", "pnl_similarity_model.pkl")

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Baixando pacote 'stopwords' do NLTK...")
    nltk.download('stopwords')

STOPWORDS_PT = set(stopwords.words('portuguese'))

def carregar_dados():    #Carrega a pasta Data.
    try:
        df = pd.read_csv(DATA_FILE)
        print(f"Arquivo '{DATA_FILE}' carregado com {len(df)} filmes.")
        return df
    except FileNotFoundError:
        print(f"Erro: Arquivo '{DATA_FILE}' não encontrado.")
        # print("Certifique-se de executar o script 'coleta_api.py' primeiro.")
        return None

def limpar_texto(texto): #Limpa e pré-processa uma string de texto.
    if not isinstance(texto, str):
        return
    texto = texto.lower()
    texto = re.sub(r'[^a-z\s]', '', texto)
    palavras = [palavra for palavra in texto.split() if palavra not in STOPWORDS_PT]
    return " ".join(palavras)

def criar_features_de_texto(df): #Combina colunas de texto (sinopse, generos, etc.) em uma única "super-feature" para o modelo PNL.
    print("Criando features de texto combinadas...")

    df['sinopse'] = df['sinopse'].fillna('') # Preenche valores vazios com strings vazias
    df['generos'] = df['generos'].fillna('')
    df['diretor'] = df['diretor'].fillna('')
    df['atores'] = df['atores'].fillna('')
    df['sinopse_limpa'] = df['sinopse'].apply(limpar_texto) # Limpa e formata cada coluna de texto e são unidos por '|'. Trocamos por espaço.
    df['generos_limpo'] = df['generos'].apply(lambda x: " ".join(x.split('|')))
    df['diretor_limpo'] = df['diretor'].apply(lambda x: " ".join(x.split('|')))
    df['atores_limpo'] = df['atores'].apply(lambda x: " ".join(x.split('|')))
    df['feature_pnl'] = (
        df['sinopse_limpa'] * 3 + " " +  # Sinopse tem maior peso
        df['generos_limpo'] * 2 + " " + # Gêneros tem peso médio
        df['diretor_limpo'] + " " +     # Diretor tem peso normal
        df['atores_limpo']              # Atores tem peso normal
    )
    
    print("Features de texto criadas com sucesso.")
    return df

def treinar_e_salvar_modelo(): #Função principal: Carrega, processa, treina o modelo TF-IDF, calcula a similaridade de cosseno e salva o modelo final.
    filmes_df = carregar_dados()
    if filmes_df is None:
        return
        
    filmes_df = criar_features_de_texto(filmes_df)
    print("Iniciando vetorização TF-IDF...") 
    tfidf_vectorizer = TfidfVectorizer(max_features=5000) # Limita as 5000 palavras mais frequentes
    tfidf_matrix = tfidf_vectorizer.fit_transform(filmes_df['feature_pnl']) # Transforma em uma matriz numérica
    print("Matriz TF-IDF criada.")
    print("Calculando similaridade de cosseno...")
    cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix) # Matriz que compara cada filme com todos os outros
    print("Matriz de similaridade calculada.")

    movie_indices = pd.Series(filmes_df.index, index=filmes_df['movieId']).drop_duplicates() # Define o mapeamento do 'movieId' para o índice da matriz (0, 1, 2...)
    os.makedirs("Modelos", exist_ok=True) # Garante que a pasta 'Modelos' exista antes de salvar 
    modelo_pnl_data = { # Salva os componentes essenciais para o recomendador
        'cosine_sim_matrix': cosine_sim_matrix,
        'movie_indices': movie_indices
    }
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(modelo_pnl_data, f)
        
    print(f"Modelo PNL salvo com sucesso em '{MODEL_FILE}'!")

if __name__ == "__main__":
    print("Iniciando script de treinamento do 'pnl_modulo'...")
    treinar_e_salvar_modelo()