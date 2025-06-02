from fastapi import FastAPI


api = FastAPI(title="CollagrCms", version="0.1.0")


@api.get("/")
def root():
    return {"message": "Hello, FastAPI!"}
