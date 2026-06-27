from rest_framework.response import Response


def api_success(data=None, message="操作成功", status=200):
    body = {"status": "success", "message": message}
    if data is not None:
        body["data"] = data
    return Response(body, status=status)


def api_error(message, status=400):
    return Response({"status": "error", "message": message}, status=status)


def parse_bool_param(value: str) -> bool:
    """Convert a query-string boolean token to Python bool.

    Accepts: "true"/"1"/"yes" → True; anything else → False.
    """
    return value.lower() in ("true", "1", "yes")
