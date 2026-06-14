from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_db
from fastapi import FastAPI, UploadFile, File
import os
import shutil
from auth import authenticate_user, create_token, verify_token
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token!")
    return username

app= FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def home():
    return {"message": "Welcome to Resume DB"}



from pydantic import BaseModel 
from typing import Optional, List
import json 

class Resume(BaseModel):
    name: str
    title: str
    location: str
    exp: int
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    edu: Optional[str] = None 
    skills: Optional[List[str]] = []
    summary: Optional[str] = None
    status: Optional[str] = 'active'

@app.post("/resumes")
def add_resume(resume: Resume):
    conn = get_db()
    conn.execute("""
    INSERT INTO resumes
    (name, title, location, exp, email, phone, company, edu, skills, summary, status)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        resume.name, resume.title, resume.location, resume.exp, resume.email, resume.phone, resume.company, resume.edu,
        json.dumps(resume.skills), resume.summary, resume.status 
    ))

    conn.commit()
    conn.close()
    return{"Message":"Resume added successfully"}

@app.get("/resumes")
def get_resumes(
    location: Optional[str] = None,
    exp_min: Optional[int] = None,
    exp_max: Optional[int] = None,
    edu: Optional[str] = None,
    skills: Optional[str] = None
):
    conn = get_db()
    sql = "SELECT * FROM resumes WHERE 1=1"
    params = []

    if location:
        sql += " AND location = ?"
        params.append(location)
    if exp_min is not None:
        sql += " AND exp >= ?"
        params.append(exp_min)
    if exp_max is not None:
        sql += " AND exp <= ?"
        params.append(exp_max)
    if edu:
        sql += " AND edu = ?"
        params.append(edu)

    resumes = conn.execute(sql, params).fetchall()
    conn.close()

    results = [dict(r) for r in resumes]

    if skills:
        skill_list = [s.strip().lower() for s in skills.split(",")]
        results = [
            r for r in results
            if any(s.lower() in skill_list for s in eval(r["skills"] or "[]"))
        ]

    return results

@app.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int):
    conn = get_db()
    conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
    conn.commit()
    conn.close()
    return {"message": "Resume deleted successfully!"}

@app.put("/resumes/{resume_id}")
def update_resume(resume_id: int, resume: Resume):
    conn = get_db()
    conn.execute("""
        UPDATE resumes 
        SET name=?, title=?, location=?, exp=?, email=?, 
            phone=?, company=?, edu=?, skills=?, summary=?, status=?
        WHERE id=?
    """, (
        resume.name, resume.title, resume.location, resume.exp,
        resume.email, resume.phone, resume.company, resume.edu,
        json.dumps(resume.skills), resume.summary, resume.status,
        resume_id
    ))
    conn.commit()
    conn.close()
    return {"message": "Resume updated successfully!"}

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload/{resume_id}")
async def upload_resume(resume_id: int, file: UploadFile = File(...)):
    file_path = f"{UPLOAD_FOLDER}/{resume_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "File uploaded successfully!", "file": file_path}

@app.get("/download/{resume_id}")
async def download_resume(resume_id: int):
    folder = UPLOAD_FOLDER
    for filename in os.listdir(folder):
        if filename.startswith(f"{resume_id}_"):
            from fastapi.responses import FileResponse
            return FileResponse(f"{folder}/{filename}", filename=filename)
    return {"error": "No file found for this resume"}


from fastapi.security import OAuth2PasswordRequestForm

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Wrong username or password!")
    token = create_token(user["username"])
    return {"access_token": token, "token_type": "bearer"}