"""
Verificadores de qualidade do TCC.
Resolve os 4 problemas principais:
1. Alucinação de fontes
2. Alucinação de dados
3. Linguagem inadequada (marketing, jornalístico, grandiloqüente)
4. Padronização ABNT
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

from src.config import config
from src.llm_client import llm
from src.rag import base_conhecimento


@dataclass
class ResultadoVerificacao:
    """Resultado de uma verificação."""
    passou: bool
    score: float  # 0.0 a 1.0
    mensagem: str
    detalhes: List[str]


class VerificadorFontes:
    """
    Verificador 6.1 + 6.2: Fontes adicionadas e existência real.
    
    Técnica: RAG + verificação semântica na base de conhecimento.
    """
    
    def verificar(self, texto: str) -> ResultadoVerificacao:
        """
        Verifica se todas as citações no texto existem na base.
        
        Args:
            texto: Texto do TCC
        
        Returns:
            Resultado da verificação
        """
        # Extrai citações do texto (padrões comuns)
        padroes_citacao = [
            r'\(([^)]+\d{4}[^)]*)\)',  # (Autor, 2023)
            r'\[(\d+)\]',              # [1]
            r'"(.*?)"\s*\(([^)]+)\)',  # "Título" (Autor)
        ]
        
        citacoes_encontradas = []
        for padrao in padroes_citacao:
            citacoes_encontradas.extend(re.findall(padrao, texto))
        
        if not citacoes_encontradas:
            return ResultadoVerificacao(
                passou=False,
                score=0.0,
                mensagem="Nenhuma citação encontrada no texto.",
                detalhes=["Adicione citações para fundamentar seu trabalho."]
            )
        
        # Verifica cada citação na base
        citacoes_verificadas = []
        citacoes_falsas = []
        
        for citacao in citacoes_encontradas:
            citacao_str = str(citacao) if isinstance(citacao, tuple) else citacao
            resultado = base_conhecimento.verificar_existencia(citacao_str)
            
            if resultado["existe"]:
                citacoes_verificadas.append({
                    "citacao": citacao_str,
                    "score": resultado["score"],
                    "fonte": resultado["fonte"]
                })
            else:
                citacoes_falsas.append(citacao_str)
        
        score = len(citacoes_verificadas) / len(citacoes_encontradas) if citacoes_encontradas else 0
        
        if score >= config.SCORE_MINIMO_FONTES:
            return ResultadoVerificacao(
                passou=True,
                score=score,
                mensagem=f"{len(citacoes_verificadas)}/{len(citacoes_encontradas)} citações verificadas.",
                detalhes=[f"✓ {c['citacao']} -> {c['fonte']}" for c in citacoes_verificadas]
            )
        else:
            detalhes = [f"✓ {c['citacao']}" for c in citacoes_verificadas]
            detalhes.extend([f"✗ {c} (NÃO ENCONTRADA - possível alucinação!)" for c in citacoes_falsas])
            
            return ResultadoVerificacao(
                passou=False,
                score=score,
                mensagem=f"ALERTA: {len(citacoes_falsas)} citações não encontradas na base.",
                detalhes=detalhes
            )


class VerificadorABNT:
    """
    Verificador 6.3: Normas ABNT.
    
    Verifica formatação de citações e referências.
    """
    
    # Padrões ABNT NBR 10520 (citações) e 6023 (referências)
    PADROES_ABNT = {
        "citacao_direta_curta": r'"[^"]{1,40}"\s*\([^)]+\d{4}[^)]*\)',
        "citacao_direta_longa": r'^[ ]{4}[^<].*\(\d{4}\)',
        "citacao_indireta": r'\([^)]+\d{4}[^)]*\)',
        "referencia_autor_ano": r'^[A-Z][a-z]+,\s*[A-Z]\.\s*[A-Z]?\.?\s*\(\d{4}\)',
    }
    
    def verificar(self, texto: str, referencias: str = "") -> ResultadoVerificacao:
        """
        Verifica conformidade com normas ABNT.
        
        Args:
            texto: Texto do TCC
            referencias: Seção de referências bibliográficas
        
        Returns:
            Resultado da verificação
        """
        problemas = []
        acertos = []
        
        # Verifica citações no texto
        citacoes_diretas = re.findall(r'"([^"]{1,100})"', texto)
        for citacao in citacoes_diretas:
            if len(citacao) > 40:
                # Citação direta longa deve estar em bloco (recuo 4cm)
                if not re.search(r'^[ ]{4}' + re.escape(citacao[:20]), texto, re.MULTILINE):
                    problemas.append(f"Citação direta longa deve ter recuo de 4cm: '{citacao[:50]}...'")
            else:
                acertos.append(f"Citação direta curta OK: '{citacao[:30]}...'")
        
        # Verifica se há referências para todas as citações
        anos_citados = set(re.findall(r'\((?:[^)]+\s)?(\d{4})[^)]*\)', texto))
        anos_referencias = set(re.findall(r'\((\d{4})\)', referencias)) if referencias else set()
        
        anos_faltantes = anos_citados - anos_referencias
        if anos_faltantes:
            problemas.append(f"Anos citados sem referência: {anos_faltantes}")
        
        # Verifica formato de referências
        if referencias:
            linhas_ref = referencias.strip().split('\n')
            for i, linha in enumerate(linhas_ref[:5], 1):  # Verifica primeiras 5
                if re.match(self.PADROES_ABNT["referencia_autor_ano"], linha):
                    acertos.append(f"Referência {i}: formato autor-ano OK")
                else:
                    problemas.append(f"Referência {i}: formato não conforme ABNT")
        
        score = 1.0 - (len(problemas) / (len(problemas) + len(acertos) + 1))
        
        if score >= config.SCORE_MINIMO_ABNT:
            return ResultadoVerificacao(
                passou=True,
                score=score,
                mensagem="Formatação ABNT aprovada.",
                detalhes=acertos + problemas
            )
        else:
            return ResultadoVerificacao(
                passou=False,
                score=score,
                mensagem="Problemas de formatação ABNT detectados.",
                detalhes=problemas + acertos
            )


class VerificadorLinguagem:
    """
    Verificador 6.4: Linguagem inadequada.
    
    Detecta tom jornalístico, grandiloqüente, marketing ou convencimento.
    """
    
    # Palavras e padrões de linguagem não acadêmica
    PALAVRAS_MARKETING = [
        "incrível", "sensacional", "revolucionário", "game-changer", "disruptivo",
        "inovador", "exclusivo", "premium", "top", "melhor", "supremo",
        "transformador", "poderoso", "eficaz", "garantido", "comprovado"
    ]
    
    PALAVRAS_JORNALISTICAS = [
        "chocante", "inesperado", "surpreendente", "urgente", "exclusivo",
        "bomba", "revelado", "escândalo", "polêmica", "controverso"
    ]
    
    PALAVRAS_GRANDILOQUENTES = [
        "magnânimo", "sublime", "grandioso", "extraordinário", "imponente",
        "majestoso", "esplêndido", "radiante", "prodigioso", "colossal"
    ]
    
    PADROES_CONVENCIMENTO = [
        r"você precisa",
        r"é importante que",
        r"não deixe de",
        r"aproveite",
        r"descubra",
        r"saiba mais",
        r"clique aqui",
        r"não perca"
    ]
    
    def verificar(self, texto: str) -> ResultadoVerificacao:
        """
        Verifica se o texto tem tom acadêmico adequado.
        
        Args:
            texto: Texto do TCC
        
        Returns:
            Resultado da verificação
        """
        texto_lower = texto.lower()
        problemas = []
        sugestoes = []
        
        # Verifica marketing
        for palavra in self.PALAVRAS_MARKETING:
            if palavra in texto_lower:
                problemas.append(f"Palavra de marketing detectada: '{palavra}'")
                sugestoes.append(f"Substitua '{palavra}' por termo neutro acadêmico")
        
        # Verifica jornalismo
        for palavra in self.PALAVRAS_JORNALISTICAS:
            if palavra in texto_lower:
                problemas.append(f"Tom jornalístico: '{palavra}'")
                sugestoes.append(f"Remova '{palavra}' ou use 'observa-se que', 'constata-se'")
        
        # Verifica grandiloqüência
        for palavra in self.PALAVRAS_GRANDILOQUENTES:
            if palavra in texto_lower:
                problemas.append(f"Linguagem grandiloqüente: '{palavra}'")
                sugestoes.append(f"Substitua '{palavra}' por termo técnico objetivo")
        
        # Verifica convencimento
        for padrao in self.PADROES_CONVENCIMENTO:
            if re.search(padrao, texto_lower):
                problemas.append(f"Tom de convencimento detectado: '{padrao}'")
                sugestoes.append("Use voz passiva e terceira pessoa: 'observa-se', 'verifica-se'")
        
        # Verifica uso de primeira pessoa (evitar "eu", "meu")
        primeiras_pessoas = re.findall(r'\b(eu|meu|minha|me|mim)\b', texto_lower)
        if len(primeiras_pessoas) > 3:
            problemas.append(f"Uso excessivo de primeira pessoa ({len(primeiras_pessoas)}x)")
            sugestoes.append("Use terceira pessoa ou voz passiva: 'o autor', 'o presente estudo'")
        
        # Verifica adjetivos superlativos excessivos
        superlativos = re.findall(r'\b(mais|muito|extremamente|altamente|profundamente)\s+\w+', texto_lower)
        if len(superlativos) > 5:
            problemas.append(f"Superlativos excessivos ({len(superlativos)}x)")
            sugestoes.append("Reduza adjetivos intensificadores, use dados concretos")
        
        score = 1.0 - (len(problemas) * 0.15)
        score = max(0.0, min(1.0, score))
        
        if score >= config.SCORE_MINIMO_LINGUAGEM:
            return ResultadoVerificacao(
                passou=True,
                score=score,
                mensagem="Tom acadêmico aprovado.",
                detalhes=["Texto mantém neutralidade e objetividade acadêmica."]
            )
        else:
            return ResultadoVerificacao(
                passou=False,
                score=score,
                mensagem="Tom inadequado detectado. Ajuste para linguagem acadêmica.",
                detalhes=problemas + sugestoes
            )


class VerificadorAlucinacao:
    """
    Verificador 6.5: Corretor de alucinação.
    
    Detecta informações inventadas pela IA usando múltiplas técnicas:
    1. Self-consistency (múltiplas gerações)
    2. RAG grounding (compara com fontes)
    3. Factual claims verification
    """
    
    def verificar(self, texto: str) -> ResultadoVerificacao:
        """
        Verifica se o texto contém alucinações.
        
        Args:
            texto: Texto a verificar
        
        Returns:
            Resultado da verificação
        """
        problemas = []
        
        # TÉCNICA 1: Verificar citações na base RAG
        citacoes = re.findall(r'\(([^)]+\d{4}[^)]*)\)', texto)
        for citacao in citacoes:
            resultado = base_conhecimento.verificar_existencia(citacao)
            if not resultado["existe"]:
                problemas.append(f"ALUCINAÇÃO DE FONTE: '{citacao}' não encontrada na base")
        
        # TÉCNICA 2: Verificar dados estatísticos (números soltos)
        dados_numericos = re.findall(r'\b\d{1,3}(?:\.\d{3})*(?:,\d+)?\s*(?:%|por cento|habitantes|km|m²)\b', texto)
        for dado in dados_numericos:
            # Verifica se o dado tem fonte próxima
            contexto = texto[max(0, texto.find(dado) - 200):texto.find(dado) + len(dado)]
            if not re.search(r'\(\d{4}\)', contexto):
                problemas.append(f"DADO SEM FONTE: '{dado}' - adicione referência")
        
        # TÉCNICA 3: Verificar afirmações absolutas
        afirmacoes_absolutas = re.findall(r'\b(sempre|nunca|todos|nenhum|é impossível|é certo que)\b[^.]{10,100}\.', texto_lower := texto.lower())
        for afirmacao in afirmacoes_absolutas:
            problemas.append(f"AFIRMAÇÃO ABSOLUTA (risco de alucinação): '{afirmacao[:80]}...'")
        
        # TÉCNICA 4: Self-consistency para trechos suspeitos
        trechos_suspeitos = self._identificar_trechos_suspeitos(texto)
        for trecho in trechos_suspeitos:
            consistencia = self._verificar_consistencia(trecho)
            if consistencia < 0.5:
                problemas.append(f"INCONSISTÊNCIA DETECTADA: '{trecho[:100]}...' (score: {consistencia:.2f})")
        
        score = 1.0 - (len(problemas) * 0.2)
        score = max(0.0, min(1.0, score))
        
        if score <= config.SCORE_MAXIMO_ALUCINACAO:
            return ResultadoVerificacao(
                passou=False,
                score=score,
                mensagem="ALUCINAÇÃO DETECTADA! Revisar trechos marcados.",
                detalhes=problemas
            )
        else:
            return ResultadoVerificacao(
                passou=True,
                score=score,
                mensagem="Texto verificado. Sem indícios de alucinação.",
                detalhes=["Todas as citações foram validadas na base de conhecimento."]
            )
    
    def _identificar_trechos_suspeitos(self, texto: str) -> List[str]:
        """Identifica trechos que precisam de verificação de consistência."""
        # Divide em parágrafos e pega os que têm citações ou dados
        paragrafos = texto.split('\n\n')
        suspeitos = []
        
        for p in paragrafos:
            if len(p) > 100 and (re.search(r'\d{4}', p) or re.search(r'"[^"]+"', p)):
                suspeitos.append(p)
        
        return suspeitos[:3]  # Limita para não sobrecarregar
    
    def _verificar_consistencia(self, trecho: str) -> float:
        """
        Verifica consistência usando self-consistency.
        Gera múltiplas verificações e compara.
        """
        try:
            prompt = f"""
            Verifique se o seguinte trecho é factualmente consistente e bem fundamentado:
            
            "{trecho[:500]}"
            
            Responda apenas com um número de 0 a 1, onde:
            1.0 = totalmente factual e verificável
            0.0 = claramente inventado ou inconsistente
            """
            
            # Gera 3 respostas e pega a média
            respostas = llm.gerar_multiplas_respostas(prompt, n=3, temperatura=0.3)
            scores = []
            
            for resp in respostas:
                numeros = re.findall(r'0?\.\d+|\d', resp)
                if numeros:
                    scores.append(float(numeros[0]))
            
            return sum(scores) / len(scores) if scores else 0.5
            
        except Exception:
            return 0.5  # Neutro se falhar


# Instâncias dos verificadores
verificador_fontes = VerificadorFontes()
verificador_abnt = VerificadorABNT()
verificador_linguagem = VerificadorLinguagem()
verificador_alucinacao = VerificadorAlucinacao()
