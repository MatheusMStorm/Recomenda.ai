import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import pickle
import os

# Define o caminho para salvar o sistema Fuzzy compilado
MODEL_FILE = os.path.join("Modelos", "fuzzy_control_system.pkl")
def definir_e_salvar_sistema_fuzzy():
    
    ###Cria, executa e salva o sistema de controle fuzzy que usa a nota prevista e 
    ###o tempo disponível para definir a prioridade final de recomendação.

    print("Iniciando definição do Sistema de Controle Fuzzy...")

    # --- 1. Especificação das Variáveis  ---

    # Entrada 1: Nota estimada pelo modelo colaborativo
    # Escala de 1 a 5 
    nota_prevista = ctrl.Antecedent(np.arange(1, 5.1, 0.1), 'nota_prevista')

    # Entrada 2: Tempo livre do usuário em minutos
    # Escala de 15 a 240 minutos
    tempo_disponivel = ctrl.Antecedent(np.arange(15, 241, 1), 'tempo_disponivel')
    
    # Consequente: Prioridade da recomendação
    # Escala de 0 a 100
    prioridade_final = ctrl.Consequent(np.arange(0, 101, 1), 'prioridade_final')

    # --- 2. Especificação das Funções de Membros ---
    
    # Funções de Membros para 'nota_prevista'
    nota_prevista['baixa'] = fuzz.trimf(nota_prevista.universe, [1, 1, 3])
    nota_prevista['media'] = fuzz.trimf(nota_prevista.universe, [2.5, 3.5, 4.5])
    nota_prevista['alta'] = fuzz.trimf(nota_prevista.universe, [4, 5, 5])

    # Funções de Membros para 'tempo_disponivel'
    tempo_disponivel['curto'] = fuzz.trimf(tempo_disponivel.universe, [15, 15, 90])
    tempo_disponivel['medio'] = fuzz.trimf(tempo_disponivel.universe, [70, 100, 130])
    tempo_disponivel['longo'] = fuzz.trimf(tempo_disponivel.universe, [110, 240, 240])

    # Funções de Membros para 'prioridade_final' 
    prioridade_final['baixa'] = fuzz.trimf(prioridade_final.universe, [0, 0, 40])
    prioridade_final['media'] = fuzz.trimf(prioridade_final.universe, [30, 50, 70])
    prioridade_final['alta'] = fuzz.trimf(prioridade_final.universe, [60, 100, 100])

    # --- 3. Especificação das Regras  ---
    
    # Regra 1: SE a nota prevista for ALTA E o tempo for CURTO, a prioridade é ALTA.
    regra1 = ctrl.Rule(nota_prevista['alta'] & tempo_disponivel['curto'], prioridade_final['alta'])
    regra2 = ctrl.Rule(nota_prevista['media'], prioridade_final['media'])
    regra3 = ctrl.Rule(nota_prevista['baixa'], prioridade_final['baixa'])
    regra4 = ctrl.Rule(nota_prevista['alta'] & tempo_disponivel['longo'], prioridade_final['media'])
    regra5 = ctrl.Rule(nota_prevista['media'] & tempo_disponivel['curto'], prioridade_final['alta'])
   
    # --- 4.Criação e Armazenamento do Sistema de Controle ---
    sistema_ctrl = ctrl.ControlSystem([regra1, regra2, regra3, regra4, regra5])
    simulacao_fuzzy = ctrl.ControlSystemSimulation(sistema_ctrl) 
    os.makedirs("Modelos", exist_ok=True)
    
    # Salva o sistema de controle no arquivo
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(sistema_ctrl, f)
        
    print(f"Sistema de Controle Fuzzy definido e salvo em '{MODEL_FILE}'!")
    
    return simulacao_fuzzy

def testar_sistema(simulacao_fuzzy, nota, tempo):
    ###Função para testar a simulação com entradas.
    simulacao_fuzzy.input['nota_prevista'] = nota
    simulacao_fuzzy.input['tempo_disponivel'] = tempo
    
    # Executa a computação Fuzzy
    simulacao_fuzzy.compute()
    
    prioridade = simulacao_fuzzy.output['prioridade_final']
    print(f"--- Teste ---")
    print(f"Entradas: Nota Prevista={nota}, Tempo Disponível={tempo} min")
    print(f"Resultado (Prioridade Final): {prioridade:.2f} / 100")
    return prioridade

if __name__ == "__main__":
    print("Executando 'fuzzy_modulo.py' para definir e salvar o sistema...")
    sistema_sim = definir_e_salvar_sistema_fuzzy()
    
    print("\n--- Executando Testes de Simulação ---")
    
    # Teste 1: Filme ótimo (4.5), tempo curto (30 min) -> Deve dar prioridade ALTA
    testar_sistema(sistema_sim, 4.5, 30)
    
    # Teste 2: Filme ótimo (4.5), tempo longo (200 min) -> Deve dar prioridade MEDIA (Regra 4)
    testar_sistema(sistema_sim, 4.5, 200)

    # Teste 3: Filme "ok" (3.0), tempo curto (40 min) -> Deve dar prioridade ALTA (Regra 5)
    testar_sistema(sistema_sim, 3.0, 40)
    
    # Teste 4: Filme ruim (1.5), tempo qualquer (120 min) -> Deve dar prioridade BAIXA
    testar_sistema(sistema_sim, 1.5, 120)