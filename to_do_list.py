import hashlib
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

app = FastAPI()

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client['to_do_list']
collection = db['list_1']


class Task(BaseModel):
    # the id will be created separately
    name: str
    priority: Optional[str] = None  # urgent, important or unimportant
    expiration_date: Optional[datetime] = None
    finished: Optional[bool] = None
    remind: Optional[bool] = None


def get_id(x):
    return hashlib.md5(x.encode('utf-8'))


@app.post("/tasks/")
async def create_task(task: Task):
    new_task = {
        "_id": str(get_id(task.name)),
        "name": task.name,
        "priority": task.priority,
        "expiration_date": task.expiration_date,
        "remind": task.remind,
        "finished": task.finished
    }
    await collection.insert_one(new_task)
    return {"massage": "received task successfully"}


@app.get("/tasks/name/{task_name}", response_model=dict)
async def read_task_by_name(task_name: str):
    task = await collection.find_one({"name": task_name})
    if task is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return task


@app.get("/tasks/priority/{task_priority}", response_model=list[dict])
async def read_tasks_by_priority(task_priority: str):
    task = await collection.find({"priority": task_priority}).to_list(length=None)
    if not task:
        raise HTTPException(status_code=404, detail="Item not found")
    return task


@app.get("/tasks/finished", response_model=list[dict])
async def read_finished_tasks():
    tasks_list = await collection.find({"finished": True}).to_list(length=None)
    if not tasks_list:
        raise HTTPException(status_code=404, detail="Item not found")
    return tasks_list


@app.put("/tasks/{task_name}", response_model=str)
async def update_task(task_name: str, updated_task: Task):
    old_task = await collection.find_one({"name": task_name})
    if not old_task:
        raise HTTPException(status_code=404, detail="Task not found")
    new_task = old_task.copy()
    task_data = {k: v for k, v in updated_task.dict().items() if v is not None}
    new_task.update(task_data)
    await collection.update_one({"name": task_name}, {"$set": new_task})
    return f"update succeed"


@app.delete("/tasks/{task_name}", response_model=str)
async def delete_task_by_name(task_name: str):
    result = await collection.delete_one({"name": task_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return f"Item deleted successfully"


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
