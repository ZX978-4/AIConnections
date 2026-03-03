import sqlite3
from neo4j import GraphDatabase
from config import Config


class DatabaseManager:
    def __init__(self):
        # 初始化 SQLite
        self.sqlite_conn = sqlite3.connect(Config.SQLITE_DB, check_same_thread=False)
        self._init_sqlite()

        # 初始化 Neo4j
        self.neo4j_driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )

    def _init_sqlite(self):
        cursor = self.sqlite_conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS models
                          (
                              id
                              TEXT
                              PRIMARY
                              KEY,
                              author
                              TEXT,
                              downloads
                              INTEGER,
                              processed
                              INTEGER
                              DEFAULT
                              0
                          )''')
        self.sqlite_conn.commit()

    def save_model_info(self, m_id, author, downloads):
        """存入 SQLite 详情"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO models (id, author, downloads, processed) VALUES (?, ?, ?, 1)",
                       (m_id, author, downloads))
        self.sqlite_conn.commit()

    def add_relation(self, source, target, rel_type):
        """存入 Neo4j 关系图谱"""
        with self.neo4j_driver.session() as session:
            # Cypher 语句：MERGE 保证不重复创建
            query = (
                f"MERGE (s:Model {{id: $source}}) "
                f"MERGE (t:Entity {{id: $target}}) "
                f"MERGE (s)-[:{rel_type}]->(t)"
            )
            session.run(query, source=source, target=target)

    def close(self):
        self.sqlite_conn.close()
        self.neo4j_driver.close()