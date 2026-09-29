import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Score, Submission, RubricCriterion, User, RoleEnum, JudgeAssignment, Team
from app.auth import require_roles
from app.algorithms.normalization import compute_z_score_normalization

router = APIRouter()

class ScoreInput(BaseModel):
    submission_id: int
    criterion_id: int
    raw_score: float
    feedback: str | None = None

def assert_assigned(db, judge_id, submission_id):
    if not db.query(JudgeAssignment).filter_by(judge_id=judge_id, submission_id=submission_id).first():
        raise HTTPException(403, "This submission is not assigned to you.")

@router.post("/evaluate", status_code=status.HTTP_200_OK)
def submit_evaluation(payload: ScoreInput, db: Session = Depends(get_db), judge: User = Depends(require_roles(RoleEnum.JUDGE, RoleEnum.ADMIN))):
    if judge.role == RoleEnum.JUDGE:
        assert_assigned(db, judge.id, payload.submission_id)
    submission = db.query(Submission).filter_by(id=payload.submission_id).first()
    criterion = db.query(RubricCriterion).filter_by(id=payload.criterion_id).first()
    if not submission or not criterion:
        raise HTTPException(404, "Submission or criterion not found.")
    if submission.team.event_id != criterion.event_id:
        raise HTTPException(400, "Criterion does not belong to this event.")
    if payload.raw_score < 0 or payload.raw_score > criterion.max_score:
        raise HTTPException(422, f"Score must be between 0 and {criterion.max_score}.")
    score = db.query(Score).filter_by(submission_id=submission.id, judge_id=judge.id, criterion_id=criterion.id).first()
    if score:
        score.raw_score, score.feedback = payload.raw_score, payload.feedback
    else:
        db.add(Score(submission_id=submission.id, judge_id=judge.id, criterion_id=criterion.id, raw_score=payload.raw_score, feedback=payload.feedback))
    db.commit()
    return {"message":"Score saved successfully"}

def ranking_rows(db):
    rows = db.query(Score, RubricCriterion).join(RubricCriterion, Score.criterion_id == RubricCriterion.id).all()
    evaluations = [{"submission_id":s.submission_id,"judge_id":s.judge_id,"weighted_score":(s.raw_score/c.max_score)*c.weight*100 if c.max_score else 0} for s,c in rows]
    normalized = compute_z_score_normalization(evaluations)
    raw = {}
    for e in evaluations:
        raw.setdefault(e["submission_id"], []).append(e["weighted_score"])
    result=[]
    for sid, values in raw.items():
        sub=db.query(Submission).filter_by(id=sid).first()
        result.append({"submission_id":sid,"team":sub.team.name,"project":sub.title,"raw_score":round(sum(values),2),"normalized_score":normalized.get(sid,0)})
    return sorted(result,key=lambda x:x["normalized_score"],reverse=True)

@router.get("/results/normalized")
def get_normalized_rankings(db: Session = Depends(get_db), admin: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    return ranking_rows(db)

@router.get("/results.csv")
def export_results(db: Session = Depends(get_db), admin: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    output=io.StringIO()
    writer=csv.DictWriter(output,fieldnames=["rank","team","project","raw_score","normalized_score"])
    writer.writeheader()
    for rank,row in enumerate(ranking_rows(db),1):
        writer.writerow({"rank":rank,**{k:row[k] for k in ["team","project","raw_score","normalized_score"]}})
    return Response(output.getvalue(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=results.csv"})
