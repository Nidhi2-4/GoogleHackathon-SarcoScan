import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..crypto import phone_hash
from ..db import get_db
from ..models import Patient, User, now
from ..schemas import PatientIn, PatientOut
from ..security import STAFF, Audit, require_roles

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def register_patient(
    body: PatientIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF)),
    audit: Audit = Depends(),
):
    if not body.consent_given:
        raise HTTPException(422, "The patient's consent is required")
    if db.scalar(select(Patient.id).where(Patient.mrn == body.mrn)):
        raise HTTPException(status.HTTP_409_CONFLICT, "A patient with this MRN already exists")
    patient = Patient(
        **body.model_dump(),
        phone_hash=phone_hash(body.phone) if body.phone else None,
        consent_at=now(),
        created_by=user.id,
    )
    db.add(patient)
    db.flush()
    audit.log(user, "CREATE", "patient", patient.id)
    db.commit()
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(
    q: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF)),
    audit: Audit = Depends(),
):
    patients = db.scalars(select(Patient).order_by(Patient.created_at.desc())).all()
    needle = q.strip().lower()
    if needle:
        # ponytail: names are encrypted, so they are matched here after decryption, row by row.
        # Fine for a few thousand patients. Add a search index if the table grows past that.
        wanted = phone_hash(needle)
        patients = [
            p for p in patients if needle in p.name.lower() or needle in p.mrn.lower() or p.phone_hash == wanted
        ]
    audit.log(user, "VIEW", "patient_list")
    db.commit()
    return patients[:50]


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*STAFF)),
    audit: Audit = Depends(),
):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such patient")
    audit.log(user, "VIEW", "patient", patient.id)
    db.commit()
    return patient
