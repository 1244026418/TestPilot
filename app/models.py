from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="user", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)
    description = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    endpoints = relationship("ApiEndpoint", back_populates="project", cascade="all, delete-orphan")
    runs = relationship("TestRun", back_populates="project", cascade="all, delete-orphan")


class ApiEndpoint(Base):
    __tablename__ = "api_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    method = Column(String(12), nullable=False, default="GET")
    url = Column(String(512), nullable=False)
    headers_json = Column(Text, default="{}", nullable=False)
    body_json = Column(Text, default="{}", nullable=False)
    expected_status = Column(Integer, default=200, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="endpoints")
    cases = relationship("TestCase", back_populates="endpoint", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("api_endpoints.id"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    category = Column(String(32), default="normal", nullable=False)
    request_headers_json = Column(Text, default="{}", nullable=False)
    request_body_json = Column(Text, default="{}", nullable=False)
    expected_status = Column(Integer, nullable=True)
    expected_contains = Column(String(256), nullable=True)
    reason = Column(Text, default="", nullable=False)
    created_by_ai = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    endpoint = relationship("ApiEndpoint", back_populates="cases")
    results = relationship("TestResult", back_populates="case", cascade="all, delete-orphan")


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    status = Column(String(24), default="running", nullable=False)
    total = Column(Integer, default=0, nullable=False)
    passed = Column(Integer, default=0, nullable=False)
    failed = Column(Integer, default=0, nullable=False)
    report_path = Column(String(512), nullable=True)
    summary_json = Column(Text, default="{}", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="runs")
    results = relationship("TestResult", back_populates="run", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False, index=True)
    testcase_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False, index=True)
    status = Column(String(16), nullable=False)
    status_code = Column(Integer, nullable=True)
    elapsed_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    response_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("TestRun", back_populates="results")
    case = relationship("TestCase", back_populates="results")
