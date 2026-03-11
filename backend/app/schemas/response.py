

def success_response(data: dict | None = None, message: str = "success") -> dict:

    return {"code": 200, "message": message, "data": data or {}}

