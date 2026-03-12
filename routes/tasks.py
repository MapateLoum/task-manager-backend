from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import db
from schemas.task import TaskCreate, TaskUpdate
from auth.jwt import verify_token
from bson import ObjectId
from datetime import datetime

router = APIRouter(tags=["Tasks"])
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return payload

def task_serializer(task) -> dict:
    return {
        "id": str(task["_id"]),
        "titre": task["titre"],
        "description": task.get("description", ""),
        "status": task.get("status", "todo"),
        "priority": task.get("priority", "moyenne"),
        "assigned_to": task.get("assigned_to", ""),
        "due_date": task.get("due_date", ""),
        "project_id": task["project_id"],
        "created_at": task.get("created_at", "")
    }

@router.post("/projects/{project_id}/tasks")
async def create_task(project_id: str, task: TaskCreate, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    if current_user["sub"] not in project["membres"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    new_task = {
        "titre": task.titre,
        "description": task.description,
        "status": "todo",
        "priority": task.priority,
        "assigned_to": task.assigned_to,
        "due_date": task.due_date,
        "project_id": project_id,
        "created_at": datetime.utcnow()
    }
    result = await db.tasks.insert_one(new_task)
    return {"message": "Tâche créée avec succès", "id": str(result.inserted_id)}

@router.get("/projects/{project_id}/tasks")
async def get_tasks(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    if current_user["sub"] not in project["membres"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    tasks = []
    async for task in db.tasks.find({"project_id": project_id}):
        tasks.append(task_serializer(task))
    return tasks

@router.put("/tasks/{task_id}")
async def update_task(task_id: str, task: TaskUpdate, current_user: dict = Depends(get_current_user)):
    db_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not db_task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    project = await db.projects.find_one({"_id": ObjectId(db_task["project_id"])})
    if current_user["sub"] not in project["membres"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    update_data = {k: v for k, v in task.dict().items() if v is not None}
    await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    return {"message": "Tâche modifiée avec succès"}

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(get_current_user)):
    db_task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if not db_task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    project = await db.projects.find_one({"_id": ObjectId(db_task["project_id"])})
    if current_user["sub"] not in project["membres"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    await db.tasks.delete_one({"_id": ObjectId(task_id)})
    return {"message": "Tâche supprimée avec succès"}