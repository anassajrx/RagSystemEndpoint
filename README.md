# Multi-Format RAG (Retrieval-Augmented Generation) API

## Overview
This repository contains a scalable Retrieval-Augmented Generation (RAG) API built with FastAPI and deployed on Google Cloud Run. The application supports multiple document formats, uses ChromaDB for vector storage, and leverages Google's Gemini Pro model for generating responses.

### Key Features
- 📄 Multi-format document support (PDF, DOCX, PPT, CSV, JSON, TXT)
- 🔍 Semantic text chunking for improved context understanding
- ☁️ Cloud-native architecture using Google Cloud services
- 🔄 Persistent vector storage with ChromaDB
- 🚀 Scalable deployment on Cloud Run
- 🤖 Powered by Google's Gemini Pro model

## Architecture
```
                                     ┌─────────────────┐
                                     │   Cloud Run     │
                                     │    RAG API      │
                                     └────────┬────────┘
                                              │
                         ┌────────────────────┼────────────────────┐
                         │                    │                    │
                   ┌─────┴─────┐        ┌─────┴─────┐       ┌─────┴─────┐
                   │  Cloud     │        │  ChromaDB  │       │  Gemini   │
                   │  Storage   │        │   Vector   │       │    Pro    │
                   │            │        │   Store    │       │           │
                   └───────────┘        └───────────┘       └───────────┘
```

## Prerequisites
- Python 3.9+
- Google Cloud account with billing enabled
- Google Cloud CLI installed
- Gemini API access

# Comparison of Diabot Versions and AxiomAI

| **Feature**            | **Diabot Version 1**                                      | **Diabot RAG Version 1**                            | **Diabot RAG Version 2**                                          | **AxiomAI**                                                        |
|-------------------------|----------------------------------------------------------|----------------------------------------------------|-------------------------------------------------------------------|-------------------------------------------------------------------|
| **Purpose**             | Prototype chatbot based on Groq API.                     | Simple standalone RAG system.                     | Fully integrated RAG system with enhancements.                    | Multi-domain chatbot framework with advanced configuration.        |
| **Technology**          | Groq API only, no RAG.                                   | Streamlit, basic chunking, no persistence.        | Advanced RAG with Groq fallback and Firebase integration.         | Integrated RAG system, multi-source support.                      |
| **Authentication**      | ❌ No authentication.                                    | ❌ No authentication.                              | ✅ Authentication with Firebase.                                  | ✅ Authentication and profile management.                         |
| **Data Storage**        | ❌ Local storage only, no persistence.                   | ❌ No persistence.                                 | ✅ Data stored in Firebase and synchronized.                      | ✅ Cloud storage with real-time syncing.                          |
| **RAG System**          | ❌ No RAG system.                                        | ✅ Basic RAG with document chunking.              | ✅ Advanced RAG with Groq fallback.                               | ✅ RAG system with multi-domain support.                          |
| **Response Customization** | ❌ No customization.                                  | ❌ No customization.                               | ✅ Customized responses based on profiles.                        | ✅ Full customization per domain.                                 |
| **User Profiles**       | ❌ No profile management.                                | ❌ No profile management.                          | ✅ User profiles with synchronization.                            | ✅ User profiles with multi-domain support.                       |
| **Audio Transcription** | ❌ Not available.                                        | ❌ Not available.                                  | ✅ Audio transcription available.                                 | ✅ Audio transcription available.                                 |
| **Data Synchronization**| ❌ No synchronization.                                   | ❌ No synchronization.                             | ✅ Real-time data synchronization via Firebase.                   | ✅ Cloud synchronization across platforms.                        |
| **Deployment**          | Vercel deployment, local processing.                    | Local deployment (localhost).                     | Cloud-based with Firebase deployment.                             | Fully cloud-based with multi-domain support.                      |
| **Admin Features**      | ❌ No admin features.                                    | ❌ No admin features.                              | ✅ Admin dashboard for configuration and user management.         | ✅ Advanced admin dashboard for multi-domain configurations.      |
| **Backup & Data Retrieval** | ❌ No backup or retrieval.                           | ❌ No backup.                                      | ✅ Data backup and retrieval via Firebase.                        | ✅ Full backup and data retrieval options.                        |

## Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/multi-format-rag.git
cd multi-format-rag
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. **Set up environment variables**
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
GCS_BUCKET_NAME=your_bucket_name
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

5. **Run the application locally**
```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` to access the Swagger documentation.

## Project Structure
```
├── app/
│   ├── main.py           # Main FastAPI application
│   └── __init__.py
├── requirements.txt      # Project dependencies
├── Dockerfile           # Container configuration
├── .dockerignore        # Docker ignore file
└── README.md           # Project documentation
```

## API Endpoints

### `GET /`
Health check endpoint.

### `POST /upload/`
Upload documents for processing.
- Supports multiple files
- Returns processing status and file metadata

### `GET /files/`
List all processed files and their metadata.

### `POST /ask/`
Ask questions about the uploaded documents.
- Requires a question in the request body
- Returns AI-generated answers based on document context

## Deployment to Google Cloud Run

### 1. Initial Setup

```bash
# Install Google Cloud SDK if you haven't already
# https://cloud.google.com/sdk/docs/install

# Initialize Google Cloud CLI
gcloud init

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable firestore.googleapis.com
```

### 2. Set Up Cloud Storage

```bash
# Create a bucket for document storage
gsutil mb gs://your-rag-documents-bucket

# Create a service account
gcloud iam service-accounts create rag-service-account \
    --description="RAG application service account" \
    --display-name="RAG Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:rag-service-account@your-project-id.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

### 3. Set Up Secrets

```bash
# Create secret for Gemini API key
echo -n "your-gemini-api-key" | \
gcloud secrets create GEMINI_API_KEY --data-file=-

# Grant service account access to secrets
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
    --member="serviceAccount:rag-service-account@your-project-id.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 4. Deploy to Cloud Run

```bash
# Build the container
gcloud builds submit --tag gcr.io/your-project-id/rag-app

# Deploy to Cloud Run
gcloud run deploy rag-app \
    --image gcr.io/your-project-id/rag-app \
    --platform managed \
    --region your-region \
    --memory 2Gi \
    --cpu 2 \
    --service-account rag-service-account@your-project-id.iam.gserviceaccount.com \
    --set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest \
    --set-env-vars=GCS_BUCKET_NAME=your-rag-documents-bucket,CHROMA_PERSIST_DIR=/tmp/chroma_db
```

## Usage Examples

### Upload Documents
```python
import requests

url = "https://your-app-url/upload/"
files = [
    ('files', ('document1.pdf', open('document1.pdf', 'rb'))),
    ('files', ('document2.docx', open('document2.docx', 'rb')))
]
response = requests.post(url, files=files)
print(response.json())
```

### Ask Questions
```python
import requests

url = "https://your-app-url/ask/"
data = {"question": "What are the main points discussed in the documents?"}
response = requests.post(url, data=data)
print(response.json())
```

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



## Acknowledgments
- FastAPI for the modern web framework
- Langchain for document processing
- Google Cloud for infrastructure
- Gemini Pro for AI capabilities
- ChromaDB for vector storage

## Support
For support, please open an issue in the GitHub repository or contact the maintainers.
