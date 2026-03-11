
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeeRuleSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    free_minutes: int
    rate_per_hour: float
    max_daily: float
    is_active: bool
    created_at: datetime


class FeeRuleUpdatePayload(BaseModel):

    name: str = Field(..., min_length=1, max_length=50)
    free_minutes: int = Field(..., ge=0, le=1440)
    rate_per_hour: float = Field(..., ge=0, le=9999)
    max_daily: float = Field(..., ge=0, le=9999)


class FeeIncomeSummary(BaseModel):

    total_fee: float
    owner_income_total: float
    admin_income_total: float
    owner_income_count: int
    admin_income_count: int
