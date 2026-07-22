"""
RAG (Retrieval-Augmented Generation) com embeddings semânticos.
Base de conhecimento que impede alucinação: IA só usa fontes verificadas.
"""

import os
import hashlib
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from src.config import config


@dataclass
class Documento:
    """Documento/fonte na base de conhecimento."""
    id: str
    titulo: str
    conteudo: str
    fonte: str
    tipo: str
    autor: str = ""
    ano: int = 0


class BaseConhecimento:
    """
    Base de conhecimento com busca semântica via embeddings.
    
    Técnica anti-alucinação: IA só pode citar documentos que existem aqui.
    """
    
    def __init__(self):
        # Modelo de embeddings (converte texto em vetores numéricos)
        self.modelo_embeddings = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # Cliente ChromaDB (banco vetorial)
        self.cliente_chroma = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="data/chroma"
        ))
        
        # Coleção de documentos
        self.colecao = self.cliente_chroma.get_or_create_collection(
            name=config.CHROMA_COLLECTION
        )
        
        # Cache de documentos em memória
        self.documentos: Dict[str, Documento] = {}
        
        # Cria pasta se não existir
        os.makedirs("data/fontes", exist_ok=True)
    
    def _gerar_id(self, texto: str) -> str:
        """Gera ID único baseado no conteúdo."""
        return hashlib.md5(texto.encode()).hexdigest()[:16]
    
    def _gerar_embedding(self, texto: str) -> List[float]:
        """Converte texto em vetor numérico (embedding)."""
        embedding = self.modelo_embeddings.encode(texto)
        return embedding.tolist()
    
    def adicionar_documento(self, doc: Documento) -> None:
        """
        Adiciona documento à base com embedding semântico.
        
        Args:
            doc: Documento a ser adicionado
        """
        # Gera ID se não fornecido
        doc_id = doc.id or self._gerar_id(doc.conteudo)
        
        # Gera embedding do conteúdo
        embedding = self._gerar_embedding(doc.conteudo)
        
        # Adiciona ao ChromaDB
        self.colecao.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[doc.conteudo],
            metadatas=[{
                "titulo": doc.titulo,
                "fonte": doc.fonte,
                "tipo": doc.tipo,
                "autor": doc.autor,
                "ano": doc.ano
            }]
        )
        
        # Guarda em memória
        self.documentos[doc_id] = doc
        
        # Salva arquivo de backup
        caminho = os.path.join("data/fontes", f"{doc_id}.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(f"TITULO: {doc.titulo}\n")
            f.write(f"AUTOR: {doc.autor}\n")
            f.write(f"ANO: {doc.ano}\n")
            f.write(f"FONTE: {doc.fonte}\n")
            f.write(f"TIPO: {doc.tipo}\n")
            f.write(f"CONTEUDO:\n{doc.conteudo}\n")
    
    def buscar(self, query: str, max_resultados: int = 5) -> List[Documento]:
        """
        Busca documentos semanticamente similares à query.
        
        Args:
            query: Texto de busca
            max_resultados: Quantidade máxima de resultados
        
        Returns:
            Lista de documentos mais relevantes
        """
        # Gera embedding da query
        embedding_query = self._gerar_embedding(query)
        
        # Busca no ChromaDB
        resultados = self.colecao.query(
            query_embeddings=[embedding_query],
            n_results=max_resultados
        )
        
        documentos = []
        if resultados["ids"]:
            for i, doc_id in enumerate(resultados["ids"][0]):
                metadata = resultados["metadatas"][0][i]
                documentos.append(Documento(
                    id=doc_id,
                    titulo=metadata["titulo"],
                    conteudo=resultados["documents"][0][i],
                    fonte=metadata["fonte"],
                    tipo=metadata["tipo"],
                    autor=metadata.get("autor", ""),
                    ano=metadata.get("ano", 0)
                ))
        
        return documentos
    
    def buscar_por_similaridade(
        self,
        texto: str,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Busca documentos com score de similaridade acima do threshold.
        
        Args:
            texto: Texto para comparar
            threshold: Score mínimo de similaridade (0 a 1)
        
        Returns:
            Lista de documentos com scores
        """
        embedding = self._gerar_embedding(texto)
        
        resultados = self.colecao.query(
            query_embeddings=[embedding],
            n_results=10,
            include=["distances"]
        )
        
        documentos_com_score = []
        if resultados["ids"]:
            for i, doc_id in enumerate(resultados["ids"][0]):
                # Converte distância em similaridade (1 - distância normalizada)
                distancia = resultados["distances"][0][i]
                similaridade = 1 / (1 + distancia)  # Transformação sigmoide
                
                if similaridade >= threshold:
                    metadata = resultados["metadatas"][0][i]
                    documentos_com_score.append({
                        "documento": Documento(
                            id=doc_id,
                            titulo=metadata["titulo"],
                            conteudo=resultados["documents"][0][i],
                            fonte=metadata["fonte"],
                            tipo=metadata["tipo"],
                            autor=metadata.get("autor", ""),
                            ano=metadata.get("ano", 0)
                        ),
                        "score": similaridade
                    })
        
        return documentos_com_score
    
    def verificar_existencia(self, citacao: str, threshold: float = 0.6) -> Dict:
        """
        Verifica se uma citação existe na base (anti-alucinação).
        
        Técnica: busca semântica + threshold de similaridade.
        
        Args:
            citacao: Texto da citação a verificar
            threshold: Score mínimo para considerar existente
        
        Returns:
            Dict com existe (bool), score e fonte
        """
        resultados = self.buscar_por_similaridade(citacao, threshold)
        
        if resultados:
            melhor = max(resultados, key=lambda x: x["score"])
            return {
                "existe": True,
                "score": melhor["score"],
                "fonte": melhor["documento"].titulo,
                "autor": melhor["documento"].autor,
                "ano": melhor["documento"].ano
            }
        
        return {
            "existe": False,
            "score": 0.0,
            "fonte": None,
            "autor": None,
            "ano": None
        }
    
    def listar_fontes(self) -> List[str]:
        """Lista todas as fontes disponíveis."""
        return [f"{d.titulo} ({d.fonte})" for d in self.documentos.values()]


# Instância global
base_conhecimento = BaseConhecimento()
