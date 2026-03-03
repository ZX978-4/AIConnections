import os
from dotenv import load_dotenv

# 加载 .env 文件中的变量
load_dotenv()


class Config:
    # Hugging Face 配置
    HF_TOKEN = os.getenv("HF_TOKEN", "")

    # SQLite 配置
    SQLITE_DB = "ai_supply_chain.db"

    # Neo4j 配置
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")