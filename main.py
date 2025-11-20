import os
from datetime import date, datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from database import create_document, get_documents
from schemas import Motherprofile, Note

app = FastAPI(title="New Mum Companion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "New Mum Companion API is running"}

@app.get("/schema")
def get_schema_info():
    # Simple schema info endpoint for tooling
    return {
        "collections": [
            "motherprofile",
            "note",
        ]
    }

class ProfileRequest(BaseModel):
    name: str
    email: str
    last_period_date: Optional[date] = None
    due_date: Optional[date] = None

@app.post("/profile")
def create_or_update_profile(payload: ProfileRequest):
    try:
        # If only LMP provided, estimate due date (Naegel's rule: LMP + 280 days)
        lmp = payload.last_period_date
        edd = payload.due_date
        if lmp and not edd:
            edd = (datetime.combine(lmp, datetime.min.time())).date().fromordinal(
                lmp.toordinal() + 280
            )
        data = Motherprofile(
            name=payload.name,
            email=payload.email,
            last_period_date=lmp,
            due_date=edd,
        )
        inserted_id = create_document("motherprofile", data)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content/weeks")
def get_weekly_content(week: int):
    if week < 1 or week > 42:
        raise HTTPException(status_code=400, detail="Week must be between 1 and 42")
    # Very simple curated weekly content
    stages = _generate_weekly_stages()
    item = next((s for s in stages if s["week"] == week), None)
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    return item

@app.get("/content/birth")
def get_birth_content(mode: str = "vaginal"):
    mode = (mode or "vaginal").lower()
    if mode not in ["vaginal", "cesarean"]:
        raise HTTPException(status_code=400, detail="mode must be 'vaginal' or 'cesarean'")
    content = _birth_content()[mode]
    return content

class NoteRequest(BaseModel):
    email: str
    week: int
    text: str

@app.post("/notes")
def add_note(note: NoteRequest):
    try:
        data = Note(email=note.email, week=note.week, text=note.text)
        note_id = create_document("note", data)
        return {"status": "ok", "id": note_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notes")
def list_notes(email: str, week: Optional[int] = None):
    try:
        filter_dict = {"email": email}
        if week is not None:
            filter_dict["week"] = week
        docs = get_documents("note", filter_dict=filter_dict, limit=100)
        # Convert ObjectId to str if present
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_weekly_stages():
    # Simplified, encouraging content for weeks 1-40, with buffer 41-42
    stages = []
    for w in range(1, 43):
        if w < 5:
            title = "Early signs and gentle care"
            mom = "You might just have found out. Rest, hydrate, and take folic acid."
            baby = "Cells are rapidly dividing. The foundation is forming."
        elif w < 13:
            title = "First trimester milestones"
            mom = "Fatigue and nausea are common. Small, frequent meals help."
            baby = "Tiny organs are forming. A heartbeat may be detectable."
        elif w < 28:
            title = "Second trimester comfort"
            mom = "Energy often returns. Start light movement and routine checkups."
            baby = "Growing steadily; senses begin developing."
        elif w < 37:
            title = "Third trimester prep"
            mom = "Body feels heavier. Practice gentle stretching and birth planning."
            baby = "Putting on weight and maturing lungs."
        elif w < 41:
            title = "Almost there"
            mom = "Have your hospital bag ready. Notice baby's movements."
            baby = "Full term is near. Baby is ready for the world."
        else:
            title = "Extra monitoring"
            mom = "Stay in close contact with your provider for plans."
            baby = "Awaiting a cozy arrival."
        stages.append({
            "week": w,
            "title": title,
            "mother_tips": mom,
            "baby_development": baby,
        })
    return stages


def _birth_content():
    return {
        "vaginal": {
            "title": "Vaginal (Natural) Birth",
            "overview": "Most births are vaginal. Your care team supports you through stages of labor with pain relief options and close monitoring.",
            "stages": [
                {"name": "Early labor", "info": "Mild, irregular contractions. Rest, hydrate, and breathe."},
                {"name": "Active labor", "info": "Stronger contractions, 3-5 minutes apart. Pain relief options available."},
                {"name": "Transition", "info": "Intense but brief phase leading to pushing."},
                {"name": "Pushing & birth", "info": "Baby is born. Skin-to-skin and first feed encouraged."},
            ],
            "when_to_seek_help": [
                "Bleeding more than a period",
                "Baby's movements reduce",
                "Waters break with green/brown fluid",
            ],
            "recovery": "Soreness is common. Use peri care, rest, hydrate, and accept help." 
        },
        "cesarean": {
            "title": "Cesarean (C-Section) Birth",
            "overview": "Sometimes planned, sometimes urgent. Surgery delivers baby safely through the abdomen with anesthesia.",
            "what_to_expect": [
                "Preparation and anesthesia (usually spinal).",
                "Birth happens quickly; baby checked and brought to you.",
                "Stitches or staples close the incision.",
            ],
            "aftercare": "Walk gently early, manage pain, keep incision clean and dry.",
            "recovery_timeline": "Most feel better over 4-6 weeks. Avoid heavy lifting until cleared.",
            "when_to_seek_help": [
                "Fever or spreading redness at incision",
                "Severe pain or heavy bleeding",
                "Shortness of breath or chest pain",
            ],
        },
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
