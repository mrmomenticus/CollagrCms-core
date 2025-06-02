from fastapi import FastAPI


api = FastAPI(title="CollagrCms", version="0.1.0")


@api.post("/hi", status_code=200)
def test():
    return {"message": "Hello, FastAPI!"}
