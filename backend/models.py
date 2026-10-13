"""Database tables. Columns follow docs/DATABASE.md."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    DDL,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from .crypto import EncryptedStr
from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"
    technician = "technician"


class Sex(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class VisitStatus(str, enum.Enum):
    draft = "draft"
    in_progress = "in_progress"
    analyzed = "analyzed"
    reviewed = "reviewed"
    reported = "reported"


class Hand(str, enum.Enum):
    left = "left"
    right = "right"


class Stage(str, enum.Enum):
    none = "none"
    possible = "possible"
    probable = "probable"
    severe = "severe"


class Tier(str, enum.Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    mrn: Mapped[str] = mapped_column(String(40), unique=True)
    abha_id: Mapped[str | None] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(EncryptedStr(512))
    age: Mapped[int] = mapped_column(Integer)
    sex: Mapped[Sex] = mapped_column(Enum(Sex, name="sex"))
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    phone: Mapped[str | None] = mapped_column(EncryptedStr(255))
    phone_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    consent_given: Mapped[bool] = mapped_column(Boolean)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Visit(Base):
    __tablename__ = "visits"
    __table_args__ = (Index("ix_visits_patient_date", "patient_id", "visit_date"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"))
    performed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    visit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    status: Mapped[VisitStatus] = mapped_column(Enum(VisitStatus, name="visit_status"), default=VisitStatus.in_progress)
    bmi: Mapped[float] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    # The spec's clinical_inputs table is one-to-one with a visit, so its columns live here.
    sarcf_score: Mapped[int | None] = mapped_column(Integer)
    chair_stand_5_sec: Mapped[float | None] = mapped_column(Float)
    calf_circumference_cm: Mapped[float | None] = mapped_column(Float)
    # Optional inputs of the muscle-mass model (ml/tabular.py).
    waist_cm: Mapped[float | None] = mapped_column(Float)
    arm_circ_cm: Mapped[float | None] = mapped_column(Float)
    # Medical-history answers as JSON text ({question: true or false}); empty when history was not asked.
    history_json: Mapped[str | None] = mapped_column(Text)


class GripMeasurement(Base):
    __tablename__ = "grip_measurements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id"), index=True)
    hand: Mapped[Hand] = mapped_column(Enum(Hand, name="hand"))
    trial_no: Mapped[int] = mapped_column(Integer)
    value_kg: Mapped[float] = mapped_column(Float)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(16), default="manual")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class XrayStudy(Base):
    __tablename__ = "xray_studies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id"), index=True)
    storage_key: Mapped[str] = mapped_column(String(255))
    laterality: Mapped[str] = mapped_column(String(8), default="unknown")
    qc_passed: Mapped[bool] = mapped_column(Boolean)
    qc_reason: Mapped[str | None] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id"), index=True)
    xray_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("xray_studies.id"))
    model_version: Mapped[str] = mapped_column(String(40))
    mask_storage_key: Mapped[str | None] = mapped_column(String(255))
    overlay_storage_key: Mapped[str | None] = mapped_column(String(255))
    gradcam_storage_key: Mapped[str | None] = mapped_column(String(255))
    thigh_soft_to_bone: Mapped[float | None] = mapped_column(Float)
    calf_soft_to_bone: Mapped[float | None] = mapped_column(Float)
    soft_to_plateau: Mapped[float | None] = mapped_column(Float)
    soft_area_ratio: Mapped[float | None] = mapped_column(Float)
    kl_grade: Mapped[int | None] = mapped_column(Integer)
    sarcopenia_prob: Mapped[float | None] = mapped_column(Float)
    sarcopenia_stage: Mapped[Stage] = mapped_column(Enum(Stage, name="sarcopenia_stage"))
    # Empty until a trained model is connected. The API never fills these with made-up values.
    osteoporosis_prob: Mapped[float | None] = mapped_column(Float)
    osteoporosis_tier: Mapped[Tier | None] = mapped_column(Enum(Tier, name="osteoporosis_tier"))
    # From the two models in ml/tabular.py. Empty when they are not installed.
    low_muscle: Mapped[bool | None] = mapped_column(Boolean)
    low_muscle_prob: Mapped[float | None] = mapped_column(Float)
    bone_loss: Mapped[bool | None] = mapped_column(Boolean)
    bone_loss_prob: Mapped[float | None] = mapped_column(Float)
    inference_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class DoctorReview(Base):
    __tablename__ = "doctor_reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id"), index=True)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    final_stage: Mapped[Stage] = mapped_column(Enum(Stage, name="final_stage"))
    agrees_with_ai: Mapped[bool] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_user_time", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(16))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    ip_address: Mapped[str] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


# audit_logs is append-only on PostgreSQL: the database itself rejects edits and deletes.
for _statement in (
    """
    CREATE OR REPLACE FUNCTION audit_logs_no_change() RETURNS trigger AS $$
    BEGIN
      RAISE EXCEPTION 'audit_logs is append-only';
    END;
    $$ LANGUAGE plpgsql
    """,
    """
    CREATE TRIGGER audit_logs_no_update_delete
      BEFORE UPDATE OR DELETE ON audit_logs
      FOR EACH ROW EXECUTE FUNCTION audit_logs_no_change()
    """,
    """
    CREATE TRIGGER audit_logs_no_truncate
      BEFORE TRUNCATE ON audit_logs
      FOR EACH STATEMENT EXECUTE FUNCTION audit_logs_no_change()
    """,
):
    event.listen(AuditLog.__table__, "after_create", DDL(_statement).execute_if(dialect="postgresql"))
