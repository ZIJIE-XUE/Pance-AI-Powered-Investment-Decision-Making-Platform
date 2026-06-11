"""User-related Pydantic models."""

from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    """Request to create a new user profile."""

    email: str = Field(..., description="User email address")
    display_name: str = Field("", description="Optional display name")
    age: int = Field(..., ge=18, le=120, description="User age")
    income: float = Field(..., ge=0, description="Annual income (CNY)")
    asset_size: float = Field(..., ge=0, description="Total investable assets (CNY)")
    investment_horizon: int = Field(..., description="Investment horizon in years")
    investment_goal: str = Field("", description="Investment goals in free text")


class UserResponse(BaseModel):
    """User profile returned to the frontend."""

    id: UUID
    email: str
    display_name: str
    age: int
    income: float
    asset_size: float
    investment_horizon: int
    investment_goal: str
    created_at: datetime

    model_config = {"from_attributes": True}
