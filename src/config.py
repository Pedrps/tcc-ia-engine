"""
Configurações centralizadas do sistema.
"""

import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()


class Config:
    """Configurações do sistema."""
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Banco de dados
    DATABASE_URL = "sqlite:///tcc_database.db"
    
    # RAG / Embeddings
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Modelo leve de embeddings
    CHROMA_COLLECTION = "fontes_tcc"
    
    # Verificadores
    SCORE_MINIMO_FONTES = 0.7      # Score mínimo para fonte ser confiável
    SCORE_MINIMO_ABNT = 0.8        # Score mínimo para formato ABNT
    SCORE_MINIMO_LINGUAGEM = 0.75  # Score mínimo para linguagem acadêmica
    SCORE_MAXIMO_ALUCINACAO = 0.3  # Score máximo de risco de alucinação
    
    # LLM
    MODELO_LLM = "gpt-4o-mini"     # Modelo da OpenAI
    TEMPERATURA_PADRAO = 0.3       # Baixa = mais determinístico, menos alucinação
    MAX_TOKENS = 4000


config = Config()
