from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Field, SQLModel, Session, create_engine, select
from typing import Optional, List
import uuid
import os
# Replace this with your noenDB connection string if needed.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite")
engine = create_engine(DATABASE_URL, echo=True)

# Define the APIKey model.
class APIKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True)

# Define the Book model.
class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str

# Define the Book model.
class Question(SQLModel):
    query : str

### Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")


# Create tables on startup.
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Dependency to get a session.
def get_session():
    with Session(engine) as session:
        yield session

# Setup the HTTP Bearer security scheme.
security = HTTPBearer()

# Dependency to verify API key from Authorization header.
def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    session: Session = Depends(get_session),
):
    token = credentials.credentials
    statement = select(APIKey).where(APIKey.key == token)
    api_key = session.exec(statement).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )
    return token

# Endpoint to generate a new API key and store it in the database.
@app.post("/apikeys/generate")
def generate_api_key(session: Session = Depends(get_session)):
    new_key = str(uuid.uuid4())
    api_key = APIKey(key=new_key)
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return {"api_key": new_key}

# Endpoint to fetch book data; requires a valid API key.
@app.get("/books", response_model=List[Book])
def read_books(
    session: Session = Depends(get_session), token: str = Depends(verify_api_key)
):
    books = session.exec(select(Book)).all()
    return books


# Optional: Endpoint to add a book (for testing).
@app.post("/books", response_model=Book)
def add_book(book: Book, session: Session = Depends(get_session)):
    session.add(book)
    session.commit()
    session.refresh(book)
    return book
