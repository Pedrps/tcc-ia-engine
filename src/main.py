"""
API principal do TCC IA Engine.
Endpoints para interagir com o sistema.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.motor import MotorTCC, StatusExecucao
from src.rag import Documento


# Modelos de request/response
class InputEstudante(BaseModel):
    """Input do estudante."""
    texto: str
    modo: Optional[str] = "completo"


class AprovacaoPlano(BaseModel):
    """Aprovação do plano pelo estudante."""
    plano: dict
    dados_tcc: dict
    aprovado: bool
    feedback: Optional[str] = ""


class FonteInput(BaseModel):
    """Input para adicionar fonte."""
    titulo: str
    conteudo: str
    fonte: str
    tipo: str
    autor: Optional[str] = ""
    ano: Optional[int] = 0


# Cria aplicação FastAPI
app = FastAPI(
    title="TCC IA Engine",
    description="Sistema de auxílio à construção de TCCs com IA",
    version="1.0.0"
)

# Instância do motor
motor = MotorTCC()


@app.get("/")
def home():
    """Página inicial."""
    return {
        "message": "TCC IA Engine funcionando!",
        "versao": "1.0.0",
        "endpoints": [
            "/parse - Parsear input do estudante",
            "/plano - Gerar plano de ações",
            "/aprovar - Aprovar plano e executar",
            "/fontes - Gerenciar fontes",
            "/health - Verificar saúde do sistema"
        ]
    }


@app.get("/health")
def health():
    """Verifica saúde do sistema."""
    return {"status": "ok", "servicos": ["parser", "planejador", "rag", "verificadores"]}


@app.post("/parse")
def parse_input_endpoint(input_data: InputEstudante):
    """
    Parseia input do estudante e retorna dados estruturados.
    
    Exemplo:
    {
        "texto": "Tema: Arquitetura sustentável em favelas",
        "modo": "apenas_parser"
    }
    """
    resultado = motor.executar(input_data.texto, modo="apenas_parser")
    
    if resultado.status == StatusExecucao.ERRO:
        raise HTTPException(status_code=500, detail=resultado.mensagem)
    
    return resultado.dados


@app.post("/plano")
def gerar_plano_endpoint(input_data: InputEstudante):
    """
    Gera plano de ações baseado no input do estudante.
    
    Retorna plano com ações e justificativas.
    """
    resultado = motor.executar(input_data.texto, modo="apenas_plano")
    
    if resultado.status == StatusExecucao.ERRO:
        raise HTTPException(status_code=500, detail=resultado.mensagem)
    
    return resultado.dados


@app.post("/aprovar")
def aprovar_plano_endpoint(aprovar_data: AprovacaoPlano):
    """
    Aprova plano e continua execução.
    
    Exemplo:
    {
        "plano": {...},
        "dados_tcc": {...},
        "aprovado": true,
        "feedback": ""
    }
    """
    if not aprovar_data.aprovado:
        return {
            "status": "reprovado",
            "mensagem": "Plano reprovado. Ajuste conforme feedback.",
            "feedback": aprovar_data.feedback
        }
    
    resultado = motor.continuar_execucao(
        aprovar_data.plano,
        aprovar_data.dados_tcc
    )
    
    if resultado.status == StatusExecucao.ERRO:
        raise HTTPException(status_code=500, detail=resultado.mensagem)
    
    return resultado.dados


@app.post("/fontes")
def adicionar_fonte_endpoint(fonte_data: FonteInput):
    """
    Adiciona fonte verificada à base de conhecimento.
    
    Anti-alucinação: só fontes adicionadas aqui podem ser citadas.
    """
    doc = Documento(
        id="",
        titulo=fonte_data.titulo,
        conteudo=fonte_data.conteudo,
        fonte=fonte_data.fonte,
        tipo=fonte_data.tipo,
        autor=fonte_data.autor,
        ano=fonte_data.ano
    )
    
    motor.adicionar_fonte(doc)
    
    return {
        "status": "adicionada",
        "fonte": fonte_data.titulo,
        "mensagem": "Fonte adicionada à base de conhecimento."
    }


@app.get("/fontes")
def listar_fontes_endpoint():
    """Lista todas as fontes disponíveis."""
    fontes = motor.base_conhecimento.listar_fontes()
    return {"total": len(fontes), "fontes": fontes}


@app.post("/verificar")
def verificar_texto_endpoint(texto: str):
    """
    Verifica texto usando os 4 verificadores.
    
    Retorna resultados de fontes, ABNT, linguagem e alucinação.
    """
    from src.verificadores import (
        verificador_fontes,
        verificador_abnt,
        verificador_linguagem,
        verificador_alucinacao
    )
    
    return {
        "fontes": {
            "passou": verificador_fontes.verificar(texto).passou,
            "score": verificador_fontes.verificar(texto).score,
            "mensagem": verificador_fontes.verificar(texto).mensagem
        },
        "abnt": {
            "passou": verificador_abnt.verificar(texto).passou,
            "score": verificador_abnt.verificar(texto, "").score,
            "mensagem": verificador_abnt.verificar(texto).mensagem
        },
        "linguagem": {
            "passou": verificador_linguagem.verificar(texto).passou,
            "score": verificador_linguagem.verificar(texto).score,
            "mensagem": verificador_linguagem.verificar(texto).mensagem
        },
        "alucinacao": {
            "passou": verificador_alucinacao.verificar(texto).passou,
            "score": verificador_alucinacao.verificar(texto).score,
            "mensagem": verificador_alucinacao.verificar(texto).mensagem
        }
    }
