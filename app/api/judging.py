from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Score, Submission, RubricCriterion, User, RoleEnum
from app.auth import require_roles
from app.algorithms.normalization import compute_z_score_normalization

router = APIRouter()

class ScoreInput(BaseModel):
    submission_id: int
    criterion_id: int
    raw_score: float
    feedback: str | None = None

@router.post("/evaluate", status_code=status.HTTP_201_CREATED)
def submit_evaluation(
    payload: ScoreInput,
    db: Session = Depends(get_db),
    judge: User = Depends(require_roles(RoleEnum.JUDGE, RoleEnum.ADMIN))
):
    # Verify rubric criterion
    criterion = db.query(RubricCriterion).filter(RubricCriterion.id == payload.criterion_id).first()
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found.")
    
    if payload.raw_score < 0 or payload.raw_score > criterion.max_score:
        raise HTTPException(status_code=422, detail=f"Score must be between 0 and {criterion.max_score}")

    eval_record = db.query(Score).filter(
        Score.submission_id == payload.submission_id,
        Score.judge_id == judge.id,
        Score.criterion_id == payload.criterion_id
    ).first()

    if eval_record:
        eval_record.raw_score = payload.raw_score
        eval_record.feedback = payload.feedback
    else:
        eval_record = Score(
            submission_id=payload.submission_id,
            judge_id=judge.id,
            criterion_id=payload.criterion_id,
            raw_score=payload.raw_score,
            feedback=payload.feedback
        )
        db.add(eval_record)

    db.commit()
    return {"message": "Score saved successfully"}

@router.get("/results/normalized")
def get_normalized_rankings(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))
):
    """Computes cross-judge z-score normalization across all submitted rubrics."""
    scores = db.query(Score, RubricCriterion).join(RubricCriterion, Score.criterion_id == RubricCriterion.id).all()
    
    # Calculate weighted points per evaluation
    eval_list = []
    for score, criterion in scores:
        eval_list.append({
            "submission_id": score.submission_id,
            "judge_id": score.judge_id,
            "weighted_score": score.raw_score * criterion.weight
        })

    rankings = compute_z_score_normalization(eval_list)
    return [{"submission_id": sub_id, "final_normalized_score": score} for sub_id, score in rankings.items()]
