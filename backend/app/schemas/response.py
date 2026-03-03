"""统一响应封装。"""


def success_response(data: dict | None = None, message: str = "success") -> dict:
    """返回统一格式响应。"""

    return {"code": 200, "message": message, "data": data or {}}

