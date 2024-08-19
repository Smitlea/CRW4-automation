
import datetime
import os

from dotenv import load_dotenv
from sqlalchemy import Column, Boolean, Integer, Float, String, func, TIMESTAMP
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
SQL_URL=os.environ.get("SQL_SERVER")
Base = declarative_base()


class DatabaseManager:
    def __init__(self):
        self.engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)
        self.Base = declarative_base()

    def _create_engine(self):
        engine_url = f"{SQL_URL}?charset=utf8mb4"
        return create_engine(engine_url)


class BaseTable():
    __table_args__ = {
        "mysql_charset": "utf8mb4"
    }
    id = Column(Integer, nullable=False, primary_key=True)
    ttimestamp = Column(TIMESTAMP, nullable=False, default=func.now())


class TestTable(BaseTable, Base): 
    __tablename__ = "TestTable"
    cas = Column(String(40), nullable=False)
    

if __name__ == "__main__":
    # Load env variable
    dotenv_path = f"{os.path.dirname(os.path.abspath(__file__))}/.env"
    if os.path.exists(dotenv_path):
        load_dotenv(f"{os.path.dirname(os.path.abspath(__file__))}/.env")

    engine = create_engine(SQL_URL, echo=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)