from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from io import StringIO
import sys

from weaviate_k8_test_simple import main as original_main

app = FastAPI()

# Mount static files and template directory
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    try:
        original_main()
        output = mystdout.getvalue()
    finally:
        sys.stdout = old_stdout
    return templates.TemplateResponse("index.html", {"request": request, "output": output})