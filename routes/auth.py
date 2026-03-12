from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import db
from schemas.user import UserRegister, UserLogin
from auth.hash import hash_password, verify_password
from auth.jwt import create_access_token, verify_token
from bson import ObjectId
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from pydantic import BaseModel, field_validator
from typing import Optional

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer()

# ── Schemas locaux ─────────────────────────────────────────────────────────────

class UpdateProfile(BaseModel):
    nom: str

    @field_validator("nom")
    def nom_valide(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Le nom doit avoir au moins 2 caractères")
        if len(v) > 50:
            raise ValueError("Le nom ne peut pas dépasser 50 caractères")
        return v.strip()

class UpdatePassword(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    def password_valide(cls, v):
        if len(v) < 8:
            raise ValueError("Minimum 8 caractères")
        if not any(c.isupper() for c in v):
            raise ValueError("Au moins une majuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Au moins un chiffre")
        if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in v):
            raise ValueError("Au moins un caractère spécial")
        return v

# ── Helper ─────────────────────────────────────────────────────────────────────

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return payload

# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/register")
async def register(user: UserRegister):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    new_user = {
        "nom": user.nom,
        "email": user.email,
        "password": hash_password(user.password)
    }
    result = await db.users.insert_one(new_user)
    return {"message": "Compte créé avec succès", "id": str(result.inserted_id)}

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    token = create_access_token({"sub": str(db_user["_id"]), "email": db_user["email"]})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"_id": ObjectId(current_user["sub"])})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {
        "id": str(user["_id"]),
        "nom": user["nom"],
        "email": user["email"]
    }

@router.put("/me")
async def update_profile(data: UpdateProfile, current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"_id": ObjectId(current_user["sub"])})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    await db.users.update_one(
        {"_id": ObjectId(current_user["sub"])},
        {"$set": {"nom": data.nom}}
    )
    return {
        "id": str(user["_id"]),
        "nom": data.nom,
        "email": user["email"]
    }

@router.put("/me/password")
async def update_password(data: UpdatePassword, current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"_id": ObjectId(current_user["sub"])})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    if not verify_password(data.current_password, user["password"]):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    await db.users.update_one(
        {"_id": ObjectId(current_user["sub"])},
        {"$set": {"password": hash_password(data.new_password)}}
    )
    return {"message": "Mot de passe mis à jour avec succès"}