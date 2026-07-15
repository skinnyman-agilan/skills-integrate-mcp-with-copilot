"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import sqlite3
from pathlib import Path

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)

DB_PATH = current_dir / "activities.db"
INITIAL_ACTIVITIES = [
    {
        "name": "Chess Club",
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    {
        "name": "Programming Class",
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    {
        "name": "Gym Class",
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    {
        "name": "Soccer Team",
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    {
        "name": "Basketball Team",
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    {
        "name": "Art Club",
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    {
        "name": "Drama Club",
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    {
        "name": "Math Club",
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    {
        "name": "Debate Team",
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
]


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_name TEXT NOT NULL,
                email TEXT NOT NULL,
                UNIQUE(activity_name, email),
                FOREIGN KEY(activity_name) REFERENCES activities(name)
            );
            """
        )
        conn.commit()

        activity_count = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
        if activity_count == 0:
            for activity in INITIAL_ACTIVITIES:
                conn.execute(
                    "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
                    (
                        activity["name"],
                        activity["description"],
                        activity["schedule"],
                        activity["max_participants"],
                    ),
                )
                for email in activity["participants"]:
                    conn.execute(
                        "INSERT INTO participants (activity_name, email) VALUES (?, ?)",
                        (activity["name"], email),
                    )
            conn.commit()
    finally:
        conn.close()


init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    conn = get_db_connection()
    try:
        activity_rows = conn.execute(
            "SELECT name, description, schedule, max_participants FROM activities ORDER BY name"
        ).fetchall()
        activities = {}
        for row in activity_rows:
            participant_rows = conn.execute(
                "SELECT email FROM participants WHERE activity_name = ? ORDER BY email",
                (row["name"],),
            ).fetchall()
            activities[row["name"]] = {
                "description": row["description"],
                "schedule": row["schedule"],
                "max_participants": row["max_participants"],
                "participants": [participant["email"] for participant in participant_rows],
            }
        return activities
    finally:
        conn.close()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    conn = get_db_connection()
    try:
        activity = conn.execute(
            "SELECT name FROM activities WHERE name = ?",
            (activity_name,),
        ).fetchone()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        existing = conn.execute(
            "SELECT 1 FROM participants WHERE activity_name = ? AND email = ?",
            (activity_name, email),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        conn.execute(
            "INSERT INTO participants (activity_name, email) VALUES (?, ?)",
            (activity_name, email),
        )
        conn.commit()
        return {"message": f"Signed up {email} for {activity_name}"}
    finally:
        conn.close()


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    conn = get_db_connection()
    try:
        activity = conn.execute(
            "SELECT name FROM activities WHERE name = ?",
            (activity_name,),
        ).fetchone()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        existing = conn.execute(
            "SELECT 1 FROM participants WHERE activity_name = ? AND email = ?",
            (activity_name, email),
        ).fetchone()
        if not existing:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity",
            )

        conn.execute(
            "DELETE FROM participants WHERE activity_name = ? AND email = ?",
            (activity_name, email),
        )
        conn.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}
    finally:
        conn.close()
