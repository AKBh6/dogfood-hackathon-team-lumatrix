# fix_models.py
import os

content = """import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class RoleEnum(str, enum.Enum):
    PARTICIPANT = "Participant"
    JUDGE = "Judge"
    ORGANIZER = "Organizer"
    ADMIN = "Admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.PARTICIPANT)

    team_memberships = relationship("TeamMember", back_populates="user")
    scores = relationship("Score", back_populates="judge")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    invite_code = Column(String, unique=True, nullable=False)

    members = relationship("TeamMember", back_populates="team")
    submissions = relationship("Submission", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_leader = Column(Boolean, default=False)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    demo_url = Column(String, nullable=True)
    is_draft = Column(Boolean, default=True)

    team = relationship("Team", back_populates="submissions")
    scores = relationship("Score", back_populates="submission")

class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    weight = Column(Float, default=1.0)
    max_score = Column(Float, default=10.0)

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    judge_id = Column(Integer, ForeignKey("users.id"))
    criterion_id = Column(Integer, ForeignKey("rubric_criteria.id"))
    raw_score = Column(Float, nullable=False)
    feedback = Column(String, nullable=True)

    submission = relationship("Submission", back_populates="scores")
    judge = relationship("User", back_populates="scores")
"""

with open("app/models.py", "w", encoding="utf-8") as f:
    f.write(content.strip())

print("app/models.py updated successfully!")