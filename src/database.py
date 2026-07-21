from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Cria o arquivo do banco
engine = create_engine('sqlite:///tcc_database.db', connect_args={"check_same_thread": False})

# Base para definir tabelas
Base = declarative_base()

# Sessão para consultar e salvar
SessionLocal = sessionmaker(bind=engine)

# Tabela de TCCs
class TCC(Base):
    __tablename__ = "tccs"
    
    id = Column(Integer, primary_key=True)
    titulo = Column(String)
    tema = Column(String)
    estudante = Column(String)
    status = Column(String, default="em_andamento")
    criado_em = Column(DateTime, default=datetime.now)

# Cria as tabelas
Base.metadata.create_all(engine)
