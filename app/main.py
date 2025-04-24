from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import pandas as pd
import io
import os
from pathlib import Path
import uuid

app = FastAPI(title="JSON to CSV Converter")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Create uploads directory if it doesn't exist
uploads_dir = Path("uploads")
if not uploads_dir.exists():
    uploads_dir.mkdir()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/convert")
async def convert_json(
    request: Request, json_file: UploadFile = File(None), json_text: str = Form(None)
):
    try:
        # Generate unique ID for this conversion
        conversion_id = str(uuid.uuid4())

        # Process JSON data from either file or text input
        if json_file and json_file.filename:  # Check if file was actually uploaded
            contents = await json_file.read()
            content_str = contents.decode("utf-8").strip()
            if not content_str:
                return templates.TemplateResponse(
                    "index.html",
                    {"request": request, "error": "The uploaded file is empty"},
                )
            try:
                json_data = json.loads(content_str)
            except json.JSONDecodeError as e:
                line_col = f"line {e.lineno}, column {e.colno}"
                return templates.TemplateResponse(
                    "index.html",
                    {
                        "request": request,
                        "error": f"Invalid JSON format in uploaded file: {str(e)} at {line_col}. Please check your JSON syntax.",
                    },
                )
        elif json_text:
            if not json_text.strip():
                return templates.TemplateResponse(
                    "index.html",
                    {
                        "request": request,
                        "error": "Please enter JSON text - the input is empty",
                    },
                )
            try:
                json_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                line_col = f"line {e.lineno}, column {e.colno}"
                return templates.TemplateResponse(
                    "index.html",
                    {
                        "request": request,
                        "error": f"Invalid JSON format: {str(e)} at {line_col}. Please check your JSON syntax.",
                    },
                )
        else:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "error": "Please provide either a JSON file or JSON text",
                },
            )

        # Convert to DataFrame
        if isinstance(json_data, list):
            if not json_data:  # Empty list
                return templates.TemplateResponse(
                    "index.html",
                    {"request": request, "error": "The JSON array is empty"},
                )
            df = pd.DataFrame(json_data)
        elif isinstance(json_data, dict):
            # Handle nested JSON by flattening it
            if any(isinstance(v, (dict, list)) for v in json_data.values()):
                df = pd.json_normalize(json_data)
            else:
                df = pd.DataFrame([json_data])
        else:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "error": f"Invalid JSON format: Expected an object or array, got {type(json_data).__name__}",
                },
            )

        # Check if dataframe is empty
        if df.empty:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "error": "No data could be extracted from the JSON",
                },
            )

        # Save as CSV
        csv_path = f"uploads/{conversion_id}.csv"
        df.to_csv(csv_path, index=False)

        # Prepare data for HTML table
        headers = df.columns.tolist()
        rows = df.values.tolist()

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "headers": headers,
                "rows": rows,
                "filename": csv_path,
                "conversion_id": conversion_id,
            },
        )
    except Exception as e:
        error_msg = str(e)
        if "Expecting value" in error_msg and "line 1 column 1" in error_msg:
            error_msg = "The provided JSON is empty or has invalid format. Make sure your JSON starts with { or ["

        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": f"Error processing JSON: {error_msg}"},
        )


@app.get("/download/{conversion_id}")
async def download_csv(conversion_id: str):
    csv_path = f"uploads/{conversion_id}.csv"
    if os.path.exists(csv_path):
        return FileResponse(
            path=csv_path,
            filename=f"converted_{conversion_id}.csv",
            media_type="text/csv",
        )
    return {"error": "File not found"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=3033, reload=True)
