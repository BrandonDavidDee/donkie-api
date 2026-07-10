# type: ignore

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import backref, declarative_base, relationship

Base = declarative_base()
metadata = Base.metadata


class AuthUser(Base):
    __tablename__ = "auth_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    notes = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    scopes = Column(String)
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(Integer, ForeignKey("auth_user.id"))

    # Relationships
    created_buckets = relationship("SourceBucket", back_populates="creator")
    created_videos = relationship("SourceVimeo", back_populates="creator")

