Esta pasta armazena todos os datasets de entrada utilizados pelo sistema `Recomenda.ai`.

## Fontes dos Dados

Os dados são uma combinação de duas fontes principais:

1.  **MovieLens (Latest Small Dataset):**
    * **Origem:** [https://grouplens.org/datasets/movielens/](https://grouplens.org/datasets/movielens/)
    * **Descrição:** Fornece a base de comportamento do usuário (avaliações) e o mapeamento de IDs.

2.  **TMDB (The Movie Database):**
    * **Origem:** [https://www.themoviedb.org/](https://www.themoviedb.org/)
    * **Descrição:** Usado via API para coletar metadados de conteúdo ricos (sinopse, diretor, atores).

## Estrutura dos Arquivos

| Arquivo | Origem | Conteúdo Principal | Propósito no Projeto |
| :--- | :--- | :--- | :--- |
| **`usuarios.csv`** | MovieLens (`ratings.csv`) | `userId`, `movieId`, `rating` | Treinamento do modelo de **Filtragem Colaborativa** (`machine.py`). |
| **`links.csv`** | MovieLens (`links.csv`) | `movieId`, `imdbId`, `tmdbId` | **Mapeamento (Ponte)**. Usado pelo `coleta_api.py` para traduzir o `movieId` (local) para o `tmdbId` (API). |
| **`filmes.csv`** | **Gerado pelo `coleta_api.py`** | `movieId`, `titulo`, `sinopse`, `generos`, `diretor`, `atores` | Treinamento do modelo de **PNL e Similaridade de Conteúdo** (`pnl_modulo.py`). |