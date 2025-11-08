
# Recomenda.ai

<center>
<img src="Recomenda.ai.png" width=150 alt="logo recomenda.ai">
</center>

Recomenda.ai é um sistema de recomendação de filmes alimentado por inteligência artificial, projetado para ajudar usuários a descobrir o filme certo, no momento certo. Utilizando técnicas modernas de filtragem colaborativa, embeddings semânticos e modelos híbridos que combinam conteúdo e comportamento, o serviço personaliza sugestões com base no histórico de visualização, avaliações, preferências explícitas e sinais contextuais (por exemplo: dia da semana, tempo disponível, dispositivo). Além de entregar recomendações precisas, o sistema prioriza explicabilidade — cada sugestão vem acompanhada de motivos curtos (gênero, diretor, atores, similaridade de enredo) para aumentar a confiança do usuário e facilitar a descoberta.

#  Sistema Híbrido de Recomendação de Filmes

Este projeto é um sistema de recomendação de filmes desenvolvido para a UC de Inteligência Artificial. O "Recomenda.ai" utiliza uma abordagem híbrida que combina múltiplas técnicas de IA para fornecer sugestões personalizadas, contextuais e explicáveis.

## 🎯 Objetivo

O objetivo é aplicar técnicas de IA aprendidas em sala de aula (como lógica fuzzy, algoritmos de busca e redes neurais/genéticos) em um desafio de complexidade média para difícil. O sistema não apenas sugere filmes com base no histórico do usuário, mas também considera o **contexto** (ex: tempo disponível) e fornece **explicabilidade** (o porquê da recomendação).

## 🧠 Arquitetura de IA

O sistema utiliza um modelo híbrido que combina três motores de Inteligência Artificial:

1.  **Filtragem Colaborativa (`machine.py`):**
    * **Técnica:** Fatoração Matricial (ex: SVD).
    * **Função:** Analisa o comportamento de usuários similares (com base no `Data/usuarios.csv`) para prever avaliações e encontrar filmes que o usuário provavelmente gostará com base no gosto da comunidade.

2.  **Filtragem Baseada em Conteúdo (PNL) (`pnl_modulo.py`):**
    * **Técnica:** Processamento de Linguagem Natural (PNL) com TF-IDF e Similaridade de Cosseno.
    * **Função:** Gera "embeddings semânticos" a partir de `sinopse`, `gênero`, `diretor` e `atores`. É usado para encontrar filmes textualmente similares (similaridade de enredo) e para justificar recomendações.

3.  **Refinamento Contextual (`fuzzy_modulo.py`):**
    * **Técnica:** Lógica Fuzzy.
    * **Função:** Ajusta o ranking final das recomendações com base em entradas contextuais vagas, como `tempo_disponível` e `nota_prevista`, para aumentar a relevância da sugestão no momento exato.

## 🔧 Como Executar o Projeto

O projeto é dividido em três fases: Instalação, Treinamento (que gera os modelos) e Execução (que inicia a aplicação).

### Pré-requisitos

Certifique-se de ter o Python 3.10+ instalado.

### 1. Instalar Dependências

Instale todas as bibliotecas necessárias listadas no arquivo `requirements.txt`:

pip install -r requirements.txt

2. Coleta de Dados e Treinamento dos Modelos de IA

Estes scripts preparam os dados e treinam os modelos de IA, salvando os artefatos (.pkl) na pasta Modelos. Execute-os apenas uma vez (ou sempre que os dados de origem mudarem).

Coleta de Dados (Opcional, se filmes.csv não existir):

## 1. Coleta os dados da API do TMDB
python3 coleta_api.py

Treinamento dos Modelos:

## 2. Treina o modelo de Similaridade de Conteúdo (PNL)
python3 Codigo_fonte/pnl_modulo.py

## 3. Define e salva o sistema de Lógica Fuzzy
python3 Codigo_fonte/fuzzy_modulo.py

## 4. Treina o modelo de Filtragem Colaborativa (ML)
python3 Codigo_fonte/machine.py

## 5. Executar a Aplicação Principal
Para iniciar a interface gráfica (GUI) e interagir com o sistema de recomendação (usando o Streamlit):

streamlit run Codigo_fonte/Simple_gui.py

## 📦 Estrutura de Entrega (Requisitos da A3)

Este repositório segue os requisitos de entrega da A3:

Codigo_fonte/: Contém todos os artefatos, scripts de inicialização e o requirements.txt.

poster/: Contém o poster da apresentação detalhando a arquitetura, estratégia e algoritmos utilizados.

Tag EntregaA3: O repositório será marcado com esta tag no commit final para a entrega. Prazo final: TBD
