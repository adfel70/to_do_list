from bson import ObjectId
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from pydantic import BaseModel
from datetime import date

app = FastAPI()

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client['to_do_list']
collection = db['list_1']


class Task(BaseModel):
    # the id will be created separately
    priority: str  # urgent, important or unimportant
    description: str
    expiration_date: date
    status: int     # -1 for no difference, 0 for doing it, 1 for completed. TODO - make a boolean for finished?
    remind: bool

def bson_to_dict(task):
    task["_id"] = int(task["_id"])
    return task


@app.post("/tasks/", response_model=dict)
async def create_task(task: Task):

#TODO !!!!
@app.put("", response_model=dict)
async def update_expiration_date(task: Task):

@app.put("", response_model=dict)
async def update_status(task: Task):

@app.put("", response_model=dict)
async def update_priority(task: Task):

@app.put("", response_model=dict)
async def update_remind(task: Task):



@app.get("/tasks/{task_id}", response_model=dict)
async def read_task(task_id: int):
        task = await collection.find_one({"_id": ObjectId(task_id)})
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

@app.delete("/tasks/{task_id}", response_model=dict)
async def delete_task_by_id(task_id: int):
    result = await collection.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

@app.delete("/tasks/{task_description}", response_model=dict)
async def delete_task_by_description(task_description : str):
    result = await collection.delete_one({"_id": ObjectId(task_description)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}

            # @app.delete("/tasks/", response_model=dict)
            # async def create_task(task: Task):
            #
            # @app.delete("/tasks/", response_model=dict)
            # async def create_task(task: Task):



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
