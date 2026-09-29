import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum, UniqueConstraint
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
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    assigned_scores = relationship("Score", back_populates="judge")
    judge_assignments = relationship("JudgeAssignment", back_populates="judge", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    submission_deadline = Column(DateTime, nullable=False)
    voting_deadline = Column(DateTime, nullable=False)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    tracks = Column(Text, nullable=False, default="")
    prizes = Column(Text, nullable=False, default="")
    custom_questions = Column(Text, nullable=False, default="")
    is_active = Column(Boolean, default=True, nullable=False)
    rubrics = relationship("RubricCriterion", back_populates="event", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="event", cascade="all, delete-orphan")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    invite_code = Column(String(64), unique=True, index=True, nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    event = relationship("Event", back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    submission = relationship("Submission", back_populates="team", uselist=False, cascade="all, delete-orphan")

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    is_leader = Column(Boolean, default=False, nullable=False)
    user = relationship("User", back_populates="team_memberships")
    team = relationship("Team", back_populates="members")
    __table_args__ = (UniqueConstraint("user_id", "team_id", name="uq_user_team"),)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    tagline = Column(String(255), nullable=True)
    thumbnail_url = Column(String(512), nullable=True)
    image_gallery = Column(Text, nullable=False, default="")
    demo_video_url = Column(String(512), nullable=True)
    live_url = Column(String(512), nullable=True)
    tech_tags = Column(Text, nullable=False, default="")
    track = Column(String(100), nullable=True)
    custom_answers = Column(Text, nullable=False, default="")
    repo_url = Column(String(512), nullable=False)
    demo_url = Column(String(512), nullable=True)
    is_draft = Column(Boolean, default=True, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    team = relationship("Team", back_populates="submission")
    scores = relationship("Score", back_populates="submission", cascade="all, delete-orphan")
    assignments = relationship("JudgeAssignment", back_populates="submission", cascade="all, delete-orphan")

class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0, nullable=False)
    max_score = Column(Float, default=10.0, nullable=False)
    event = relationship("Event", back_populates="rubrics")

class JudgeInvitation(Base):
    __tablename__ = "judge_invitations"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    email = Column(String(255), nullable=False)
    token = Column(String(128), unique=True, index=True, nullable=False)
    invited_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    accepted_at = Column(DateTime, nullable=True)

class JudgeTrack(Base):
    __tablename__ = "judge_tracks"
    id = Column(Integer, primary_key=True, index=True)
    judge_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    track = Column(String(100), nullable=False)
    __table_args__ = (UniqueConstraint("judge_id", "event_id", "track", name="uq_judge_event_track"),)

class JudgeAssignment(Base):
    __tablename__ = "judge_assignments"
    id = Column(Integer, primary_key=True, index=True)
    judge_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    judge = relationship("User", back_populates="judge_assignments")
    submission = relationship("Submission", back_populates="assignments")
    __table_args__ = (UniqueConstraint("judge_id", "submission_id", name="uq_judge_submission"),)

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
    criterion = relationship("RubricCriterion")
    __table_args__ = (UniqueConstraint("submission_id", "judge_id", "criterion_id", name="uq_judge_criterion_eval"),)
