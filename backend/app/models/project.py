from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    matter_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("matters.id", ondelete="SET NULL"), nullable=True
    )
    wbs_tmp: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    matter: Mapped["Matter | None"] = relationship("Matter", back_populates="projects")
    monthly_workloads: Mapped[list["MonthlyWorkload"]] = relationship(
        "MonthlyWorkload", back_populates="project"
    )
    forecast_snapshots: Mapped[list["ForecastSnapshot"]] = relationship(
        "ForecastSnapshot", back_populates="project"
    )
