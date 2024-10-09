import hashlib

from bson import ObjectId
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from pydantic import BaseModel
from datetime import date
from typing import Optional

app = FastAPI()

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client['to_do_list']
collection = db['list_1']


class Task(BaseModel):
    # the id will be created separately
    name: str
    priority: Optional[str] = None  # urgent, important or unimportant
    expiration_date: Optional[date] = None
    finished: Optional[bool] = None
    remind: Optional[bool] = None


def bson_to_dict(task):
    task["_id"] = int(task["_id"])
    return task


def get_id(x):
    return hashlib.md5(x.encode('utf-8'))


@app.post("/tasks/", response_model=str)
async def create_task(task: Task):
    new_task = {
        "_id": get_id(task.name),
        "name": task.name,
        "priority": task.priority,
        "expiration_date": task.expiration_date,
        "remind": task.remind,
        "finished": task.finished
    }
    db.collection.insert_one(new_task)
    return f"received task successfully"


@app.get("/tasks/{task_name}", response_model=dict)
async def read_task(task_name: str):
    task = await collection.find_one({"name": ObjectId(task_name)})
    if task is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return bson_to_dict(task)

    # @app.get("/tasks/", response_model=dict)
    # async def create_task(task: Task):
    #
    # @app.get("/tasks/", response_model=dict)
    # async def create_task(task: Task):
    #
    # @app.get("/tasks/", response_model=dict)
    # async def create_task(task: Task):
    #
    # @app.get("/tasks/", response_model=dict)
    # async def create_task(task: Task):


@app.put("/tasks/{task_name}", response_model=str)
async def update_task(task_name: str, updated_task: Task):
    old_task = collection.find_one({"name": task_name})
    if not old_task:
        raise HTTPException(status_code=404, detail="Task not found")
    new_task = old_task.copy()
    task_data = {k: v for k, v in updated_task.dist().items() if v is not None}
    new_task.update(task_data)
    collection.update_one({"name": task_name}, {"$set": new_task})
    return f"update succeed"


@app.delete("/tasks/{task_id}", response_model=dict)
async def delete_task_by_id(task_id: int):
    result = await collection.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

#
# @app.delete("/tasks/{task_name}", response_model=dict)
# async def delete_task_by_name(task_name: str):
#     result = await collection.delete_one({"_id": ObjectId(task_name)})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return {"message": "Item deleted successfully"}

    # @app.delete("/tasks/", response_model=dict)
    # async def create_task(task: Task):
    #
    # @app.delete("/tasks/", response_model=dict)
    # async def create_task(task: Task):


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)