"""Request and response shapes. FastAPI shows them at /docs."""
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .analysis import HISTORY_QUESTIONS
from .models import Role, Sex, Stage, Tier, VisitStatus


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    role: Role


class PatientIn(BaseModel):
    mrn: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=18, le=120)  # adults only
    sex: Sex
    height_cm: float = Field(ge=120, le=220)
    weight_kg: float = Field(ge=25, le=250)
    phone: str | None = Field(default=None, min_length=6, max_length=20)
    abha_id: str | None = Field(default=None, max_length=40)
    consent_given: bool


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mrn: str
    name: str
    age: int
    sex: Sex
    height_cm: float
    weight_kg: float
    phone: str | None
    abha_id: str | None
    consent_given: bool
    consent_at: datetime
    created_at: datetime


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    visit_date: datetime
    status: VisitStatus
    bmi: float
    sarcf_score: int | None
    chair_stand_5_sec: float | None
    calf_circumference_cm: float | None
    waist_cm: float | None
    arm_circ_cm: float | None


class ClinicalIn(BaseModel):
    sarcf_score: int | None = Field(default=None, ge=0, le=10)
    chair_stand_5_sec: float | None = Field(default=None, gt=0, lt=300)
    calf_circumference_cm: float | None = Field(default=None, gt=10, lt=100)
    waist_cm: float | None = Field(default=None, gt=40, lt=200)
    arm_circ_cm: float | None = Field(default=None, gt=10, lt=70)
    # Medical history: {question: yes or no}. Leave out when the patient was not asked.
    history: dict[str, bool] | None = None

    @field_validator("history")
    @classmethod
    def known_questions(cls, value):
        unknown = set(value or {}) - set(HISTORY_QUESTIONS)
        if unknown:
            raise ValueError(f"Unknown history questions: {sorted(unknown)}")
        return value


Kilograms = Annotated[float, Field(gt=0, lt=100)]


class GripIn(BaseModel):
    left: list[Kilograms] = Field(default=[], max_length=3)
    right: list[Kilograms] = Field(default=[], max_length=3)


class GripOut(BaseModel):
    best_left: float | None
    best_right: float | None
    best_kg: float | None
    cutoff_kg: float
    low: bool | None


class XrayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    visit_id: uuid.UUID
    qc_passed: bool
    qc_reason: str | None
    uploaded_at: datetime


class ReviewIn(BaseModel):
    agrees_with_ai: bool
    final_stage: Stage | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doctor_id: uuid.UUID
    final_stage: Stage
    agrees_with_ai: bool
    notes: str | None
    reviewed_at: datetime


class ResultOut(BaseModel):
    visit_id: uuid.UUID
    patient_id: uuid.UUID
    visit_date: datetime
    status: VisitStatus
    performed_by_name: str | None
    reviewed_by_name: str | None
    bmi: float
    grip: GripOut
    sarcf_score: int | None
    sarcf_positive: bool | None
    chair_stand_5_sec: float | None
    chair_stand_slow: bool | None
    calf_circumference_cm: float | None
    waist_cm: float | None
    arm_circ_cm: float | None
    history: dict[str, bool] | None
    # From the two body-measurement models; empty when they are not installed.
    low_muscle: bool | None
    low_muscle_prob: float | None
    bone_loss: bool | None
    bone_loss_prob: float | None
    xray_id: uuid.UUID | None
    has_overlay: bool
    # False while ml/predict.py is not in the repo: the image-based fields below are then empty.
    model_connected: bool
    model_version: str | None
    sarcopenia_stage: Stage | None
    osteoporosis_prob: float | None
    osteoporosis_tier: Tier | None
    thigh_soft_to_bone: float | None
    calf_soft_to_bone: float | None
    soft_to_plateau: float | None
    soft_area_ratio: float | None
    kl_grade: int | None
    inference_ms: int | None
    review: ReviewOut | None


class HistoryItem(BaseModel):
    visit_id: uuid.UUID
    visit_date: datetime
    status: VisitStatus
    best_grip_kg: float | None
    sarcopenia_stage: Stage | None
    osteoporosis_tier: Tier | None
    final_stage: Stage | None


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: uuid.UUID
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    ip_address: str
    created_at: datetime
