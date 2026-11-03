from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app import db, auth, users, missions, vision
from backend.app.db import get_db
from backend.app.schemas import UserCreate, UserRead, MissionRead, ObjectiveRead, ObjectiveCreate, UserMission as UserMissionSchema, HarvestUpdate
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
import io
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import Harvest, UserMission, Objective, Mission
import json

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="frontend/templates")

async def get_current_active_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> users.User:
    decoded = auth.decode_access_token(token)
    if not decoded:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await users.get_user_by_username(db, decoded.get("sub"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# Dependency to check if user is logged in
async def require_auth(current_user: users.User = Depends(get_current_active_user)):
    return current_user

# Dependency to check if user is admin
async def require_admin(current_user: users.User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user

# Helper for current user dependency

@router.get("/login")
async def login_page():
    return HTMLResponse(content="""
    <html>
        <head><title>Login</title></head>
        <body>
            <h1>Login</h1>
            <p>Please log in to access the tracker.</p>
        </body>
    </html>
    """)

@router.post("/auth/register", response_model=UserRead)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await users.get_user_by_username(db, user_in.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    user = await users.create_user(db, user_in)
    return user

@router.post("/auth/login")
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await users.get_user_by_username(db, user_in.username)
    if not user or not auth.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/missions", response_model=List[MissionRead])
async def list_missions(db: AsyncSession = Depends(get_db)):
    return await missions.get_missions(db)

@router.post("/missions", response_model=MissionRead)
async def create_mission(mission_in: MissionRead, db: AsyncSession = Depends(get_db)):
    return await missions.create_mission(db, mission_in)

@router.post("/missions/{mission_id}/objectives", response_model=ObjectiveRead)
async def create_objective(mission_id: int, objective_in: ObjectiveCreate, db: AsyncSession = Depends(get_db)):
    return await missions.create_objective(db, mission_id, objective_in)

@router.post("/missions/{mission_id}/start", response_model=UserMissionSchema)
async def start_mission(mission_id: int, current_user: users.User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    stmt = select(UserMission).where(UserMission.mission_id == mission_id, UserMission.status == "Active")
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mission already active for a user.")
    
    obj_stmt = select(Objective).where(Objective.mission_id == mission_id).order_by(Objective.order_index.asc()).limit(1)
    obj_res = await db.execute(obj_stmt)
    first_obj = obj_res.scalars().first()
    
    if not first_obj:
        raise HTTPException(status_code=404, detail="Mission has no objectives.")
    
    new_um = UserMission(
        user_id=current_user.id,
        mission_id=mission_id,
        current_objective_id=first_obj.id,
        status="Active"
    )
    db.add(new_um)
    await db.commit()
    await db.refresh(new_um)
    return new_um

@router.get("/user/missions")
async def get_user_missions(current_user: users.User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return await missions.get_user_missions(db, current_user.id)

@router.post("/missions/{user_mission_id}/complete-objective")
async def complete_objective(user_mission_id: int, db: AsyncSession = Depends(get_db)):
    result = await missions.complete_objective(db, user_mission_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User mission not found or not active")
    return {"status": "success", "current_objective_id": result.current_objective_id, "status": result.status}

@router.get("/")
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    print(f"DEBUG: Accessing root URL via {request.method} {request.url.path}")
    return RedirectResponse(url="/login")

@router.get("/dashboard")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserMission).where(UserMission.status == "Active"))
    active_missions = result.scalars().all()
    
    mission_data = []
    for um in active_missions:
        m_stmt = select(Mission).where(Mission.id == um.mission_id)
        m_res = await db.execute(m_stmt)
        mission = m_res.scalars().first()
        
        o_stmt = select(Objective).where(Objective.mission_id == um.mission_id).order_by(Objective.order_index.asc())
        o_res = await db.execute(o_stmt)
        objectives = o_res.scalars().all()
        
        current_obj_index = -1
        if um.current_objective_id:
            for i, obj in enumerate(objectives):
                if obj.id == um.current_objective_id:
                    current_obj_index = i
                    break
        
        progress = 0
        if objectives:
            if current_obj_index >= 0:
                progress = ((current_obj_index + 1) / len(objectives)) * 100
            else:
                progress = 0
        else:
            progress = 100
            
        mission_data.append({
            "id": um.id,
            "title": mission.title,
            "description": mission.description,
            "current_objective_id": um.current_objective_id,
            "progress": round(progress),
            "mission": mission
        })
    
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"active_missions": mission_data})

@router.get("/leaderboard")
async def leaderboard(request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from backend.app.models import User
    res = await db.execute(select(User.username, User.points).order_by(User.points.desc()))
    leaderboard = res.all()
    return templates.TemplateResponse(request=request, name="leaderboard.html", context={"leaderboard": leaderboard})

@router.get("/mission/{mission_id}")
async def mission_detail(request: Request, mission_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Mission).where(Mission.id == mission_id)
    res = await db.execute(stmt)
    mission = res.scalars().first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return templates.TemplateResponse(request=request, name="mission_detail.html", context={"mission": mission})

@router.post("/harvest/upload")
async def upload_harvest(
    file: UploadFile = File(...), 
    current_user: users.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    content = await file.read()
    harvest_data = await vision.extract_harvest_data(content)
    stmt = select(UserMission).where(
        UserMission.user_id == current_user.id,
        UserMission.status == "Active"
    )
    res = await db.execute(stmt)
    active_mission_record = res.scalars().first()
    
    if not active_mission_record:
        raise HTTPException(status_code=400, detail="No active mission found for this user.")
    
    new_harvest = Harvest(
        user_id=current_user.id,
        image_url="placeholder_url",
        extracted_data=harvest_data,
        status="Pending"
    )
    db.add(new_harvest)
    await db.commit()
    await db.refresh(new_harvest)
    
    return {
        "status": "summary_ready",
        "harvest_id": new_harvest.id,
        "summary": {
            "species": harvest_data.get("species"),
            "location": harvest_data.get("location"),
            "class": harvest_data.get("class"),
            "gender": harvest_data.get("gender"),
            "weight": harvest_data.get("weight"),
            "fur_type": harvest_data.get("fur_type"),
            "tracking_distance": harvest_data.get("tracking_distance"),
            "difficulty": harvest_data.get("difficulty"),
            "trophy_type": harvest_data.get("trophy_type"),
            "trophy_organs": harvest_data.get("trophy_organs"),
            "trophy_tier": harvest_data.get("trophy_tier"),
            "trophy_rating": harvest_data.get("trophy_rating"),
            "harvest_checks": harvest_data.get("harvest_checks"),
            "xp": harvest_data.get("xp"),
            "cash": harvest_data.get("cash"),
            "session_score": harvest_data.get("session_score"),
            "organs_high": harvest_data.get("organs_high"),
            "weapon": harvest_data.get("weapon"),
            "ammo": harvest_data.get("ammo"),
            "distance": harvest_data.get("distance"),
            "weapon_score": harvest_data.get("weapon_score")
        },
        "message": "Please confirm if the extracted harvest details are correct."
    }

@router.post("/harvest/{harvest_id}/confirm")
async def confirm_harvest(
    harvest_id: int,
    db: AsyncSession = Depends(get_db)
):
    harvest = await db.get(Harvest, harvest_id)
    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")
    
    active_mission_stmt = select(UserMission).where(
        UserMission.user_id == harvest.user_id,
        UserMission.status == "Active"
    )
    res = await db.execute(active_mission_stmt)
    active_mission_record = res.scalars().first()
    
    if not active_mission_record:
        raise HTTPException(status_code=400, detail="No active mission found to verify this harvest.")
    
    obj_stmt = select(Objective).where(Objective.id == active_mission_record.current_objective_id)
    obj_res = await db.execute(obj_stmt)
    objective = obj_res.scalars().first()
    
    if not objective:
        raise HTTPException(status_code=400, detail="Active mission has no current objective.")
    
    is_valid = await missions.validate_harvest(harvest.extracted_data, objective)
    
    if is_valid:
        await missions.complete_objective(db, active_mission_record.id)
        return {"status": "success", "message": f"Objective '{objective.description}' completed!"}
    else:
        raise HTTPException(status_code=400, detail=f"Harvest data {harvest.extracted_data} did not match objective requirements: {objective.requirements}")

@router.post("/harvest/{harvest_id}/correct")
async def correct_harvest(
    harvest_id: int,
    corrected_data: HarvestUpdate,
    db: AsyncSession = Depends(get_db)
):
    harvest = await db.get(Harvest, harvest_id)
    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")
    
    if corrected_data.extracted_data:
        harvest.extracted_data = corrected_data.extracted_data
        await db.commit()
        await db.refresh(harvest)
    
    active_mission_stmt = select(UserMission).where(
        UserMission.user_id == harvest.user_id,
        UserMission.status == "Active"
    )
    res = await db.execute(active_mission_stmt)
    active_mission_record = res.scalars().first()
    
    if active_mission_record:
        obj_stmt = select(Objective).where(Objective.id == active_mission_record.current_objective_id)
        obj_res = await db.execute(obj_stmt)
        objective = obj_res.scalars().first()
        
        if objective:
            is_valid = await missions.validate_harvest(harvest.extracted_data, objective)
            if is_valid:
                await missions.complete_objective(db, active_mission_record.id)
                return {"status": "success", "message": f"Corrected information validated and objective '{objective.description}' completed!"}
    
    return {"status": "corrected", "message": "Harvest data updated successfully."}

@router.get("/admin/missions", response_model=List[MissionRead])
async def admin_list_missions(db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    res = await db.execute(select(Mission))
    return res.scalars().all()

@router.post("/admin/missions", response_model=MissionRead)
async def admin_create_mission(mission_in: MissionRead, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    mission = Mission(**mission_in.dict(exclude={"id"}))
    db.add(mission)
    await db.commit()
    await db.refresh(mission)
    return mission

@router.put("/admin/missions/{mission_id}", response_model=MissionRead)
async def admin_update_mission(mission_id: int, mission_in: MissionRead, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    for key, value in mission_in.dict(exclude={"id"}).items():
        setattr(mission, key, value)
    await db.commit()
    await db.refresh(mission)
    return mission

@router.delete("/admin/missions/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_mission(mission_id: int, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    await db.delete(mission)
    await db.commit()
    return None

@router.get("/admin/objectives", response_model=List[ObjectiveRead])
async def admin_list_objectives(db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    res = await db.execute(select(Objective))
    return res.scalars().all()

@router.post("/admin/objectives", response_model=ObjectiveRead)
async def admin_create_objective(objective_in: ObjectiveCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    objective = Objective(**objective_in.dict())
    db.add(objective)
    await db.commit()
    await db.refresh(objective)
    return objective

@router.put("/admin/objectives/{objective_id}", response_model=ObjectiveRead)
async def admin_update_objective(objective_id: int, objective_in: ObjectiveCreate, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    objective = await db.get(Objective, objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")
    for key, value in objective_in.dict().items():
        setattr(objective, key, value)
    await db.commit()
    await db.refresh(objective)
    return objective

@router.delete("/admin/objectives/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_objective(objective_id: int, db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    objective = await db.get(Objective, objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")
    await db.delete(objective)
    await db.commit()
    return None
