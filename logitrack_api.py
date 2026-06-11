import jwt, os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from passlib.context import CryptContext

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
# -------------------------------------------------------------------------------------------------------------------------------
# Pull the configuration values dynamically from the environment
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256") # Fallback to HS256 if not specified
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing!")
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Database Setup
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# ORM Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    assigned_hub = Column(String, nullable=True)

    # Relationship Link: Tells SQLAlchemy to automatically pull all logs tied to this user
    logs = relationship("TrackingLog", back_populates="creator")


class TrackingLog(Base):
    __tablename__ = "tracking_logs"
    # Define the exact columns as Python attributes
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String, index=True)
    sku = Column(String, index=True)
    package_count = Column(Integer)
    weight_grams = Column(Integer)
    hub = Column(String, nullable=True)
    # 1. The Physical Constraint: Stores the ID of the user who made this log
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 2. The Python Conceptual Link: Lets you write `log.creator.username` instantly
    creator = relationship("User", back_populates="logs")

Base.metadata.create_all(bind=engine)
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Schemas (Pydantic)
class UserPassModel(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    assigned_hub: str | None = Field(None, max_length=100)


class LogIngestionModel(BaseModel):
    tracking_number: str = Field(..., min_length=1, max_length=50)
    sku: str = Field(..., min_length=1, max_length=50)
    package_count : int = Field(..., ge=0, le=999)
    weight_grams: int = Field(..., gt=0)
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Security Helpers
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    # Takes a dictionary payload, appends an expiration window, and signs it using the global secret key.
    # Create a copy of the payload to prevent mutating original data
    to_encode = data.copy()    
    #Calculate the exact expiration time stamp (e.g., 30 minutes from right now)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)    
    #Inject the standard 'exp' claim into the token structure
    to_encode.update({"exp": expire})    
    #Sign the payload using the secret key and algorithm
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)    
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print("HERE")
        # Decode the token using our system secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username  # Return the validated username context
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Dependency: Opens a session for a network request, and safely closes it when finished
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# App & Routes       
app = FastAPI()

@app.post("/register")
def register(payload: UserPassModel, db: Session = Depends(get_db)):
    reg_log = User(
        username = payload.username,
        hashed_password = hash_password(payload.password),
        name=payload.name,
        assigned_hub=payload.assigned_hub
    )
    db.add(reg_log)
    db.commit()
    db.refresh(reg_log)

    return {"status": "success", "inserted_id": reg_log.id, "record": payload}


@app.post("/login")
def login(payload: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_record = db.query(User).filter(User.username == payload.username).first()

    if not user_record or not verify_password(payload.password, user_record.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    else:
        # SUCCESS PATHWAY: Package the non-sensitive public user claims
        token_claims = {
        "sub": user_record.username,        # 'sub' stands for Subject (The user's unique identity)
        "user_id": user_record.id
        }
        # Generate the signed token string
        access_token = create_access_token(data=token_claims)
        # Return the token in the strict OAuth2 specification standard
        return {
        "access_token": access_token,
        "token_type": "bearer"
        }
    
@app.post("/logs")
def write_log(
    payload: LogIngestionModel,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user) # The gateway guard
    ):    
    # Query the database to find the actual User record for this token
    user_record = db.query(User).filter(User.username == current_user).first()

    # If the execution reaches this line, the token is 100% valid!
    new_log = TrackingLog(
        tracking_number=payload.tracking_number,
        sku = payload.sku,
        package_count = payload.package_count,
        weight_grams = payload.weight_grams,
        hub = user_record.assigned_hub,
        user_id=user_record.id
    )
    db.add(new_log)
    db.commit()    
    db.refresh(new_log)
    return {
        "status": "success", 
        "inserted_id": new_log.id,
        "owner_id": new_log.user_id
    }