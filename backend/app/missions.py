from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db import get_db
from backend.app.models import Mission, Objective, UserMission, User
from backend.app.schemas import MissionRead, ObjectiveRead
from typing import List, Optional

async def create_mission(db: AsyncSession, mission_in: MissionRead) -> Mission:
    new_mission = Mission(
        title=mission_in.title,
        description=mission_in.description,
        base_points=mission_in.base_points
    )
    db.add(new_mission)
    await db.commit()
    await db.refresh(new_mission)
    return new_mission

async def create_objective(db: AsyncSession, mission_id: int, objective_in: ObjectiveRead) -> Objective:
    new_obj = Objective(
        mission_id=mission_id,
        description=objective_in.description,
        order_index=objective_in.order_index,
        is_completed=False
    )
    db.add(new_obj)
    await db.commit()
    await db.refresh(new_obj)
    return new_obj

async def get_missions(db: AsyncSession) -> List[Mission]:
    result = await db.execute(select(Mission))
    return list(result.scalars().all())

async def get_user_missions(db: AsyncSession, user_id: int) -> List[UserMission]:
    result = await db.execute(select(UserMission).where(UserMission.user_id == user_id))
    return list(result.scalars().all())

async def validate_harvest(harvest_data: dict, objective: Objective) -> bool:
    # Validate extraction data against objective requirements
    reqs = objective.requirements
    if not reqs:
        return True

    # Map of requirement keys to their validation logic
    # Each logic function returns False if the requirement is not met
    rules = {
        "species": lambda val, req: val == req,
        "location": lambda val, req: val == req,
        "class": lambda val, req: val == req,
        "gender": lambda val, req: val == req,
        "fur_type": lambda val, req: val == req,
        "trophy_type": lambda val, req: val == req,
        "trophy_tier": lambda val, req: val == req,
        "weapon": lambda val, req: val == req,
        "ammo": lambda val, req: val == req,
        "difficulty": lambda val, req: val == req,
        "min_weight": lambda val, req: val >= req,
        "max_tracking": lambda val, req: val <= req,
        "max_distance": lambda val, req: val <= req,
        "min_score": lambda val, req: val >= req,
        "min_session": lambda val, req: val >= req,
        "min_rating": lambda val, req: val >= req,
        "min_xp": lambda val, req: val >= req,
        "min_cash": lambda val, req: val >= req,
        "required_organs": lambda val, req: all(org in (harvest_data.get("trophy_organs", []) + harvest_data.get("organs_hit", [])) for org in req),
        "organs_high": lambda val, req: all(org in harvest_data.get("organs_high", []) for org in req),
        "harvest_checks": lambda val, req: all(req),
    }

    for key, requirement_value in reqs.items():
        if key not in rules:
            continue
            
        # Determine correct field in harvest_data to compare against
        # Some keys in reqs map to different keys in harvest_data
        field_map = {
            "min_weight": "weight",
            "max_tracking": "tracking_distance",
            "max_distance": "distance",
            "min_score": "weapon_score",
            "min_session": "session_score",
            "min_rating": "trophy_rating",
            "min_xp": "xp",
            "min_cash": "cash",
            "required_organs": "trophy_organs",
            "organs_high": "organs_high",
            "harvest_checks": "harvest_checks"
        }
        
        actual_value = harvest_data.get(field_map.get(key, key))
        
        if actual_value is None:
            # If a required field is missing from harvest data, it fails validation
            return False
            
        if not rules[key](actual_value, requirement_value):
            return False

    return True

async def complete_objective(db: AsyncSession, user_mission_id: int) -> Optional[UserMission]:
    # 1. Fetch user mission
    stmt = select(UserMission).where(UserMission.id == user_mission_id)
    result = await db.execute(stmt)
    user_mission = result.scalars().first()
    
    if not user_mission or user_mission.status != "Active":
        return None

    # 2. Get the current objective
    obj_stmt = select(Objective).where(Objective.id == user_mission.current_objective_id)
    obj_result = await db.execute(obj_stmt)
    current_obj = obj_result.scalars().first()

    if current_obj is not None:
        current_obj.is_completed = True
        await db.commit()
        await db.refresh(current_obj)

    # 3. Find next objective
    next_obj_stmt = select(Objective).where(
        Objective.mission_id == user_mission.mission_id,
        Objective.order_index > current_obj.order_index
    ).order_by(Objective.order_index.asc()).limit(1)

    next_obj_result = await db.execute(next_obj_stmt)
    next_obj = next_obj_result.scalars().first()

    if next_obj:
        user_mission.current_objective_id = next_obj.id
    else:
        user_mission.status = "Completed"
        # Award mission points (simplified for now)
        # We'd want to find the mission and update the user's total points
        user_stmt = select(User).where(User.id == user_mission.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalars().first()
        if user:
            user.points += user_mission.mission.base_points
            
    await db.commit()
    await db.refresh(user_mission)
    return user_mission

async def get_leaderboard(db: AsyncSession) -> List[tuple]:
    stmt = select(User.username, User.points).order_by(User.points.desc())
    result = await db.execute(stmt)
    return [tuple(row) for row in result.all()]
