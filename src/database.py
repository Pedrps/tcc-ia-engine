"""
Banco de dados principal do sistema.
Guarda TCCs, planos, versões de texto e fontes verificadas.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Cria engine SQLite (arquivo local)
engine = create_engine(
    'sqlite:///tcc_database.db',
    connect_args={"check_same_thread": False}
)

# Base para criar tabelas como classes
Base = declarative_base()

# Fábrica de sessões
SessionLocal = sessionmaker(bind=engine)


class TCC(Base):
    """Tabela de TCCs."""
    __tablename__ = "tccs"
    
    id = Column(Integer, primary_key=True)
    titulo = Column(String(500))
    tema = Column(String(500))
    area = Column(String(100))
    estudante = Column(String(200))
    status = Column(String(50), default="em_andamento")
    criado_em = Column(DateTime, default=datetime.now)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    planos = relationship("PlanoDB", back_populates="tcc")
    versoes = relationship("Versao", back_populates="tcc")


class PlanoDB(Base):
    """Tabela de planos de ação."""
    __tablename__ = "planos"
    
    id = Column(Integer, primary_key=True)
    tcc_id = Column(Integer, ForeignKey("tccs.id"))
    descricao = Column(Text)
    tipo = Column(String(50))
    status = Column(String(50), default="pendente")
    ordem = Column(Integer)
    justificativa = Column(Text)
    criado_em = Column(DateTime, default=datetime.now)
    
    tcc = relationship("TCC", back_populates="planos")


class Versao(Base):
    """Tabela de versões de texto."""
    __tablename__ = "versoes"
    
    id = Column(Integer, primary_key=True)
    tcc_id = Column(Integer, ForeignKey("tccs.id"))
    conteudo = Column(Text)
    tipo = Column(String(50))
    score_qualidade = Column(Float, default=0.0)
    criado_em = Column(DateTime, default=datetime.now)
    
    tcc = relationship("TCC", back_populates="versoes")


class FonteVerificada(Base):
    """Tabela de fontes verificadas (anti-alucinação)."""
    __tablename__ = "fontes_verificadas"
    
    id = Column(Integer, primary_key=True)
    titulo = Column(String(500))
    autor = Column(String(300))
    ano = Column(Integer)
    url = Column(String(1000))
    conteudo_resumo = Column(Text)
    confiabilidade = Column(Float, default=1.0)  # 0.0 a 1.0
    criado_em = Column(DateTime, default=datetime.now)


# Cria tabelas
Base.metadata.create_all(engine)
