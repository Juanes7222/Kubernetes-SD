from fastapi import APIRouter, Depends
from typing import List
from core.authentication import verify_token
from models.schemas import TaskList
from services.lists import ListServices

router = APIRouter(prefix="/lists",
                   tags=["Listas"])

@router.post("/")
def create_list(name: str, uid: str = Depends(verify_token)):
    return ListServices.create_list(name, uid)

@router.get("/", response_model=List[TaskList])
def get_lists(uid: str = Depends(verify_token)):
    return ListServices.get_lists(uid)