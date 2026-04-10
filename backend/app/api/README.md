# API Routes Template

Folder ini untuk mendefinisikan API routes (endpoints).

## Struktur

```
api/
├── v1/                           # API version 1
│   ├── __init__.py
│   ├── users.py                  # GET/POST/PUT/DELETE users
│   ├── cameras.py                # GET/POST/PUT/DELETE cameras
│   ├── violations.py             # GET violations, update status
│   ├── stats.py                  # GET detection stats
│   ├── notifications.py          # GET/PUT notifications
│   └── dependencies.py           # Common dependencies (auth, db)
```

## Quick Example - users.py

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core import get_db
from app.schemas import UserResponse, UserCreate
from app.models import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

## Setup di main.py

```python
from app.api.v1 import users, cameras, violations

app = FastAPI()

# Include routers
app.include_router(users.router)
app.include_router(cameras.router)
app.include_router(violations.router)
```

## API Endpoints to Create

### Users
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user
- `POST /api/v1/users` - Create user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Cameras
- `GET /api/v1/cameras` - List cameras
- `GET /api/v1/cameras/{id}` - Get camera
- `POST /api/v1/cameras` - Create camera
- `PUT /api/v1/cameras/{id}` - Update camera
- `DELETE /api/v1/cameras/{id}` - Delete camera

### Violations
- `GET /api/v1/violations` - List violations
- `GET /api/v1/violations/{id}` - Get violation
- `PUT /api/v1/violations/{id}/status` - Update violation status

### Stats
- `GET /api/v1/stats/cameras/{id}` - Get camera stats
- `GET /api/v1/stats/summary` - Get summary stats

### Notifications
- `GET /api/v1/notifications` - List notifications
- `PUT /api/v1/notifications/{id}/read` - Mark as read

## Documentation

- FastAPI docs: http://localhost:8000/docs
- Swagger: http://localhost:8000/swagger
- ReDoc: http://localhost:8000/redoc
