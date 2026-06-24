from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from web_app.api.serializers.preferences import TimezonePreferenceSerializer
from web_app.api.utils import api_success
from web_app.utils.timezone import store_session_timezone

_PreferencesErrorResponse = inline_serializer(
    name="PreferencesErrorResponse",
    fields={
        "status": serializers.CharField(default="error"),
        "message": serializers.CharField(),
    },
)


class TimezonePreferenceAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="儲存使用者顯示時區",
        description=(
            "將瀏覽器自動偵測到的 IANA timezone 儲存在 session，供頁面顯示時間使用。"
            "無需登入即可呼叫。"
        ),
        tags=["偏好設定"],
        request=TimezonePreferenceSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="TimezonePreferenceResponse",
                    fields={
                        "status": serializers.CharField(default="success"),
                        "message": serializers.CharField(default="時區設定已更新"),
                        "data": inline_serializer(
                            name="TimezonePreferenceData",
                            fields={
                                "timezone": serializers.CharField(
                                    help_text="已儲存的 IANA 時區名稱"
                                )
                            },
                        ),
                    },
                ),
                description="時區儲存成功",
                examples=[
                    OpenApiExample(
                        "成功範例",
                        value={
                            "status": "success",
                            "message": "時區設定已更新",
                            "data": {"timezone": "Asia/Taipei"},
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=_PreferencesErrorResponse,
                description="timezone 欄位缺失或非合法 IANA 時區名稱",
                examples=[
                    OpenApiExample(
                        "缺少欄位",
                        value={"status": "error", "message": "This field is required."},
                    ),
                    OpenApiExample(
                        "無效時區",
                        value={"status": "error", "message": "不合法的時區名稱"},
                    ),
                ],
            ),
        },
    )
    def post(self, request):
        serializer = TimezonePreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        timezone_name = store_session_timezone(
            request.session, serializer.validated_data["timezone"]
        )
        return api_success({"timezone": timezone_name}, message="時區設定已更新")
