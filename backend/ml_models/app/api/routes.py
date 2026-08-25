"""
HTTP surface of the backend. Matches the frontend flow discussed in the
proposal: upload/select image(s) -> ask a question -> get results.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.agent.orchestrator import run_query
from app.config import settings
from app.schemas.requests import ImageModality, QueryRequest, QueryResponse, UploadResponse
from app.utils.geo_io import guess_modality, load_image
from app.utils.validation import IncompatibleInputError, infer_input_scope, validate_pair_compatibility

router = APIRouter()

# In-memory map of image_id -> file path. Swap for a real DB/object store
# (S3, GCS, or even just a SQLite table) once this leaves prototype stage.
_image_store: dict[str, str] = {}


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile):
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".tif", ".tiff", ".png", ".jpg", ".jpeg"):
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    image_id = str(uuid.uuid4())
    dest_path = upload_dir / f"{image_id}{suffix}"

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.MAX_UPLOAD_MB}MB limit")

    dest_path.write_bytes(contents)
    _image_store[image_id] = str(dest_path)

    loaded = load_image(str(dest_path))
    modality = guess_modality(loaded)

    return UploadResponse(
        image_id=image_id,
        filename=file.filename,
        modality=modality,
        width=loaded.width,
        height=loaded.height,
        has_geo_metadata=loaded.has_geo_metadata,
    )


@router.post("/query", response_model=QueryResponse)
def submit_query(request: QueryRequest):
    if not (1 <= len(request.image_ids) <= 2):
        raise HTTPException(400, "Provide 1 image for single-image tasks, or 2 for pairs.")

    paths = []
    for image_id in request.image_ids:
        if image_id not in _image_store:
            raise HTTPException(404, f"Unknown image_id: {image_id}. Upload it first via /upload.")
        paths.append(_image_store[image_id])

    images = [load_image(p) for p in paths]
    modalities = [guess_modality(img) for img in images]

    try:
        input_scope = request.input_scope or infer_input_scope(images, modalities)
        validate_pair_compatibility(images)
    except IncompatibleInputError as e:
        raise HTTPException(422, str(e))

    return run_query(query_text=request.query_text, images=images, input_scope=input_scope)

