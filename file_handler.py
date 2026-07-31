import os
import shutil
from fastapi import UploadFile

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(upload_file: UploadFile) -> str:
    file_path = os.path.join(UPLOAD_DIR, upload_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path

def cleanup_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)