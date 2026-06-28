from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    department: Mapped["Department"] = relationship("Department", back_populates="members")
    team_members: Mapped[list["TeamMember"]] = relationship("TeamMember", back_populates="member")
    monthly_workloads: Mapped[list["MonthlyWorkload"]] = relationship(
        "MonthlyWorkload", back_populates="member"
    )
    forecast_snapshots: Mapped[list["ForecastSnapshot"]] = relationship(
        "ForecastSnapshot", back_populates="member"
    )
