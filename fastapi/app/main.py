
from fastapi import FastAPI
from typing import Union

from .routers import pdf

app = FastAPI()
app.include_router(pdf.router)

@app.get("/")
def read_root():
    return {"Hello": "World test"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


