from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./db.sqlite3"
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    from app.models.user import Cliente
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
