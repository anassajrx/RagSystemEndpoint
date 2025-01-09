# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import uuid
from typing import List
import spacy
from langchain.text_splitter import SpacyTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    UnstructuredPowerPointLoader,
    UnstructuredCSVLoader,
    JSONLoader,
    TextLoader
)
from langchain_community.vectorstores.pgvector import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
import google.generativeai as genai
from google.cloud import storage
from sqlalchemy import create_engine

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
DB_CONNECTION = os.getenv("DATABASE_URL")  # PostgreSQL connection string

if not all([GEMINI_API_KEY, BUCKET_NAME, DB_CONNECTION]):
    raise ValueError("Missing required environment variables")

# Initialize services
genai.configure(api_key=GEMINI_API_KEY)
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# Download spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Initialize FastAPI app
app = FastAPI(title="Enhanced RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File processing utilities
SUPPORTED_FORMATS = {
    '.pdf': PyPDFLoader,
    '.docx': Docx2txtLoader,
    '.doc': Docx2txtLoader,
    '.pptx': UnstructuredPowerPointLoader,
    '.ppt': UnstructuredPowerPointLoader,
    '.csv': UnstructuredCSVLoader,
    '.json': JSONLoader,
    '.txt': TextLoader
}

def get_file_loader(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported file format: {ext}")
    return SUPPORTED_FORMATS[ext]

def upload_to_gcs(file_path: str, destination_blob_name: str):
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    return blob.public_url

# Initialize vectorstore with PostgreSQL
def initialize_vectorstore():
    embedding_function = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    connection_string = PGVector.connection_string_from_db_params(
        driver="psycopg2",
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "vectordb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )
    
    return PGVector(
        connection_string=connection_string,
        embedding_function=embedding_function,
        collection_name="document_vectors"
    )

def process_file(file_path: str, vectorstore):
    try:
        # Get appropriate loader
        LoaderClass = get_file_loader(file_path)
        loader = LoaderClass(file_path)
        documents = loader.load()
        
        # Initialize semantic text splitter
        text_splitter = SpacyTextSplitter(
            pipeline="en_core_web_sm",
            chunk_size=1000,
            chunk_overlap=200
        )
        
        docs = text_splitter.split_documents(documents)
        vectorstore.add_documents(docs)
        return len(docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Enhanced RAG prompt generation
def generate_rag_prompt(query: str, context: str) -> str:
    escaped = context.replace("'", "").replace('"', "").replace("\n", " ")
    return f"""
    You are a helpful and informative assistant that answers questions using the provided reference context.
    Provide comprehensive answers while maintaining a conversational tone for non-technical audiences.
    Break down complex concepts into simpler terms.
    If the context doesn't contain relevant information, acknowledge that and provide a general response.
    
    QUESTION: '{query}'
    CONTEXT: '{escaped}'
    
    ANSWER:
    """

# API endpoints
@app.get("/")
async def root():
    return {"message": "Enhanced RAG API is running"}

@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    vectorstore = initialize_vectorstore()
    total_chunks = 0
    processed_files = []
    
    try:
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in SUPPORTED_FORMATS:
                continue
                
            content = await file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(content)
                
                # Upload to GCS
                gcs_path = f"documents/{uuid.uuid4()}/{file.filename}"
                gcs_url = upload_to_gcs(tmp_file.name, gcs_path)
                
                # Process for vectorstore
                num_chunks = process_file(tmp_file.name, vectorstore)
                total_chunks += num_chunks
                processed_files.append({
                    "filename": file.filename,
                    "chunks_created": num_chunks,
                    "gcs_url": gcs_url
                })
                os.unlink(tmp_file.name)
        
        return {
            "status": "success",
            "processed_files": processed_files,
            "total_chunks": total_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")

@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    try:
        vectorstore = initialize_vectorstore()
        results = vectorstore.similarity_search(question, k=6)
        context = "\n".join(doc.page_content for doc in results)
        
        prompt = generate_rag_prompt(question, context)
        model = genai.GenerativeModel(model_name='gemini-pro')
        answer = model.generate_content(prompt)
        
        return {
            "question": question,
            "answer": answer.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
