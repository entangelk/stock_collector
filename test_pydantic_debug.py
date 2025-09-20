#!/usr/bin/env python3
"""
Pydantic v2 호환성 디버그 테스트
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

print("Pydantic 기본 테스트 시작...")

try:
    # 1. 가장 기본적인 모델
    class SimpleModel(BaseModel):
        name: str
        value: int

    simple = SimpleModel(name="test", value=123)
    print("✅ 기본 모델 OK")

except Exception as e:
    print(f"❌ 기본 모델 실패: {e}")

try:
    # 2. Field 사용하는 모델
    class FieldModel(BaseModel):
        name: str = Field(..., description="Name field")
        value: int = Field(..., description="Value field")

    field_model = FieldModel(name="test", value=123)
    print("✅ Field 모델 OK")

except Exception as e:
    print(f"❌ Field 모델 실패: {e}")

try:
    # 3. Validator 사용하는 모델
    class ValidatorModel(BaseModel):
        name: str = Field(..., description="Name field")
        value: int = Field(..., description="Value field")

        @field_validator('name')
        @classmethod
        def validate_name(cls, v):
            return v

    validator_model = ValidatorModel(name="test", value=123)
    print("✅ Validator 모델 OK")

except Exception as e:
    print(f"❌ Validator 모델 실패: {e}")

try:
    # 4. ConfigDict 사용하는 모델
    class ConfigModel(BaseModel):
        name: str = Field(..., description="Name field")
        value: int = Field(..., description="Value field")

        model_config = ConfigDict(
            json_schema_extra={
                "example": {
                    "name": "test",
                    "value": 123
                }
            }
        )

    config_model = ConfigModel(name="test", value=123)
    print("✅ Config 모델 OK")

except Exception as e:
    print(f"❌ Config 모델 실패: {e}")

try:
    # 5. datetime 사용하는 모델
    class DateTimeModel(BaseModel):
        name: str = Field(..., description="Name field")
        created: datetime = Field(default_factory=datetime.utcnow)

    datetime_model = DateTimeModel(name="test")
    print("✅ DateTime 모델 OK")

except Exception as e:
    print(f"❌ DateTime 모델 실패: {e}")

try:
    # 6. date 사용하는 모델
    class DateModel(BaseModel):
        name: str = Field(..., description="Name field")
        today: date = Field(..., description="Today field")

    from datetime import date as date_import
    date_model = DateModel(name="test", today=date_import.today())
    print("✅ Date 모델 OK")

except Exception as e:
    print(f"❌ Date 모델 실패: {e}")

print("\nPydantic 디버그 테스트 완료!")