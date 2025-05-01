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
import itertools

app = FastAPI(title="JSON to CSV Converter")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Create uploads directory if it doesn't exist
uploads_dir = Path("uploads")
if not uploads_dir.exists():
    uploads_dir.mkdir()


def flatten_nested_json(data, prefix=""):
    """
    Recursively flatten nested JSON structures.
    Returns a list of flattened dictionaries.
    """
    flattened_items = []

    if isinstance(data, dict):
        # Process dictionary
        dict_items = []
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key

            if isinstance(value, (dict, list)):
                # Recursively flatten nested structures
                nested_items = flatten_nested_json(value, new_prefix)
                dict_items.append(nested_items)
            else:
                # Add simple value
                dict_items.append([{new_prefix: value}])

        # Combine all combinations of flattened items
        for items in itertools.product(*dict_items):
            combined = {}
            for item in items:
                if isinstance(item, list):
                    for i in item:
                        combined.update(i)
                else:
                    combined.update(item)
            flattened_items.append(combined)

    elif isinstance(data, list):
        # Process list
        if not data:
            return [{f"{prefix}": []}]

        # Handle list of primitive values
        if all(not isinstance(item, (dict, list)) for item in data):
            return [{f"{prefix}": data}]

        # Process list of complex items
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                # Recursively flatten nested structures with index
                nested_items = flatten_nested_json(item, f"{prefix}")
                flattened_items.extend(nested_items)
            else:
                flattened_items.append({f"{prefix}[{i}]": item})

    else:
        # Handle primitive values
        return [{prefix: data}]

    return flattened_items


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

            # Use json_normalize with record_path for deeply nested structures
            try:
                # For deeply nested structures, try custom flattening
                if any(
                    isinstance(item, dict)
                    and any(isinstance(v, (dict, list)) for v in item.values())
                    for item in json_data
                ):
                    # Custom recursive flattening for complex nested structures
                    flattened_data = []
                    for item in json_data:
                        flat_items = flatten_nested_json(item)
                        flattened_data.extend(flat_items)

                    # Create DataFrame from flattened data
                    if flattened_data:
                        df = pd.DataFrame(flattened_data)
                    else:
                        df = pd.json_normalize(json_data)
                else:
                    # Simple array of objects, use standard approach
                    df = pd.DataFrame(json_data)
            except Exception as e:
                # Fallback to standard json_normalize if custom flattening fails
                df = pd.json_normalize(json_data)

        elif isinstance(json_data, dict):
            # Handle nested JSON by flattening it
            try:
                # For deeply nested dictionaries, try custom flattening
                if any(isinstance(v, (dict, list)) for v in json_data.values()):
                    flattened_data = flatten_nested_json(json_data)
                    if flattened_data:
                        df = pd.DataFrame(flattened_data)
                    else:
                        df = pd.json_normalize(json_data)
                else:
                    # Simple dictionary, use standard approach
                    df = pd.DataFrame([json_data])
            except Exception as e:
                # Fallback to standard json_normalize if custom flattening fails
                df = pd.json_normalize(json_data)
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
