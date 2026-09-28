import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, 
    DateTime, ForeignKey, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

class RoleEnum(str, enum.Enum):
    PARTICIPANT = "PARTICIPANT"
    JUDGE = "JUDGE"
    ORGANIZER = "ORGANIZER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum, native_enum=False), default=RoleEnum.PARTICIPANT, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    team_memberships = relationship("TeamMember", back_populates="user")
    assigned_scores = relationship("Score", back_populates="judge")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    submission_deadline = Column(DateTime, nullable=False)
    voting_deadline = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    rubrics = relationship("RubricCriterion", back_populates="event")
    teams = relationship("Team", back_populates="event")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    invite_code = Column(String(64), unique=True, index=True, nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    event = relationship("Event", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
    submission = relationship("Submission", back_populates="team", uselist=False)

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    is_leader = Column(Boolean, default=False)

    user = relationship("User", back_populates="team_memberships")
    team = relationship("Team", back_populates="members")
    __table_args__ = (UniqueConstraint("user_id", "team_id", name="uq_user_team"),)

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    repo_url = Column(String(512), nullable=False)
    demo_url = Column(String(512), nullable=True)
    is_draft = Column(Boolean, default=True)
    submitted_at = Column(DateTime, nullable=True)

    team = relationship("Team", back_populates="submission")
    scores = relationship("Score", back_populates="submission")

class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    max_score = Column(Float, default=10.0)

    event = relationship("Event", back_populates="rubrics")

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    judge_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    criterion_id = Column(Integer, ForeignKey("rubric_criteria.id"), nullable=False)
    raw_score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    submission = relationship("Submission", back_populates="scores")
    judge = relationship("User", back_populates="assigned_scores")
    __table_args__ = (UniqueConstraint("submission_id", "judge_id", "criterion_id", name="uq_judge_criterion_eval"),)
