"""Input validation utilities."""

from src.utils.exceptions import ValidationError


def validate_age(age: int) -> int:
    """Validate user age is within acceptable range."""
    if not isinstance(age, int) or age < 18 or age > 120:
        raise ValidationError("年龄必须在18-120岁之间")
    return age


def validate_income(income: float) -> float:
    """Validate income is non-negative."""
    if income < 0:
        raise ValidationError("收入不能为负数")
    return income


def validate_asset_size(assets: float) -> float:
    """Validate total assets are non-negative."""
    if assets < 0:
        raise ValidationError("资产规模不能为负数")
    return assets


def validate_horizon_years(years: int) -> int:
    """Validate investment horizon is one of the supported values."""
    if years not in (5, 10, 20):
        raise ValidationError("投资期限必须为5年、10年或20年")
    return years


def validate_num_paths(num_paths: int) -> int:
    """Validate Monte Carlo simulation path count."""
    if num_paths < 100 or num_paths > 1_000_000:
        raise ValidationError("模拟路径数必须在100-1,000,000之间")
    return num_paths


def validate_initial_amount(amount: float) -> float:
    """Validate initial investment amount."""
    if amount <= 0:
        raise ValidationError("初始投资金额必须大于0")
    return amount
