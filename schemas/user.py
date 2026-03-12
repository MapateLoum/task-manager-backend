from pydantic import BaseModel, EmailStr, field_validator
import re

class UserRegister(BaseModel):
    nom: str
    email: EmailStr
    password: str

    @field_validator("nom")
    def nom_valide(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Le nom doit avoir au moins 2 caractères")
        if len(v) > 50:
            raise ValueError("Le nom ne peut pas dépasser 50 caractères")
        return v.strip()

    @field_validator("password")
    def password_valide(cls, v):
        if len(v) < 8:
            raise ValueError("Le mot de passe doit avoir au moins 8 caractères")
        if len(v) > 100:
            raise ValueError("Le mot de passe est trop long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r"[0-9]", v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Le mot de passe doit contenir au moins un caractère spécial")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    nom: str
    email: str