# make_all_rest.py
import os

def clean(text):
    return (text
        .replace("[LT]", "<")
        .replace("[GT]", ">")
        .replace("[BO]", "{%")
        .replace("[BC]", "%}")
        .replace("[VO]", "{{")
        .replace("[VC]", "}}")
    )

files = {
    # -------------------------------------------------------------
    # 1. PARTICIPANT TEMPLATES
    # -------------------------------------------------------------
    "app/templates/participant/team.html": """[BO] extends "base.html" [BC]
[BO] block title [BC]Team Management[BO] endblock [BC]
[BO] block nav [BC]
[LT]a href="/participant/dashboard"[GT]Dashboard[LT]/a[GT]
[LT]a href="/logout"[GT]Logout[LT]/a[GT]
[BO] endblock [BC]

[BO] block content [BC]
[LT]div class="card"[GT]
    [LT]h2[GT]My Team[LT]/h2[GT]
    [BO] if team [BC]
        [LT]p[GT][LT]strong[GT]Team Name:[LT]/strong[GT] [VO] team.name [VC][LT]/p[GT]
        [LT]p[GT][LT]strong[GT]Invite Code:[LT]/strong[GT] [LT]code[GT][VO] team.invite_code [VC][LT]/code[GT][LT]/p[GT]
        [LT]h3[GT]Members[LT]/h3[GT]
        [LT]ul[GT]
        [BO] for m in team.members [BC]
            [LT]li[GT][VO] m.user.full_name [VC] [BO] if m.is_leader [BC](Team Leader)[BO] endif [BC][LT]/li[GT]
        [BO] endfor [BC]
        [LT]/ul[GT]
    [BO] else [BC]
        [LT]p[GT]You are not currently part of any team.[LT]/p[GT]
    [BO] endif [BC]
[LT]/div[GT]
[BO] endblock [BC]""",

    "app/templates/participant/submission.html": """[BO] extends "base.html" [BC]
[BO] block title [BC]Project Submission[BO] endblock [BC]
[BO] block nav [BC]
[LT]a href="/participant/dashboard"[GT]Dashboard[LT]/a[GT]
[LT]a href="/logout"[GT]Logout[LT]/a[GT]
[BO] endblock [BC]

[BO] block content [BC]
[LT]div class="card"[GT]
    [LT]h2[GT]Submit Your Project[LT]/h2[GT]
    [LT]form action="/api/submissions" method="POST" class="form-group"[GT]
        [LT]div class="field"[GT]
            [LT]label for="title"[GT]Project Title[LT]/label[GT]
            [LT]input type="text" id="title" name="title" required value="[VO] submission.title if submission else '' [VC]"[GT]
        [LT]/div[GT]
        [LT]div class="field"[GT]
            [LT]label for="description"[GT]Description[LT]/label[GT]
            [LT]textarea id="description" name="description" rows="4" required[GT][VO] submission.description if submission else '' [VC][LT]/textarea[GT]
        [LT]/div[GT]
        [LT]div class="field"[GT]
            [LT]label for="repo_url"[GT]Repository URL[LT]/label[GT]
            [LT]input type="url" id="repo_url" name="repo_url" required value="[VO] submission.repo_url if submission else '' [VC]"[GT]
        [LT]/div[GT]
        [LT]div class="field"[GT]
            [LT]label for="demo_url"[GT]Demo URL (Optional)[LT]/label[GT]
            [LT]input type="url" id="demo_url" name="demo_url" value="[VO] submission.demo_url if submission else '' [VC]"[GT]
        [LT]/div[GT]
        [LT]button type="submit" class="btn btn-primary"[GT]Save Submission[LT]/button[GT]
    [LT]/form[GT]
[LT]/div[GT]
[BO] endblock [BC]""",

    # -------------------------------------------------------------
    # 2. JUDGE TEMPLATES
    # -------------------------------------------------------------
    "app/templates/judge/assignments.html": """[BO] extends "base.html" [BC]
[BO] block title [BC]Assigned Submissions[BO] endblock [BC]
[BO] block nav [BC]
[LT]a href="/judge/dashboard"[GT]Dashboard[LT]/a[GT]
[LT]a href="/logout"[GT]Logout[LT]/a[GT]
[BO] endblock [BC]

[BO] block content [BC]
[LT]div class="card"[GT]
    [LT]h2[GT]Submissions Pending Evaluation[LT]/h2[GT]
    [BO] if submissions [BC]
        [LT]ul class="assignment-list"[GT]
        [BO] for sub in submissions [BC]
            [LT]li[GT]
                [LT]strong[GT][VO] sub.title [VC][LT]/strong[GT] - Team [VO] sub.team.name [VC]
                [LT]a href="/judge/evaluate/[VO] sub.id [VC]" class="btn btn-primary"[GT]Evaluate[LT]/a[GT]
            [LT]/li[GT]
        [BO] endfor [BC]
        [LT]/ul[GT]
    [BO] else [BC]
        [LT]p[GT]No pending assignments found.[LT]/p[GT]
    [BO] endif [BC]
[LT]/div[GT]
[BO] endblock [BC]""",

    "app/templates/judge/evaluate.html": """[BO] extends "base.html" [BC]
[BO] block title [BC]Evaluate Submission[BO] endblock [BC]
[BO] block nav [BC]
[LT]a href="/judge/assignments"[GT]Assignments[LT]/a[GT]
[LT]a href="/logout"[GT]Logout[LT]/a[GT]
[BO] endblock [BC]

[BO] block content [BC]
[LT]div class="card"[GT]
    [LT]h2[GT]Evaluating: [VO] submission.title [VC][LT]/h2[GT]
    [LT]p[GT][VO] submission.description [VC][LT]/p[GT]
    [LT]p[GT]
        [LT]a href="[VO] submission.repo_url [VC]" target="_blank"[GT]Repository[LT]/a[GT] | 
        [LT]a href="[VO] submission.demo_url [VC]" target="_blank"[GT]Demo Link[LT]/a[GT]
    [LT]/p[GT]

    [LT]form action="/api/judging/evaluate" method="POST" class="form-group"[GT]
        [LT]input type="hidden" name="submission_id" value="[VO] submission.id [VC]"[GT]
        [BO] for criterion in criteria [BC]
        [LT]div class="field"[GT]
            [LT]label for="criterion_[VO] criterion.id [VC]"[GT]
                [VO] criterion.name [VC] (Max: [VO] criterion.max_score [VC], Weight: [VO] criterion.weight [VC])
            [LT]/label[GT]
            [LT]input type="number" id="criterion_[VO] criterion.id [VC]" name="score_[VO] criterion.id [VC]" min="0" max="[VO] criterion.max_score [VC]" step="0.5" required[GT]
        [LT]/div[GT]
        [BO] endfor [BC]
        [LT]div class="field"[GT]
            [LT]label for="feedback"[GT]Feedback / Comments[LT]/label[GT]
            [LT]textarea id="feedback" name="feedback" rows="3"[GT][LT]/textarea[GT]
        [LT]/div[GT]
        [LT]button type="submit" class="btn btn-primary"[GT]Submit Evaluation[LT]/button[GT]
    [LT]/form[GT]
[LT]/div[GT]
[BO] endblock [BC]""",

    # -------------------------------------------------------------
    # 3. ORGANIZER TEMPLATES
    # -------------------------------------------------------------
    "app/templates/organizer/event.html": """[BO] extends "base.html" [BC]
[BO] block title [BC]Event Management[BO] endblock [BC]
[BO] block nav [BC]
[LT]a href="/organizer/dashboard"[GT]Dashboard[LT]/a[GT]
[LT]a href="/logout"[GT]Logout[LT]/a[GT]
[BO] endblock [BC]

[BO] block content [BC]
[LT]div class="card"[GT]
    [LT]h2[GT]Event: [VO] event.title [VC][LT]/h2[GT]
    [LT]p[GT][LT]strong[GT]Slug:[LT]/strong[GT] [VO] event.slug [VC][LT]/p[GT]
    [LT]p[GT][LT]strong[GT]Submission Deadline:[LT]/strong[GT] [VO] event.submission_deadline [VC][LT]/p[GT]
    [LT]p[GT][LT]strong[GT]Voting Deadline:[LT]/strong[GT] [VO] event.voting_deadline [VC][LT]/p[GT]

    [LT]h3[GT]Active Rubrics[LT]/h3[GT]
    [LT]ul[GT]
    [BO] for c in event.rubrics [BC]
        [LT]li[GT][VO] c.name [VC] — Weight: [VO] c.weight [VC], Max Score: [VO] c.max_score [VC][LT]/li[GT]
    [BO] endfor [BC]
    [LT]/ul[GT]
[LT]/div[GT]
[BO] endblock [BC]""",

    "app/templates/organizer/results.html": """[BO] extends "base.html" [BC]
[BO] block title [BC]Event Leaderboard[BO] endblock [BC]
[BO] block nav [BC]
[LT]a href="/organizer/dashboard"[GT]Dashboard[LT]/a[GT]
[LT]a href="/logout"[GT]Logout[LT]/a[GT]
[BO] endblock [BC]

[BO] block content [BC]
[LT]div class="card"[GT]
    [LT]h2[GT]Normalized Results Leaderboard[LT]/h2[GT]
    [BO] if results [BC]
        [LT]table class="results-table"[GT]
            [LT]thead[GT]
                [LT]tr[GT]
                    [LT]th[GT]Rank[LT]/th[GT]
                    [LT]th[GT]Team[LT]/th[GT]
                    [LT]th[GT]Submission[LT]/th[GT]
                    [LT]th[GT]Raw Score[LT]/th[GT]
                    [LT]th[GT]Z-Score[LT]/th[GT]
                [LT]/tr[GT]
            [LT]/thead[GT]
            [LT]tbody[GT]
            [BO] for res in results [BC]
                [LT]tr[GT]
                    [LT]td[GT][VO] loop.index [VC][LT]/td[GT]
                    [LT]td[GT][VO] res.team_name [VC][LT]/td[GT]
                    [LT]td[GT][VO] res.submission_title [VC][LT]/td[GT]
                    [LT]td[GT][VO] res.raw_score [VC][LT]/td[GT]
                    [LT]td[GT][VO] res.z_score [VC][LT]/td[GT]
                [LT]/tr[GT]
            [BO] endfor [BC]
            [LT]/tbody[GT]
        [LT]/table[GT]
    [BO] else [BC]
        [LT]p[GT]No calculated scores available yet.[LT]/p[GT]
    [BO] endif [BC]
[LT]/div[GT]
[BO] endblock [BC]""",

    # -------------------------------------------------------------
    # 4. ALGORITHMS: Z-Score Normalization
    # -------------------------------------------------------------
    "app/algorithms/normalization.py": """import math
from collections import defaultdict
from typing import List, Dict

def calculate_judge_z_scores(scores_list: List[Dict]) -> List[Dict]:
    \"\"\"
    Normalizes judge scores using Z-score calculation to eliminate judge bias:
    Z = (x - mean) / std_dev
    \"\"\"
    judge_scores = defaultdict(list)
    for score in scores_list:
        judge_scores[score['judge_id']].append(score['raw_score'])

    judge_stats = {}
    for judge_id, raw_scores in judge_scores.items():
        n = len(raw_scores)
        if n == 0:
            continue
        mean = sum(raw_scores) / n
        variance = sum((x - mean) ** 2 for x in raw_scores) / n if n > 1 else 0
        std_dev = math.sqrt(variance)
        judge_stats[judge_id] = {'mean': mean, 'std_dev': std_dev}

    normalized_results = []
    for score in scores_list:
        stats = judge_stats.get(score['judge_id'])
        if stats and stats['std_dev'] > 0:
            z_score = (score['raw_score'] - stats['mean']) / stats['std_dev']
        else:
            z_score = 0.0
        
        normalized_results.append({
            'submission_id': score['submission_id'],
            'raw_score': score['raw_score'],
            'z_score': round(z_score, 4)
        })

    return normalized_results
""",

    # -------------------------------------------------------------
    # 5. API ROUTERS
    # -------------------------------------------------------------
    "app/api/submissions.py": """from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Submission, Team, User
from app.auth import get_current_user

router = APIRouter(prefix="/api/submissions", tags=["submissions"])

@router.post("")
def save_submission(
    title: str = Form(...),
    description: str = Form(...),
    repo_url: str = Form(...),
    demo_url: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team_member = current_user.team_memberships[0] if current_user.team_memberships else None
    if not team_member:
        raise HTTPException(status_code=400, detail="User is not assigned to a team")

    submission = db.query(Submission).filter(Submission.team_id == team_member.team_id).first()
    if not submission:
        submission = Submission(
            team_id=team_member.team_id,
            title=title,
            description=description,
            repo_url=repo_url,
            demo_url=demo_url,
            is_draft=False
        )
        db.add(submission)
    else:
        submission.title = title
        submission.description = description
        submission.repo_url = repo_url
        submission.demo_url = demo_url
        submission.is_draft = False

    db.commit()
    return {"message": "Submission saved successfully"}
""",

    "app/api/judging.py": """from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Score, User, RoleEnum
from app.auth import get_current_user

router = APIRouter(prefix="/api/judging", tags=["judging"])

@router.post("/evaluate")
async def submit_evaluation(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [RoleEnum.JUDGE, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    form_data = await request.form()
    submission_id = int(form_data.get("submission_id"))
    feedback = form_data.get("feedback")

    for key, value in form_data.items():
        if key.startswith("score_"):
            criterion_id = int(key.split("_")[1])
            raw_score = float(value)

            existing_score = db.query(Score).filter(
                Score.submission_id == submission_id,
                Score.judge_id == current_user.id,
                Score.criterion_id == criterion_id
            ).first()

            if existing_score:
                existing_score.raw_score = raw_score
                existing_score.feedback = feedback
            else:
                db.add(Score(
                    submission_id=submission_id,
                    judge_id=current_user.id,
                    criterion_id=criterion_id,
                    raw_score=raw_score,
                    feedback=feedback
                ))

    db.commit()
    return {"message": "Evaluation recorded successfully"}
""",

    # -------------------------------------------------------------
    # 6. STATIC JAVASCRIPT
    # -------------------------------------------------------------
    "app/static/js/app.js": """// Client side dynamic interactions
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dogfood Platform Client JS Loaded.');
});
"""
}

# Write files safely to disk
for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean(content).strip())
    print(f"Generated: {filepath}")

print("\nSuccessfully constructed all remaining codebase deliverables!")