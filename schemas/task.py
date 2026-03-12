from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum
from datetime import datetime

class StatusEnum(str, Enum):
    todo = "todo"
    en_cours = "en_cours"
    termine = "termine"

class PriorityEnum(str, Enum):
    basse = "basse"
    moyenne = "moyenne"
    haute = "haute"

class TaskCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: PriorityEnum = PriorityEnum.moyenne
    due_date: Optional[str] = None

    @field_validator("titre")
    def titre_valide(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Le titre doit avoir au moins 3 caractères")
        if len(v) > 100:
            raise ValueError("Le titre ne peut pas dépasser 100 caractères")
        return v.strip()

    @field_validator("description")
    def description_valide(cls, v):
        if v and len(v) > 500:
            raise ValueError("La description ne peut pas dépasser 500 caractères")
        return v

    @field_validator("due_date")
    def due_date_valide(cls, v):
        if v:
            try:
                date = datetime.strptime(v, "%Y-%m-%d")
                if date < datetime.utcnow():
                    raise ValueError("La date limite ne peut pas être dans le passé")
            except ValueError as e:
                raise ValueError(f"Format de date invalide, utilisez YYYY-MM-DD : {e}")
        return v

class TaskUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None

    @field_validator("titre")
    def titre_valide(cls, v):
        if v and len(v.strip()) < 3:
            raise ValueError("Le titre doit avoir au moins 3 caractères")
        if v and len(v) > 100:
            raise ValueError("Le titre ne peut pas dépasser 100 caractères")
        return v.strip() if v else v

    @field_validator("due_date")
    def due_date_valide(cls, v):
        if v:
            try:
                date = datetime.strptime(v, "%Y-%m-%d")
                if date < datetime.utcnow():
                    raise ValueError("La date limite ne peut pas être dans le passé")
            except ValueError as e:
                raise ValueError(f"Format de date invalide : {e}")
        return v