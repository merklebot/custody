import uvicorn
from fastapi import FastAPI

web_app = FastAPI()


@web_app.get("/")
async def hello():
    return {"hello": "world"}


if __name__ == "__main__":
    uvicorn.run(web_app, host="0.0.0.0", port=8080)
