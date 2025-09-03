# app/models.py

import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    Boolean,
    Index,
    Sequence,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Replace 'postgres://' with 'postgresql://' if necessary
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # For platforms like Heroku, SSL is often required
    engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
else:
    # Local development settings (ensure to set these environment variables)
    DB_USER = os.environ.get("DB_USER", "your_db_user")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "your_db_password")
    DB_NAME = os.environ.get("DB_NAME", "your_db_name")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")

    DATABASE_URL = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(DATABASE_URL)

# Session Configuration
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base Model
Base = declarative_base()


class Thread(Base):
    """
    Represents a unique conversation thread between a user and the assistant.
    """

    __tablename__ = "threads"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(
        String(50), index=True, nullable=False
    )  # e.g., WhatsApp number, Instagram ID
    sender_platform = Column(
        String(20), nullable=False, default="whatsapp"
    )  # whatsapp, instagram, web
    sender_display_name = Column(String(100), nullable=True)
    thread_id = Column(
        String(100), unique=True, nullable=False
    )  # Provided by Assistant API
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_conversation_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    follow_up_need_sent = Column(
        Boolean, default=False
    )  # Track if follow-up has been sent
    follow_up_sent_at = Column(DateTime(timezone=True), nullable=True)
    is_paused = Column(Boolean, default=False)  # If True, assistant replies are paused

    # Referral metadata for tracking conversation origins
    referral_source_type = Column(String(50), nullable=True)  # e.g., "ad", "facebook", "instagram"
    referral_source_id = Column(String(100), nullable=True)   # e.g., ad_id, post_id
    referral_source_url = Column(Text, nullable=True)         # URL that led to conversation
    referral_header = Column(String(255), nullable=True)      # Referral header text
    referral_body = Column(Text, nullable=True)               # Referral body text
    ctwa_clid = Column(String(100), nullable=True)            # Click to WhatsApp Click ID
    button_text = Column(String(100), nullable=True)          # Button text if clicked
    button_payload = Column(String(255), nullable=True)       # Button payload if clicked

    # Relationships
    conversations = relationship(
        "Conversation", back_populates="thread", cascade="all, delete-orphan"
    )
    messages = relationship(
        "Message", back_populates="thread", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Thread(id={self.id}, sender='{self.sender}', thread_id='{self.thread_id}')>"


class Conversation(Base):
    """
    Stores individual messages exchanged within a thread.
    """

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String(50), index=True, nullable=False)  # e.g., WhatsApp number
    sender_platform = Column(
        String(20), nullable=False, default="whatsapp"
    )  # whatsapp, instagram, web
    message = Column(Text, nullable=False)  # User's message
    response = Column(Text, nullable=False)  # Assistant's response
    thread_id = Column(
        Integer, ForeignKey("threads.id", ondelete="CASCADE"), nullable=False
    )
    message_sid = Column(
        String(100), unique=True, nullable=True
    )  # For message deduplication
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    thread = relationship("Thread", back_populates="conversations")

    def __repr__(self):
        return f"<Conversation(id={self.id}, sender='{self.sender}', thread_id={self.thread_id})>"


class Message(Base):
    """Individual message within a thread (user or assistant)."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    message_sid = Column(String(100), unique=True, nullable=True)

    # Relationships
    thread = relationship("Thread", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', thread_id={self.thread_id})>"


class CustomerInfo(Base):
    """
    Stores collected basic customer information from all interactions.
    """

    __tablename__ = "customer_info"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)  # Customer's name
    email = Column(String(100), nullable=True)  # Email can be collected later
    telefono = Column(String(50), nullable=False, unique=True)  # Phone number or visitor ID
    fuente = Column(String(50), nullable=False, default="WhatsApp")  # Lead source
    ciudad_interes = Column(String(100), nullable=True)  # City of interest
    tipo_propiedad = Column(String(50), nullable=True)  # Property type
    presupuesto_min = Column(Integer, nullable=True)  # Min budget
    presupuesto_max = Column(Integer, nullable=True)  # Max budget
    interes_compra = Column(String(50), nullable=True)  # Purchase interest level
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<CustomerInfo(id={self.id}, nombre='{self.nombre}', telefono='{self.telefono}')>"


class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    leads = relationship("QualifiedLead", back_populates="agent")


class LeadStatusHistory(Base):
    __tablename__ = "lead_status_history"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("qualified_leads.id"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    changed_by = Column(Integer, ForeignKey("agents.id"), nullable=True)


class BlockedNumber(Base):
    """Store phone numbers that should not receive messages."""

    __tablename__ = "blocked_numbers"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class QualifiedLead(Base):
    """
    Stores information about customers who have shown interest in buying or visiting properties.
    """

    __tablename__ = "qualified_leads"

    id = Column(Integer, primary_key=True, index=True)
    customer_info_id = Column(Integer, ForeignKey("customer_info.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    telefono = Column(String(50), nullable=False, unique=True)
    fuente = Column(String(50), nullable=False, default="WhatsApp")

    # Property preferences
    ciudad_interes = Column(String(100), nullable=True)
    proyecto_interes = Column(String(100), nullable=True)  # Specific project name
    tipo_propiedad = Column(String(50), nullable=True)  # Apartment, house, etc.
    tamano_minimo = Column(Integer, nullable=True)  # Minimum square meters
    habitaciones = Column(Integer, nullable=True)  # Number of bedrooms
    banos = Column(Integer, nullable=True)  # Number of bathrooms
    presupuesto_min = Column(Integer, nullable=True)  # Min budget
    presupuesto_max = Column(Integer, nullable=True)  # Max budget

    # Qualification details
    motivo_interes = Column(
        String(100), nullable=True
    )  # Investment, primary residence, etc.
    urgencia_compra = Column(String(50), nullable=True)  # Timeframe for purchase
    interes_compra = Column(String(50), nullable=True)  # Purchase interest level
    metodo_contacto_preferido = Column(
        String(50), nullable=True
    )  # Call, WhatsApp, email
    horario_contacto_preferido = Column(
        String(100), nullable=True
    )  # Morning, afternoon, etc.

    # Status flags
    desea_visita = Column(Boolean, default=False)  # Wants property viewing
    desea_llamada = Column(Boolean, default=False)  # Wants sales call
    desea_informacion = Column(Boolean, default=False)  # Wants more information

    # Conversation analysis
    conversation_summary = Column(Text, nullable=True)  # Summary of the conversation
    deducted_interest = Column(Text, nullable=True)  # Interest score and justification

    # New fields
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    notes = Column(Text, nullable=True)
    first_response_time = Column(Integer, nullable=True)  # seconds
    avg_response_time = Column(Integer, nullable=True)  # seconds

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="leads")
    status_history = relationship("LeadStatusHistory", backref="lead")

    def __repr__(self):
        return f"<QualifiedLead(id={self.id}, nombre='{self.nombre}', proyecto_interes='{self.proyecto_interes}')>"


class CampaignAnalytics(Base):
    """
    Track analytics data for campaigns and conversations.
    """
    __tablename__ = "campaign_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    total_conversations = Column(Integer, default=0)
    qualified_leads = Column(Integer, default=0) 
    avg_response_time = Column(Integer, default=0)  # in seconds
    active_conversations = Column(Integer, default=0)
    conversion_rate = Column(Integer, default=0)  # percentage
    platform_breakdown = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class OutboundCampaign(Base):
    """
    Track outbound marketing campaigns.
    """
    __tablename__ = "outbound_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_name = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    total_recipients = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    messages_delivered = Column(Integer, default=0)
    messages_failed = Column(Integer, default=0)
    responses_received = Column(Integer, default=0)
    leads_generated = Column(Integer, default=0)
    campaign_status = Column(String(50), default='pending')  # pending, running, completed, failed
    send_mode = Column(String(50), default='immediate')  # immediate, scheduled, throttled
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    messages = relationship("CampaignMessage", back_populates="campaign", cascade="all, delete-orphan")


class CampaignMessage(Base):
    """
    Track individual messages sent in campaigns.
    """
    __tablename__ = "campaign_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("outbound_campaigns.id", ondelete="CASCADE"), nullable=False)
    recipient_number = Column(String(20), nullable=False)
    message_sid = Column(String(100), unique=True, nullable=True)  # Twilio message SID
    message_status = Column(String(50), default='pending')  # pending, sent, delivered, failed, responded
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    campaign = relationship("OutboundCampaign", back_populates="messages")


class MessageLog(Base):
    """
    Comprehensive message logging for analytics and monitoring.
    """
    __tablename__ = "message_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    message_sid = Column(String(100), unique=True, nullable=True)  # Twilio SID
    direction = Column(String(20), nullable=False)  # inbound, outbound
    from_number = Column(String(20), nullable=False)
    to_number = Column(String(20), nullable=False)
    message_body = Column(Text, nullable=False)
    message_status = Column(String(50), nullable=True)
    platform = Column(String(20), default='whatsapp')
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("outbound_campaigns.id"), nullable=True)
    response_time = Column(Integer, nullable=True)  # seconds from user message to response
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    webhook_received_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_message_logs_created_at", "created_at"),
        Index("ix_message_logs_thread_id", "thread_id"),
    )


class AnalyticsKeyword(Base):
    """
    Track keyword performance for analytics.
    """
    __tablename__ = "analytics_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False)
    mentions = Column(Integer, default=0)
    lead_score = Column(Integer, default=0)  # 1-10 scale
    conversion_count = Column(Integer, default=0)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ContactList(Base):
    """
    Manage contact lists for outbound campaigns.
    """
    __tablename__ = "contact_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    contact_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    contacts = relationship("ContactListMember", back_populates="contact_list", cascade="all, delete-orphan")


class ContactListMember(Base):
    """
    Individual contacts in contact lists.
    """
    __tablename__ = "contact_list_members"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_list_id = Column(Integer, ForeignKey("contact_lists.id", ondelete="CASCADE"), nullable=False)
    phone_number = Column(String(20), nullable=False)
    name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    contact_list = relationship("ContactList", back_populates="contacts")


# Create all tables in the database (if they don't exist)
def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    # Initialize the database tables
    init_db()
    print("Database tables created successfully.")
