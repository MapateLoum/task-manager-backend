from pydantic import BaseModel, field_validator
from typing import Optional

class ProjectCreate(BaseModel):
    titre: str
    description: Optional[str] = None

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

class ProjectUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None

    @field_validator("titre")
    def titre_valide(cls, v):
        if v and len(v.strip()) < 3:
            raise ValueError("Le titre doit avoir au moins 3 caractères")
        if v and len(v) > 100:
            raise ValueError("Le titre ne peut pas dépasser 100 caractères")
        return v.strip() if v else v

    @field_validator("description")
    def description_valide(cls, v):
        if v and len(v) > 500:
            raise ValueError("La description ne peut pas dépasser 500 caractères")
        return v