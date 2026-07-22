"""
Cliente para API da OpenAI.
Centraliza todas as chamadas ao LLM para facilitar controle e logging.
"""

from openai import OpenAI
from src.config import config


class LLMClient:
    """
    Cliente singleton para interagir com LLM.
    Controla temperatura, tokens e modelos para reduzir alucinação.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton: garante uma única instância."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = OpenAI(api_key=config.OPENAI_API_KEY)
        return cls._instance
    
    def gerar_texto(
        self,
        prompt: str,
        sistema: str = "Você é um assistente acadêmico especializado.",
        temperatura: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Gera texto usando LLM com parâmetros controlados.
        
        Args:
            prompt: Instrução para o LLM
            sistema: Contexto de sistema (persona)
            temperatura: Criatividade (None = usa padrão baixo)
            max_tokens: Limite de tokens
        
        Returns:
            Texto gerado pelo LLM
        """
        temp = temperatura if temperatura is not None else config.TEMPERATURA_PADRAO
        tokens = max_tokens if max_tokens is not None else config.MAX_TOKENS
        
        resposta = self.client.chat.completions.create(
            model=config.MODELO_LLM,
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": prompt}
            ],
            temperature=temp,
            max_tokens=tokens
        )
        
        return resposta.choices[0].message.content
    
    def gerar_multiplas_respostas(
        self,
        prompt: str,
        n: int = 3,
        temperatura: float = 0.7
    ) -> list:
        """
        Gera N respostas para self-consistency (detecção de alucinação).
        
        Args:
            prompt: Instrução
            n: Quantidade de respostas
            temperatura: Alta para variedade
        
        Returns:
            Lista de respostas
        """
        resposta = self.client.chat.completions.create(
            model=config.MODELO_LLM,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperatura,
            n=n,
            max_tokens=1000
        )
        
        return [choice.message.content for choice in resposta.choices]


# Instância global
llm = LLMClient()
