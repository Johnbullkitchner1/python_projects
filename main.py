import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import ast

# -----------------------------------------------------------
# FIREBASE INITIALIZATION
# -----------------------------------------------------------
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# -----------------------------------------------------------
# FASTAPI APP
# -----------------------------------------------------------
app = FastAPI()

@app.get("/")
def home():
    return {"message": "BugTracker Analyzer API running successfully!"}

# -----------------------------------------------------------
# DATA MODELS
# -----------------------------------------------------------
class Project(BaseModel):
    name: str
    owner: str

class CodeFile(BaseModel):
    project_id: str
    filename: str
    content: str


# -----------------------------------------------------------
# CREATE PROJECT ENDPOINT
# -----------------------------------------------------------
@app.post("/projects/create")
def create_project(project: Project):
    doc_ref = db.collection("projects").document()
    doc_ref.set({
        "name": project.name,
        "owner": project.owner,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })
    return {"status": "success", "project_id": doc_ref.id}


# -----------------------------------------------------------
# UPLOAD CODE FILE ENDPOINT
# -----------------------------------------------------------
@app.post("/projects/upload-file")
def upload_file(data: CodeFile):
    file_ref = db.collection("projects") \
                 .document(data.project_id) \
                 .collection("files") \
                 .document()

    file_ref.set({
        "filename": data.filename,
        "content": data.content,
        "uploaded_at": datetime.utcnow()
    })

    return {"status": "uploaded", "file_id": file_ref.id}


# -----------------------------------------------------------
# BASIC PYTHON CODE ANALYZER (AST)
# -----------------------------------------------------------
def analyze_code(code):
    issues = []

    # Catch syntax errors
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        issues.append({
            "type": "syntax_error",
            "message": str(e)
        })
        return issues

    # Example danger detection: eval()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if getattr(node.func, "id", "") == "eval":
                issues.append({
                    "type": "dangerous_function",
                    "message": "Use of eval() detected — this is insecure."
                })

    return issues


# -----------------------------------------------------------
# ANALYZE & SAVE REPORT ENDPOINT
# -----------------------------------------------------------
@app.post("/projects/analyze")
def analyze(data: CodeFile):
    issues = analyze_code(data.content)

    report_ref = db.collection("projects") \
                   .document(data.project_id) \
                   .collection("reports") \
                   .document()

    report_ref.set({
        "filename": data.filename,
        "issues": issues,
        "created_at": datetime.utcnow()
    })

    return {
        "status": "analysis_complete",
        "issues": issues
    }
