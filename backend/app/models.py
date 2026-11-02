from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db import Base

class Harvest(Base):
    __tablename__ = "harvests"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    image_url: Mapped[str] = mapped_column(String(500))
    extracted_data: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20))  # e.g., "Pending", "Processed", "Failed"

    user: Mapped["User"] = relationship("User", back_populates="harvests")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    points: Mapped[int] = mapped_column(default=0)
    missions: Mapped[list["UserMission"]] = relationship("UserMission", back_populates="user")
    harvests: Mapped[list["Harvest"]] = relationship("Harvest", back_populates="user")

class Mission(Base):
    __tablename__ = "missions"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500))
    base_points: Mapped[int] = mapped_column(default=0)
    objectives: Mapped[list["Objective"]] = relationship("Objective", back_populates="mission")

class Objective(Base):
    __tablename__ = "objectives"
    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"))
    description: Mapped[str] = mapped_column(String(500))
    order_index: Mapped[int] = mapped_column(Integer)
    is_completed: Mapped[bool] = mapped_column(default=False)
    requirements: Mapped[dict] = mapped_column(JSON, default={})
    
    mission: Mapped["Mission"] = relationship("Mission", back_populates="objectives")

class UserMission(Base):
    __tablename__ = "user_missions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"))
    current_objective_id: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(20))  # e.g., "Active", "Completed"

    user: Mapped["User"] = relationship("User", back_populates="missions")
    mission: Mapped["Mission"] = relationship("Mission")
