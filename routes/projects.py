from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import db
from schemas.project import ProjectCreate, ProjectUpdate
from auth.jwt import verify_token
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["Projects"])
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return payload

def project_serializer(project) -> dict:
    return {
        "id": str(project["_id"]),
        "titre": project["titre"],
        "description": project.get("description", ""),
        "owner_id": project["owner_id"],
        "membres": project.get("membres", []),
        "created_at": project.get("created_at", "")
    }

@router.post("/")
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    new_project = {
        "titre": project.titre,
        "description": project.description,
        "owner_id": current_user["sub"],
        "membres": [current_user["sub"]],
        "created_at": datetime.utcnow()
    }
    result = await db.projects.insert_one(new_project)
    return {"message": "Projet créé avec succès", "id": str(result.inserted_id)}

@router.get("/")
async def get_projects(current_user: dict = Depends(get_current_user)):
    projects = []
    async for project in db.projects.find({"membres": current_user["sub"]}):
        projects.append(project_serializer(project))
    return projects

@router.get("/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    if current_user["sub"] not in project["membres"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    return project_serializer(project)

@router.put("/{project_id}")
async def update_project(project_id: str, project: ProjectUpdate, current_user: dict = Depends(get_current_user)):
    db_project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not db_project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    if db_project["owner_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Seul le owner peut modifier")
    update_data = {k: v for k, v in project.dict().items() if v is not None}
    await db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": update_data})
    return {"message": "Projet modifié avec succès"}

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    db_project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not db_project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    if db_project["owner_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Seul le owner peut supprimer")
    await db.projects.delete_one({"_id": ObjectId(project_id)})
    return {"message": "Projet supprimé avec succès"}

@router.post("/{project_id}/invite")
async def invite_member(project_id: str, email: dict, current_user: dict = Depends(get_current_user)):
    db_project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not db_project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    if db_project["owner_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Seul le owner peut inviter")
    user = await db.users.find_one({"email": email["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    user_id = str(user["_id"])
    if user_id in db_project["membres"]:
        raise HTTPException(status_code=400, detail="Déjà membre du projet")
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$push": {"membres": user_id}}
    )
    return {"message": "Membre ajouté avec succès"}