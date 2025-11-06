import pandas as pd
import pickle
import os
import numpy as np
from surprise import Dataset, Reader
from surprise.model_selection import train_test_split, GridSearchCV
from surprise import SVD, accuracy 

DATA_FILE = os.path.join("Data", "usuarios.csv")

MODEL_FILE = os.path.join ("Modelos", "modelo_colaborativo.pkl")

print("iniciando")
         
def otimizar_e_treinar_modelo_colaborativo():


    try: 
        df_usuarios = pd.read_csv(DATA_FILE)
        print(f"Arquivo '{DATA_FILE}' carregado com {len(df_usuarios)} avaliações.")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{DATA_FILE}' não encontrado.") 
        return

    reader = Reader (rating_scale = (0.5, 5.0))
    data = Dataset.load_df (df_usuarios[['userId', 'movieId', 'rating']], reader)

        

    param_grid = {                              #definção de parâmetros a serem testados
        'n_factors': [50, 100, 150],
        'n_epochs': [10, 20, 30],
        'lr_all': [0.005, 0.01],
        'reg_all': [0.02, 0.05]
    }
    gs = GridSearchCV (SVD, param_grid, cv=3, n_jobs = -1, measures = ['rmse'], random_state = 42)

    gs.fit (data)  # . fit Executa e treina

    print("Melhores parâmetros:", gs.best_params['rmse'])

    teste_final = SVD(**gs.best_params['rmse'])

    teste_final.fit (trainset)
    print("Treinamento concluido!")

    os.makedirs("Modelos", exist_ok=True)

        #Salva o sistema de controle no arquivo
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(teste_final, f)
        
    print(f"Sistema de Otimização e Treinamento salvo em '{MODEL_FILE}'!")
        
    return teste_final

if __name__ == "__main__":
    print("Exibindo 'machine.py' com resultados otimizados.")
    modelo_final = otimizar_e_treinar_modelo_colaborativo()
    print("\n--- Executando Testes de Simulação ---")

    if modelo_final: 
        usuario_teste = 1
        filme_teste = 532
        previsao = modelo_final.predict (uid = usuario_teste, iid = filme_teste)

        print(f"Usuário: {previsao.uid}")
        print(f"Filme: {previsao.uid}")







#Criar o segundo motor de IA: Filtragem Colaborativa. Este script treinará um modelo que entende o comportamento do usuário quais filmes eles avaliaram bem.
#Definição dos caminhos, criar funções, criar e iniciar o bloco