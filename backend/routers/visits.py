"""One screening visit: inputs, X-ray, analysis, result, review."""
import json
import logging
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image, ImageChops, ImageStat
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .. import storage
from ..analysis import (
    CHAIR_STAND_SLOW_SEC,
    SARCF_POSITIVE,
    grip_cutoff,
    run_model,
    run_tabular_models,
    sarcopenia_stage,
)
from ..db import get_db
from ..models import (
    AnalysisResult,
    DoctorReview,
    GripMeasurement,
    Hand,
    Patient,
    Role,
    Tier,
    User,
    Visit,
    VisitStatus,
    XrayStudy,
)
from ..schemas import (
    ClinicalIn,
    GripIn,
    GripOut,
    HistoryItem,
    ResultOut,
    ReviewIn,
    ReviewOut,
    VisitOut,
    XrayOut,
)
from ..security import SCREENERS, STAFF, Audit, require_roles

router = APIRouter(prefix="/api/v1", tags=["screening"])
log = logging.getLogger("sarcoscan")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MIN_SIDE_PX = 256
# Measured on a 64 x 64 copy, on a 0 to 255 scale. A knee X-ray scores about 0 and 65; a blank image 0 and 0.
MAX_COLOUR = 8  # average difference between colour channels
MIN_CONTRAST = 15  # standard deviation of brightness
NO_CACHE = {"Cache-Control": "private, no-store"}


def _get(db: Session, model, record_id: uuid.UUID, what: str):
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No such {what}")
    return record


def _latest(db: Session, model, time_column, **where):
    return db.scalars(select(model).filter_by(**where).order_by(time_column.desc())).first()


def _user_name(db: Session, user_id: uuid.UUID) -> str | None:
    user = db.get(User, user_id)
    return user.name if user else None


def _grip_summary(db: Session, visit: Visit, patient: Patient) -> GripOut:
    best = {
        row.hand: row.value_kg
        for row in db.scalars(select(GripMeasurement).filter_by(visit_id=visit.id, is_best=True))
    }
    best_kg = max(best.values(), default=None)
    cutoff = grip_cutoff(patient.sex.value)
    return GripOut(
        best_left=best.get(Hand.left),
        best_right=best.get(Hand.right),
        best_kg=best_kg,
        cutoff_kg=cutoff,
        low=None if best_kg is None else best_kg < cutoff,
    )


def _result(db: Session, visit: Visit, patient: Patient) -> ResultOut:
    analysis = _latest(db, AnalysisResult, AnalysisResult.created_at, visit_id=visit.id)
    xray = _latest(db, XrayStudy, XrayStudy.uploaded_at, visit_id=visit.id)
    review = _latest(db, DoctorReview, DoctorReview.reviewed_at, visit_id=visit.id)
    fields = ("osteoporosis_prob", "osteoporosis_tier", "thigh_soft_to_bone", "calf_soft_to_bone")
    fields += ("soft_to_plateau", "soft_area_ratio", "kl_grade", "inference_ms", "sarcopenia_stage", "model_version")
    fields += ("low_muscle", "low_muscle_prob", "bone_loss", "bone_loss_prob")
    return ResultOut(
        visit_id=visit.id,
        patient_id=patient.id,
        visit_date=visit.visit_date,
        status=visit.status,
        performed_by_name=_user_name(db, visit.performed_by),
        reviewed_by_name=_user_name(db, review.doctor_id) if review else None,
        bmi=visit.bmi,
        grip=_grip_summary(db, visit, patient),
        sarcf_score=visit.sarcf_score,
        sarcf_positive=None if visit.sarcf_score is None else visit.sarcf_score >= SARCF_POSITIVE,
        chair_stand_5_sec=visit.chair_stand_5_sec,
        chair_stand_slow=(
            None if visit.chair_stand_5_sec is None else visit.chair_stand_5_sec >= CHAIR_STAND_SLOW_SEC
        ),
        calf_circumference_cm=visit.calf_circumference_cm,
        waist_cm=visit.waist_cm,
        arm_circ_cm=visit.arm_circ_cm,
        history=json.loads(visit.history_json) if visit.history_json else None,
        xray_id=xray.id if xray else None,
        has_overlay=bool(analysis and analysis.overlay_storage_key),
        model_connected=bool(analysis and analysis.model_version != "not-connected"),
        review=ReviewOut.model_validate(review) if review else None,
        **{name: getattr(analysis, name, None) for name in fields},
    )


def _stored_name(file_path: str | None) -> str | None:
    """The model returns a path to a file it wrote in the uploads folder. Keep only a name that exists there."""
    if not file_path:
        return None
    name = Path(file_path).name
    return name if storage.path(name).is_file() else None


def _quality_problem(image: Image.Image) -> str | None:
    # ponytail: size, shape, colour and contrast only. It stops photos, logos and blank images.
    # A greyscale photo, or an X-ray of another body part, still passes; that needs a trained check.
    width, height = image.size
    if min(width, height) < MIN_SIDE_PX:
        return f"The image is too small ({width} x {height} pixels). At least {MIN_SIDE_PX} on each side is needed."
    if not 0.5 <= height / width <= 3:
        return "The image is too wide or too tall to be a single knee X-ray."
    small = image.convert("RGB").resize((64, 64))
    red, green, blue = small.split()
    colour = max(
        ImageStat.Stat(ImageChops.difference(red, green)).mean[0],
        ImageStat.Stat(ImageChops.difference(green, blue)).mean[0],
    )
    if colour > MAX_COLOUR:
        return "This looks like a colour picture, not an X-ray. X-rays are black and white."
    if ImageStat.Stat(small.convert("L")).stddev[0] < MIN_CONTRAST:
        return "The image is almost blank. Check the exposure and upload it again."
    return None


@router.post("/patients/{patient_id}/visits", response_model=VisitOut, status_code=status.HTTP_201_CREATED)
def start_visit(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*SCREENERS)),
    audit: Audit = Depends(),
):
    patient = _get(db, Patient, patient_id, "patient")
    bmi = round(patient.weight_kg / (patient.height_cm / 100) ** 2, 1)
    visit = Visit(patient_id=patient.id, performed_by=user.id, bmi=bmi)
    db.add(visit)
    db.flush()
    audit.log(user, "CREATE", "visit", visit.id)
    db.commit()
    return visit


@router.get("/visits", response_model=list[ResultOut])
def list_visits(
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF)),
    audit: Audit = Depends(),
):
    visits = db.scalars(select(Visit).order_by(Visit.visit_date.desc()).limit(limit)).all()
    audit.log(user, "VIEW", "visit_list")
    db.commit()
    # ponytail: several queries per visit. Fine for a clinic's recent list; join them if this page gets slow.
    return [_result(db, visit, db.get(Patient, visit.patient_id)) for visit in visits]


@router.get("/visits/{visit_id}", response_model=VisitOut)
def get_visit(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF)),
    audit: Audit = Depends(),
):
    visit = _get(db, Visit, visit_id, "visit")
    audit.log(user, "VIEW", "visit", visit.id)
    db.commit()
    return visit


@router.post("/visits/{visit_id}/clinical-inputs", response_model=VisitOut)
def save_clinical_inputs(
    visit_id: uuid.UUID,
    body: ClinicalIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*SCREENERS)),
    audit: Audit = Depends(),
):
    visit = _get(db, Visit, visit_id, "visit")
    visit.sarcf_score = body.sarcf_score
    visit.chair_stand_5_sec = body.chair_stand_5_sec
    visit.calf_circumference_cm = body.calf_circumference_cm
    visit.waist_cm = body.waist_cm
    visit.arm_circ_cm = body.arm_circ_cm
    visit.history_json = json.dumps(body.history) if body.history is not None else None
    audit.log(user, "UPDATE", "visit", visit.id)
    db.commit()
    return visit


@router.post("/visits/{visit_id}/grip", response_model=GripOut)
def save_grip(
    visit_id: uuid.UUID,
    body: GripIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*SCREENERS)),
    audit: Audit = Depends(),
):
    visit = _get(db, Visit, visit_id, "visit")
    if not body.left and not body.right:
        raise HTTPException(422, "Enter at least one grip reading")
    # Sending the readings again replaces the earlier ones for this visit.
    db.execute(delete(GripMeasurement).where(GripMeasurement.visit_id == visit.id))
    for hand, values in ((Hand.left, body.left), (Hand.right, body.right)):
        best_index = values.index(max(values)) if values else -1
        for index, value in enumerate(values):
            db.add(
                GripMeasurement(
                    visit_id=visit.id, hand=hand, trial_no=index + 1, value_kg=value, is_best=index == best_index
                )
            )
    audit.log(user, "UPDATE", "visit", visit.id)
    db.commit()
    return _grip_summary(db, visit, _get(db, Patient, visit.patient_id, "patient"))


@router.post("/visits/{visit_id}/xray", response_model=XrayOut, status_code=status.HTTP_201_CREATED)
def upload_xray(
    visit_id: uuid.UUID,
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*SCREENERS)),
    audit: Audit = Depends(),
):
    visit = _get(db, Visit, visit_id, "visit")
    source = file.file
    source.seek(0, 2)
    if source.tell() > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "The file is larger than 50 MB")
    source.seek(0)

    # The type is decided from the file's first bytes. The name and extension the client sent are ignored.
    head = source.read(132)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        suffix = ".png"
    elif head.startswith(b"\xff\xd8\xff"):
        suffix = ".jpg"
    elif head[128:132] == b"DICM":
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "DICOM is not supported yet. Export the image as PNG or JPG."
        )
    else:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a PNG or JPG image")
    try:
        source.seek(0)
        with Image.open(source) as image:
            image.verify()
        source.seek(0)
        with Image.open(source) as image:
            problem = _quality_problem(image)
    except Exception:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "This file is not a readable image") from None

    source.seek(0)
    xray = XrayStudy(
        visit_id=visit.id, storage_key=storage.save(source, suffix), qc_passed=problem is None, qc_reason=problem
    )
    db.add(xray)
    db.flush()
    audit.log(user, "CREATE", "xray", xray.id)
    db.commit()
    return xray


@router.post("/visits/{visit_id}/analyze", response_model=ResultOut)
def analyze(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*SCREENERS)),
    audit: Audit = Depends(),
):
    visit = _get(db, Visit, visit_id, "visit")
    patient = _get(db, Patient, visit.patient_id, "patient")
    xray = _latest(db, XrayStudy, XrayStudy.uploaded_at, visit_id=visit.id, qc_passed=True)
    if xray is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Upload an X-ray that passes the quality check first")

    grip = _grip_summary(db, visit, patient)
    started = time.perf_counter()
    try:
        output = run_model(storage.path(xray.storage_key), patient.age, patient.sex.value, visit.bmi)
        tabular = run_tabular_models(
            patient.age, patient.sex.value, patient.height_cm, patient.weight_kg, visit.bmi,
            visit.waist_cm, visit.arm_circ_cm, grip.best_left, grip.best_right,
            json.loads(visit.history_json) if visit.history_json else None,
        )
        tier = Tier(output["osteoporosis_tier"]) if output.get("osteoporosis_tier") else None
        overlay = _stored_name(output.get("overlay_path"))
        gradcam = _stored_name(output.get("gradcam_path"))
    except Exception:
        log.exception("Analysis failed for xray %s", xray.id)  # ids only, no patient details
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "This image could not be analysed. Try again or upload another image.",
        ) from None
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    # Evidence of low muscle: a measurement from the X-ray when one exists, else the body-measurement model.
    low_muscle = output.get("low_muscle")
    if low_muscle is None:
        low_muscle = tabular.get("low_muscle")
    result = AnalysisResult(
        visit_id=visit.id,
        xray_id=xray.id,
        model_version=output.get("model_version", "not-connected"),
        overlay_storage_key=overlay,
        gradcam_storage_key=gradcam,
        thigh_soft_to_bone=output.get("thigh_soft_to_bone"),
        calf_soft_to_bone=output.get("calf_soft_to_bone"),
        soft_to_plateau=output.get("soft_to_plateau"),
        soft_area_ratio=output.get("soft_area_ratio"),
        kl_grade=output.get("kl_grade"),
        sarcopenia_stage=sarcopenia_stage(
            patient.sex.value, grip.best_kg, visit.chair_stand_5_sec, low_muscle
        ),
        low_muscle=low_muscle,
        low_muscle_prob=tabular.get("low_muscle_prob"),
        bone_loss=tabular.get("bone_loss"),
        bone_loss_prob=tabular.get("bone_loss_prob"),
        osteoporosis_prob=output.get("osteoporosis_prob"),
        osteoporosis_tier=tier,
        inference_ms=elapsed_ms,
    )
    db.add(result)
    visit.status = VisitStatus.analyzed
    db.flush()
    audit.log(user, "CREATE", "analysis", result.id)
    db.commit()
    return _result(db, visit, patient)


@router.get("/visits/{visit_id}/result", response_model=ResultOut)
def get_result(
    visit_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF)),
    audit: Audit = Depends(),
):
    visit = _get(db, Visit, visit_id, "visit")
    audit.log(user, "VIEW", "visit", visit.id)
    db.commit()
    return _result(db, visit, _get(db, Patient, visit.patient_id, "patient"))


@router.post("/visits/{visit_id}/review", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def review(
    visit_id: uuid.UUID,
    body: ReviewIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.doctor)),
    audit: Audit = Depends(),
):
    visit = _get(db, Visit, visit_id, "visit")
    analysis = _latest(db, AnalysisResult, AnalysisResult.created_at, visit_id=visit.id)
    if analysis is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "This visit has no analysis to review yet")
    final_stage = analysis.sarcopenia_stage if body.agrees_with_ai else body.final_stage
    if final_stage is None:
        raise HTTPException(422, "Choose the final stage")
    # A new row each time: the system's result and every doctor decision are all kept.
    doctor_review = DoctorReview(
        visit_id=visit.id,
        doctor_id=user.id,
        final_stage=final_stage,
        agrees_with_ai=body.agrees_with_ai,
        notes=body.notes,
    )
    db.add(doctor_review)
    visit.status = VisitStatus.reviewed
    audit.log(user, "UPDATE", "visit", visit.id)
    db.commit()
    return doctor_review


@router.get("/patients/{patient_id}/history", response_model=list[HistoryItem])
def history(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF)),
    audit: Audit = Depends(),
):
    patient = _get(db, Patient, patient_id, "patient")
    items = []
    # ponytail: a few queries per visit. Fine for one patient's visits; join them if a page ever gets slow.
    for visit in db.scalars(select(Visit).filter_by(patient_id=patient.id).order_by(Visit.visit_date.desc())):
        analysis = _latest(db, AnalysisResult, AnalysisResult.created_at, visit_id=visit.id)
        doctor_review = _latest(db, DoctorReview, DoctorReview.reviewed_at, visit_id=visit.id)
        items.append(
            HistoryItem(
                visit_id=visit.id,
                visit_date=visit.visit_date,
                status=visit.status,
                best_grip_kg=_grip_summary(db, visit, patient).best_kg,
                sarcopenia_stage=analysis.sarcopenia_stage if analysis else None,
                osteoporosis_tier=analysis.osteoporosis_tier if analysis else None,
                final_stage=doctor_review.final_stage if doctor_review else None,
            )
        )
    audit.log(user, "VIEW", "patient", patient.id)
    db.commit()
    return items


@router.get("/xrays/{xray_id}/image")
def xray_image(
    xray_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF)),
    audit: Audit = Depends(),
):
    xray = _get(db, XrayStudy, xray_id, "X-ray")
    audit.log(user, "VIEW", "xray", xray.id)
    db.commit()
    return FileResponse(storage.path(xray.storage_key), headers=NO_CACHE)


@router.get("/xrays/{xray_id}/overlay")
def xray_overlay(
    xray_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF)),
    audit: Audit = Depends(),
):
    xray = _get(db, XrayStudy, xray_id, "X-ray")
    analysis = _latest(db, AnalysisResult, AnalysisResult.created_at, xray_id=xray.id)
    if analysis is None or not analysis.overlay_storage_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No overlay for this X-ray")
    audit.log(user, "VIEW", "xray", xray.id)
    db.commit()
    return FileResponse(storage.path(analysis.overlay_storage_key), headers=NO_CACHE)
