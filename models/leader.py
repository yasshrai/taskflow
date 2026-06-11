from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from models.base import Base


class LeaderModel(Base):
    __tablename__ = "leaders"

    leader_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
