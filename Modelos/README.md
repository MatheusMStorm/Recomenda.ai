Esta pasta armazena os modelos de Inteligência Artificial pré-treinados e persistidos, prontos para serem usados pela aplicação principal (`recomendar.py`).

O uso de modelos `.pkl` evita a necessidade de retreinamento a cada execução do sistema.

## Modelos Persistidos

| Arquivo `.pkl` | Script Gerador | Técnica de IA | Propósito |
| :--- | :--- | :--- | :--- |
| **`pnl_similarity_model.pkl`** | `pnl_modulo.py` | PNL (TF-IDF + Cosine Similarity) | Armazena a **Matriz de Similaridade de Conteúdo** (N_filmes x N_filmes) e o **Índice de Mapeamento** (`movieId` -> índice da matriz). |
| **`collab_model.pkl`** | `machine.py` | Machine Learning (Filtragem Colaborativa) | Armazena o objeto do **Modelo SVD (Surprise)** treinado com todos os dados de avaliação dos usuários. |
| **`fuzzy_control_system.pkl`** | `fuzzy_modulo.py` | Lógica Fuzzy | Armazena o **Sistema de Controle Fuzzy** (`skfuzzy.ControlSystem`) compilado, contendo as variáveis de entrada, saída e as regras contextuais. |