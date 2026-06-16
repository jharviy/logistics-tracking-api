import jwt, os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
import bcrypt

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
    username: str = Field(default="admin", max_length=50)
    password: str = Field(default="password123", min_length=1, max_length=50)
    name: str = Field(default="admin name", min_length=1, max_length=100)
    assigned_hub: str | None = Field(default="Manila Hub", max_length=100)


class LogIngestionModel(BaseModel):
    tracking_number: str = Field(default = "TRK-20240611-001", min_length=1, max_length=50)
    sku: str = Field(default = "SKU-LAPTOP-001", min_length=1, max_length=50)
    package_count : int = Field(default = 3, ge=0, le=999)
    weight_grams: int = Field(default = 1500, gt=0)
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Security Helpers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()    
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)    
    to_encode.update({"exp": expire})    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)    

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
        
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
# App    

app = FastAPI(
    title="LogiTrack API",
    description="""
## LogiTrack — Shipment Tracking API

A backend REST API for managing shipment logs across logistics hubs, built with **FastAPI**, **PostgreSQL**, and **JWT authentication**.

---

### How To Try

Follow these steps in order:

**Step 1 — Create an account**
Go to `POST /register` → click **Try it out** → click **Execute**.
Default values are pre-filled for you.

**Step 2 — Log in**
Click the **🔒 Authorize** button at the top right.
Enter your username and password → click **Authorize**.

**Step 3 — Submit a shipment log**
Go to `POST /logs` → click **Try it out** → fill in the fields → click **Execute**.

**Step 4 — View the database**
Go to `GET /tracking_database` → click **Try it out** → **Execute** to see all shipment records.

---

> Want a friendlier interface? Visit the **[Live Demo Page](/)** instead.
    """,
    # version="1.0.0",
    # contact={
    #     "name": "LogiTrack Project",
    #     "url": "https://github.com/jharviy/logistics-tracking-api",
    # },
    swagger_ui_parameters={"persistAuthorization": True},
)

app.mount("/static", StaticFiles(directory="static"), name="static")
# app = FastAPI(swagger_ui_parameters={"persistAuthorization": True})

# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Routes  
@app.get("/", response_class=FileResponse, include_in_schema=False)
def demo_page():
    return FileResponse("static/demo.html")


@app.post("/register",tags=["Create Account"])
def register(payload: UserPassModel, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{payload.username}' is already taken. Try a different one."
        )
    user = User(
        username = payload.username,
        hashed_password = hash_password(payload.password),
        name=payload.name,
        assigned_hub=payload.assigned_hub
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"status": "success", "inserted_id": user.id, "record": payload}


@app.post("/login",tags=["Authentication"], include_in_schema=False)
# @app.post("/login", tags=["Authenticate"], summary="Log in and get an access token", description="Enter your username and password to receive a JWT token. Then click the 🔒 Authorize button and paste it.")
def login(payload: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    else:
        # SUCCESS PATHWAY: Package the non-sensitive public user claims
        token_claims = {"sub": user.username, "user_id": user.id}
        access_token = create_access_token(data=token_claims)
        return {"access_token": access_token, "token_type": "bearer"}


@app.post("/logs", tags=["Shipment Tracking"], summary="Submit a shipment log", description="Requires authentication. The hub is automatically assigned from your account profile.")
def write_log(
    payload: LogIngestionModel,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user) # The gateway guard
    ):    
    user = db.query(User).filter(User.username == current_user).first()
    # If the execution reaches this line, the token is 100% valid!
    new_log = TrackingLog(
        tracking_number=payload.tracking_number,
        sku = payload.sku,
        package_count = payload.package_count,
        weight_grams = payload.weight_grams,
        hub = user.assigned_hub,
        user_id=user.id
    )
    db.add(new_log)
    db.commit()    
    db.refresh(new_log)
    return {
        "status": "success", 
        "inserted_id": new_log.id,
        "owner_id": new_log.user_id
    }


@app.get("/tracking_database", tags=["View Database"], summary="View all shipment logs", description="Returns all shipment records in the database. Requires authentication.")
def show_tracking_database(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    logs = db.query(TrackingLog).all()
    return logs


@app.get("/users_database", tags=["View Database"], summary="View all registered users", description="Returns all registered users — passwords excluded. Public endpoint for demo purposes.")
def show_users_database(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "name": u.name,
            "assigned_hub": u.assigned_hub,
        }
        for u in users
    ]

