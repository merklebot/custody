from fastapi import APIRouter, Depends, HTTPException, status
from custody.web.schemas.user import NewUser
from custody.web import dependencies

from sqlalchemy.orm import Session

from custody.db.models.user import User

router = APIRouter()


@router.post('/new')
async def add_new_user(new_user: NewUser, db: Session = Depends(dependencies.get_db)):
    user = User(
        email=new_user.email,
        name=new_user.name,
        api_key=new_user.api_key,
        content=[]
    )
    db.add(user)
    db.commit()
    return {
        'name': user.name,
        'email': user.email
    }


@router.get('/me')
async def get_current_user(user: User = Depends(dependencies.get_current_user)):
    return {
        'name': user.name,
        'email': user.email
    }
