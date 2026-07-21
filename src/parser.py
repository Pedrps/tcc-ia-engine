import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DadosTCC:
    """Estrutura dos dados extraídos do input do estudante."""
    tema: str
    area: Optional[str] = None
    objetivo_geral: Optional[str] = None
    delimitacao: Optional[str] = None
    palavras_chave: List[str] = None
    
    def __post_init__(self):
        if self.palavras_chave is None:
            self.palavras_chave = []


def parse_input(texto: str) -> DadosTCC:
    """
    Recebe texto livre do estudante e extrai dados estruturados.
    
    Exemplo de input:
    "Tema: Arquitetura sustentável em favelas. 
     Objetivo: Analisar estratégias bioclimáticas. 
     Delimitação: Favelas do Rio de Janeiro."
    """
    
    # Normaliza o texto
    texto = texto.lower().strip()
    
    # Extrai tema (após "tema:" ou primeira frase)
    tema = _extrair_tema(texto)
    
    # Extrai área do conhecimento
    area = _extrair_area(texto)
    
    # Extrai objetivo
    objetivo = _extrair_objetivo(texto)
    
    # Extrai delimitação
    delimitacao = _extrair_delimitacao(texto)
    
    # Extrai palavras-chave
    palavras = _extrair_palavras_chave(texto)
    
    return DadosTCC(
        tema=tema,
        area=area,
        objetivo_geral=objetivo,
        delimitacao=delimitacao,
        palavras_chave=palavras
    )


def _extrair_tema(texto: str) -> str:
    """Extrai tema do texto."""
    # Procura por "tema:" seguido de texto
    padrao = r'tema[:\s]+(.+?)(?:\.|\n|objetivo|delimitação)'
    match = re.search(padrao, texto, re.IGNORECASE)
    
    if match:
        return match.group(1).strip().capitalize()
    
    # Se não encontrar "tema:", pega primeira frase
    primeira_frase = texto.split('.')[0]
    return primeira_frase.strip().capitalize()


def _extrair_area(texto: str) -> Optional[str]:
    """Identifica área do conhecimento."""
    areas = {
        'arquitetura': ['arquitetura', 'urbanismo', 'paisagismo', 'construção'],
        'engenharia': ['engenharia', 'civil', 'estruturas', 'hidráulica'],
        'direito': ['direito', 'jurídico', 'legal', 'lei'],
        'saúde': ['saúde', 'medicina', 'enfermagem', 'psicologia'],
        'educação': ['educação', 'pedagogia', 'ensino', 'aprendizagem'],
        'tecnologia': ['tecnologia', 'computação', 'software', 'ia', 'inteligência artificial']
    }
    
    for area, palavras in areas.items():
        if any(p in texto for p in palavras):
            return area
    
    return None


def _extrair_objetivo(texto: str) -> Optional[str]:
    """Extrai objetivo geral."""
    padroes = [
        r'objetivo geral[:\s]+(.+?)(?:\.|\n)',
        r'objetivo[:\s]+(.+?)(?:\.|\n)',
    ]
    
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip().capitalize()
    
    return None


def _extrair_delimitacao(texto: str) -> Optional[str]:
    """Extrai delimitação do estudo."""
    padroes = [
        r'delimitação[:\s]+(.+?)(?:\.|\n)',
        r'delimitação do estudo[:\s]+(.+?)(?:\.|\n)',
        r'escopo[:\s]+(.+?)(?:\.|\n)',
    ]
    
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip().capitalize()
    
    return None


def _extrair_palavras_chave(texto: str) -> List[str]:
    """Extrai palavras-chave relevantes."""
    # Lista de palavras comuns em TCCs
    termos_tecnicos = [
        'sustentabilidade', 'bioclimática', 'favela', 'habitação',
        'eficiência energética', 'ventilação natural', 'material',
        'custo', 'metodologia', 'qualitativo', 'quantitativo',
        'estudo de caso', 'revisão bibliográfica', 'pesquisa de campo'
    ]
    
    encontradas = []
    for termo in termos_tecnicos:
        if termo in texto:
            encontradas.append(termo)
    
    return encontradas
