from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
from file_handler import save_uploaded_file, cleanup_file
from pdf_service import extract_text_from_pdf
from chunk_service import chunk_text

app = FastAPI(title="Document Processing API")

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_path = None
    try:
        # 1. Save the file
        file_path = save_uploaded_file(file)
        
        # 2. Extract text
        raw_text = extract_text_from_pdf(file_path)
        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        
        # 3. Chunk the text
        chunks = chunk_text(raw_text)
        
        return {
            "filename": file.filename,
            "total_chunks": len(chunks),
            "chunks": chunks
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        if file_path:
            cleanup_file(file_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)