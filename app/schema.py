# type: ignore

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
metadata = Base.metadata


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    created_by = Column(Text, nullable=False)  # opaque user_id, not a FK
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True)  # soft delete/close

    tags = relationship("ConversationTag", back_populates="conversation", cascade="all, delete-orphan")
    participants = relationship("Participant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_conversations_tenant", "tenant_id"),
    )


class ConversationTag(Base):
    """
    Generic context layer — replaces a rigid context_type/context_id column.
    tag_key/tag_value examples: ("event", "4291"), ("date", "2026-08-14"), ("assignment", "882").
    Composite PK prevents duplicate tags on the same conversation.
    """
    __tablename__ = "conversation_tags"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    tag_key = Column(Text, primary_key=True, nullable=False)
    tag_value = Column(Text, primary_key=True, nullable=False)
    tenant_id = Column(Text, nullable=False)  # denormalized for fast scoped lookups
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    conversation = relationship("Conversation", back_populates="tags")

    __table_args__ = (
        # The critical index: "all conversations with tag X for tenant Y"
        Index("idx_tags_lookup", "tenant_id", "tag_key", "tag_value"),
    )


class Participant(Base):
    """
    Membership/roster data — distinct from JWT scope.
    Used for read receipts, member lists, and notification targeting.
    """
    __tablename__ = "participants"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    user_id = Column(Text, primary_key=True, nullable=False)  # opaque, defined by host app
    tenant_id = Column(Text, nullable=False)
    last_read_at = Column(DateTime(timezone=True), nullable=True)  # null = never read
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    conversation = relationship("Conversation", back_populates="participants")

    __table_args__ = (
        Index("idx_participants_user", "tenant_id", "user_id"),
    )


class Message(Base):
    """
    sender_display_name is a snapshot at send-time so API responses are
    self-contained -- no second lookup needed by any consumer.
    Body stores mentions as @[user_id] tokens; display rendering is a
    frontend concern.

    Threading support:
    - parent_message_id points to the parent message when this is a reply.
    - reply_count caches how many direct replies a message has.
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_id = Column(Text, nullable=False)
    sender_id = Column(Text, nullable=False)           # opaque user_id
    sender_display_name = Column(Text, nullable=False) # snapshot at send-time
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    edited_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # soft delete, keeps thread intact
    reply_count = Column(Integer, nullable=False, default=0, server_default="0")

    conversation = relationship("Conversation", back_populates="messages")
    mentions = relationship("MessageMention", back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        # Hot path: messages for conversation X, paginated by time
        Index("idx_messages_conversation", "conversation_id", "created_at"),
    )


class MessageMention(Base):
    """
    Structured record of @mentions — avoids re-parsing body text to answer
    "who was mentioned" or "what am I mentioned in."
    Composite PK on (message_id, user_id) prevents duplicate mentions per message.
    """
    __tablename__ = "message_mentions"

    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    user_id = Column(Text, primary_key=True, nullable=False)  # same id space as participants.user_id
    tenant_id = Column(Text, nullable=False)
    mentioned_display_name = Column(Text, nullable=False)  # snapshot at send-time
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    message = relationship("Message", back_populates="mentions")

    __table_args__ = (
        Index("idx_mentions_user", "tenant_id", "user_id"),
    )
