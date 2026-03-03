from fastapi import FastAPI

application = FastAPI()

@application.get("/test")
def read_root():
    return {"Hello": "World"}