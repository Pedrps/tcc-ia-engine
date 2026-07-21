from dataclasses import dataclass, field
from typing import List, Optional
from src.parser import DadosTCC


@dataclass
class Acao:
    """Uma ação do plano."""
    ordem: int
    descricao: str
    tipo: str  # "busca_fontes", "escrita", "revisao", "verificacao"
    dependencias: List[int] = field(default_factory=list)
    status: str = "pendente"  # pendente, em_andamento, concluida


@dataclass
class Plano:
    """Plano completo de ações."""
    tema: str
    acoes: List[Acao]
    justificativas: dict = field(default_factory=dict)


def gerar_plano(dados: DadosTCC) -> Plano:
    """
    Recebe dados do TCC e gera plano de ações.
    """
    acoes = []
    justificativas = {}
    
    # AÇÃO 1: Buscar fontes teóricas
    acoes.append(Acao(
        ordem=1,
        descricao=f"Buscar referências teóricas sobre {dados.tema}",
        tipo="busca_fontes",
        dependencias=[]
    ))
    justificativas[1] = f"Base teórica necessária para fundamentar o tema '{dados.tema}'"
    
    # AÇÃO 2: Buscar normas técnicas (se for arquitetura/engenharia)
    if dados.area in ["arquitetura", "engenharia"]:
        acoes.append(Acao(
            ordem=2,
            descricao="Pesquisar normas ABNT e legislação aplicável",
            tipo="busca_fontes",
            dependencias=[1]
        ))
        justificativas[2] = "Normas técnicas são obrigatórias para projetos na área construída"
    
    # AÇÃO 3: Buscar estudos de caso
    acoes.append(Acao(
        ordem=3,
        descricao=f"Coletar estudos de caso sobre {dados.tema}",
        tipo="busca_fontes",
        dependencias=[1]
    ))
    justificativas[3] = "Estudos de caso fornecem referência prática e comparativos"
    
    # AÇÃO 4: Escrever introdução
    acoes.append(Acao(
        ordem=4,
        descricao="Escrever capítulo 1 - Introdução",
        tipo="escrita",
        dependencias=[1, 2, 3]
    ))
    justificativas[4] = "Introdução contextualiza o tema e apresenta o problema"
    
    # AÇÃO 5: Escrever revisão bibliográfica
    acoes.append(Acao(
        ordem=5,
        descricao="Escrever capítulo 2 - Revisão Bibliográfica",
        tipo="escrita",
        dependencias=[1, 3]
    ))
    justificativas[5] = "Revisão sistematiza o conhecimento existente sobre o tema"
    
    # AÇÃO 6: Escrever metodologia (se houver objetivo)
    if dados.objetivo_geral:
        acoes.append(Acao(
            ordem=6,
            descricao="Escrever capítulo 3 - Metodologia",
            tipo="escrita",
            dependencias=[4]
        ))
        justificativas[6] = f"Metodologia define como atingir o objetivo: {dados.objetivo_geral}"
    
    # AÇÃO 7: Verificação de fontes
    acoes.append(Acao(
        ordem=7,
        descricao="Verificar se todas as fontes foram adicionadas corretamente",
        tipo="verificacao",
        dependencias=[4, 5]
    ))
    justificativas[7] = "Garante rastreabilidade e evita plágio"
    
    # AÇÃO 8: Verificação ABNT
    acoes.append(Acao(
        ordem=8,
        descricao="Verificar formatação ABNT das citações e referências",
        tipo="verificacao",
        dependencias=[7]
    ))
    justificativas[8] = "Conformidade com normas acadêmicas é obrigatória"
    
    # AÇÃO 9: Análise qualitativa
    acoes.append(Acao(
        ordem=9,
        descricao="Analisar qualitativamente os parágrafos e identificar lacunas",
        tipo="revisao",
        dependencias=[4, 5, 6] if dados.objetivo_geral else [4, 5]
    ))
    justificativas[9] = "Análise qualitativa identifica gaps no argumento"
    
    return Plano(
        tema=dados.tema,
        acoes=acoes,
        justificativas=justificativas
    )


def plano_para_dict(plano: Plano) -> dict:
    """Converte plano para dicionário (para JSON/API)."""
    return {
        "tema": plano.tema,
        "total_acoes": len(plano.acoes),
        "acoes": [
            {
                "ordem": a.ordem,
                "descricao": a.descricao,
                "tipo": a.tipo,
                "status": a.status,
                "dependencias": a.dependencias,
                "justificativa": plano.justificativas.get(a.ordem, "")
            }
            for a in plano.acoes
        ]
    }
