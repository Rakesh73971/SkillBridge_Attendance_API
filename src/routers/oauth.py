from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2
from ..database import get_db
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    if user.institution_id is not None:
        institution = db.query(models.Institution).filter(models.Institution.id == user.institution_id).first()
        if not institution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    hashed_password = utils.hash_password(user.password)

    new_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        institution_id=user.institution_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    
    access_token = oauth2.create_access_token(
        data={"user_id": new_user.id, "role": new_user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    
    
    if not user or not utils.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
   
    access_token = oauth2.create_access_token(
        data={"user_id": user.id, "role": user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/monitoring-token", response_model=schemas.Token)
def get_monitoring_token(
    request: schemas.MonitoringTokenRequest, 
    current_user: models.User = Depends(oauth2.RoleChecker([models.RoleEnum.MONITORING_OFFICER]))
):
    if request.key != settings.monitoring_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    
    # Create scoped monitoring token with 1-hour expiry
    monitoring_token = oauth2.create_scoped_monitoring_token(
        data={"user_id": current_user.id, "role": current_user.role.value}
    )
    return {"access_token": monitoring_token, "token_type": "bearer"}
