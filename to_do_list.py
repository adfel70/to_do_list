import asyncio
import hashlib
from enum import Enum
from fastapi import (FastAPI, HTTPException, Query)
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
import aio_pika
from aio_pika import IncomingMessage

app = FastAPI()

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client['to_do_list']
collection = db['list_1']


class Priority(Enum):
    URGENT = "urgent"
    IMPORTANT = "important"
    UNIMPORTANT = "unimportant"



class Task(BaseModel):
    # the id will be created separately
    name: Optional[str]
    priority: Optional[str] = None  # urgent, important or unimportant
    expiration_date: Optional[datetime] = None
    finished: Optional[bool] = None
    remind: Optional[bool] = None

    # Priority must be one of the allowed values
    @classmethod
    @field_validator('priority')
    def check_priority(cls, v):
        if v not in Priority.__members__.values():
            raise ValueError('Priority must be one of: urgent, important, or unimportant.')
        return v

    # Expiration date must not be in the past
    @classmethod
    @field_validator('expiration_date')
    def check_expiration_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Expiration date cannot be in the past.")
        return v

    # If remind is True, expiration_date should be set
    @classmethod
    @field_validator('remind')
    def check_remind_and_expiration(cls, v, values):
        if v and not values.get('expiration_date'):
            raise ValueError("If 'remind' is set to True, 'expiration_date' must be provided.")
        return v


async def rabbit_sender(message: str, routing_key: str):
        rabbit_connection = await aio_pika.connect_robust("amqp://localhost/")
        async with rabbit_connection:
            channel = await rabbit_connection.channel()
            await channel.default_exchange.publish(aio_pika.Message(body=message.encode()), routing_key=routing_key)


async def rabbit_receiver():
    rabbit_connection = await aio_pika.connect_robust("amqp://localhost/")
    async with rabbit_connection:
        # Create a channel
        channel = await rabbit_connection.channel()

        # Declare a queue with a name (e.g., "task_queue")
        queue = await channel.declare_queue("task_queue", durable=True)

        # Use the iterator to consume messages from the queue
        async with queue.iterator() as q_iter:
            async for message in q_iter:  # type: IncomingMessage
                try:
                    # Acknowledge message processing
                    print(f"Received message: {message.body.decode()}")
                    # You can add your message processing logic here
                except Exception as e:
                    print(f"Error processing message: {e}")
                finally:
                    # Manually acknowledge message processing completion
                    await message.ack()


loop = asyncio.get_event_loop()
loop.create_task(rabbit_receiver())

@app.post("/tasks/")
async def create_task(task: Task):
    new_task = task.model_dump()
    new_task['id'] = str(get_id(task.name))
    await collection.insert_one(new_task)
    await rabbit_sender(f"Created new task: {task.name}", "task_queue")
    return {"massage": "received task successfully"}

@app.get("/tasks/name/{task_name}", response_model = dict)
async def read_task_by_name(task_name: str):
    task = await collection.find_one({"name": task_name})
    if task is None:
        raise HTTPException(status_code = 404, detail = "Item not found")
    return task


@app.get("/tasks/priority/{task_priority}", response_model = list[dict])
async def read_tasks_by_priority(task_priority: str):
    task = await collection.find({"priority": task_priority}).to_list(length = None)
    if not task:
        raise HTTPException(status_code = 404, detail = "Item not found")
    return task


@app.get("/tasks/finished", response_model = list[dict])
async def read_finished_tasks():
    tasks_list = await collection.find({"finished": True}).to_list(length = None)
    if not tasks_list:
        raise HTTPException(status_code = 404, detail = "Item not found")
    return tasks_list


@app.get("/tasks/unfinished", response_model = list[dict])
async def read_finished_tasks():
    tasks_list = await collection.find({"finished": False}).to_list(length = None)
    if not tasks_list:
        raise HTTPException(status_code = 404, detail = "Item not found")
    return tasks_list


@app.get("/tasks/expiration_range", response_model = list[dict])
async def read_by_expiration_range(start_date: datetime = Query(..., description = "Start date in ISO format"),
                                   end_date: datetime = Query(..., description = "End date in ISO format")):
    tasks_list = await collection.find({"expiration_date": {"$gte": start_date, "$lte": end_date}}).to_list(
        length = None)
    if not tasks_list:
        raise HTTPException(status_code = 404, detail = "Item not found")
    return tasks_list


@app.post("/tasks/get_by_name", response_model = dict)
async def post_read_task_by_name(task_name: str):
    task = await collection.find_one({"name": task_name})
    if task is None:
        raise HTTPException(status_code = 404, detail = "Task not found")
    return task


@app.put("/tasks/update_by_name", response_model = str)
async def update_task(task_name: str, updated_task: Task):
    old_task = await collection.find_one({"name": task_name})
    if not old_task:
        raise HTTPException(status_code = 404, detail = "Task not found")
    task_data = {k: v for k, v in updated_task.dict().items() if v is not None}
    await collection.update_one({"name": task_name}, {"$set": task_data})
    return f"update succeed"


@app.put("/tasks/update_by_priority", response_model = str)
async def update_tasks_by_priority(task_priority: str, updated_task: Task):
    task_data = {k: v for k, v in updated_task.dict().items() if v is not None}
    if not task_data:
        raise HTTPException(status_code = 400, detail = "No update data provided")
    result = await collection.update_many({"priority": task_priority}, {"$set": task_data})
    if result.matched_count == 0:
        raise HTTPException(status_code = 404, detail = "No tasks with the given priority found")
    return f"Updated {result.modified_count} task(s) with priority {task_priority}"


@app.delete("/tasks/{task_name}", response_model = str)
async def delete_task_by_name(task_name: str):
    result = await collection.delete_one({"name": task_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code = 404, detail = "Item not found")
    return f"Item deleted successfully"

def get_id(x):
    return hashlib.md5(x.encode('utf-8')).hexdigest()

if __name__ == "__main__":
    uvicorn.run(app, host = "127.0.0.1", port = 8000)
