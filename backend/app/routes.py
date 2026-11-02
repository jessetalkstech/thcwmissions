from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app import db, auth, users, missions, vision
from backend.app.db import get_db
from backend.app.schemas import UserCreate, UserRead, MissionRead, ObjectiveRead, ObjectiveCreate, UserMission, HarvestUpdate
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
import io
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models import Harvest, UserMission, Objective

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="frontend/templates")

# Helper for current user dependency
async def get_current_active_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> users.User:
    decoded = auth.decode_access_token(token)
    if not decoded:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await users.get_user_by_username(db, decoded.get("sub"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

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

@router.post("/missions/{mission_id}/start", response_model=UserMission)
async def start_mission(mission_id: int, current_user: users.User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    # Check if mission already has active user mission
    stmt = select(UserMission).where(UserMission.mission_id == mission_id, UserMission.status == "Active")
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mission already active for a user.")
    
    # Get first objective
    obj_stmt = select(Objective).where(Objective.mission_id == mission_id).order_by(Objective.order_index.asc()).limit(1)
    obj_res = await db.execute(obj_stmt)
    first_obj = obj_res.scalars().first()
    
    if not first_obj:
        raise HTTPException(status_code=404, detail="Mission has no objectives.")
    
    # Create user mission record
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

@router.get("/", response_model=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    return await dashboard(request, db)

@router.get("/dashboard", response_model=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from backend.app.models import UserMission
    result = await db.execute(select(UserMission).where(UserMission.status == "Active"))
    active_missions = result.scalars().all()
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"active_missions": active_missions})

@router.get("/leaderboard", response_model=HTMLResponse)
async def leaderboard(request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from backend.app.models import User
    res = await db.execute(select(User.username, User.points).order_by(User.points.desc()))
    leaderboard = res.all()
    return templates.TemplateResponse(request=request, name="leaderboard.html", context={"leaderboard": leaderboard})

@router.get("/mission/{mission_id}", response_model=HTMLResponse)
async def mission_detail(request: Request, mission_id: int, db: AsyncSession = Depends(get_db)):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"active_missions": []})

@router.post("/harvest/upload")
async def upload_harvest(
    file: UploadFile = File(...), 
    current_user: users.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Read file bytes
    content = await file.read()
    
    # 2. Extract data via Vision
    harvest_data = await vision.extract_harvest_data(content)
    
    # 3. Get the user's active mission status
    from sqlalchemy import select
    from backend.app.models import UserMission
    stmt = select(UserMission).where(
        UserMission.user_id == current_user.id,
        UserMission.status == "Active"
    )
    res = await db.execute(stmt)
    active_mission_record = res.scalars().first()
    
    if not active_mission_record:
        raise HTTPException(status_code=400, detail="No active mission found for this user.")
    
    # 4. Create Harvest record with 'Pending' status
    from backend.app.models import Harvest
    new_harvest = Harvest(
        user_id=current_user.id,
        image_url="placeholder_url",
        extracted_data=harvest_data,
        status="Pending"
    )
    db.add(new_harvest)
    await db.commit()
    await db.refresh(new_harvest)
    
    # 5. Return summary for user confirmation
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
    from backend.app.models import Harvest
    harvest = await db.get(Harvest, harvest_id)
    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")
    
    # Find the active mission record associated with this harvest
    from backend.app.models import UserMission, Objective
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
    
    # Use the logic from missions.py
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
    from backend.app.models import Harvest
    harvest = await db.get(Harvest, harvest_id)
    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")
    
    if corrected_data.extracted_data:
        harvest.extracted_data = corrected_data.extracted_data
        await db.commit()
        await db.refresh(harvest)
    
    # After correction, we can try to validate automatically
    from backend.app.models import UserMission, Objective
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
