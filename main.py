from fastapi import FastAPI
from utils import split_string, format_date, count_numeric_in_guid

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/split_string/{input_string}")
def split_string_endpoint(input_string: str):
    return {"result": split_string(input_string)}

@app.get("/format_date/{input_date}")
def format_date_endpoint(input_date: str):
    return {"result": format_date(input_date)}

@app.get("/count_numeric_in_guid/{guid}")
def count_numeric_in_guid_endpoint(guid: str):
    return {"result": count_numeric_in_guid(guid)}
