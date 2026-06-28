from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MonthlyWorkload(Base):
    __tablename__ = "monthly_workloads"
    __table_args__ = (
        UniqueConstraint("member_id", "project_id", "year", "month", name="uq_monthly_workload"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_mm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    simulated_mm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    actual_mm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    member: Mapped["Member"] = relationship("Member", back_populates="monthly_workloads")
    project: Mapped["Project"] = relationship("Project", back_populates="monthly_workloads")
