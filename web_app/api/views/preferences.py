from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from web_app.api.serializers.preferences import TimezonePreferenceSerializer
from web_app.api.utils import api_success
from web_app.utils.timezone import store_session_timezone


class TimezonePreferenceAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="儲存使用者顯示時區",
        description="將瀏覽器自動偵測到的 IANA timezone 儲存在 session，供頁面顯示時間使用。",
        tags=["偏好設定"],
        request=TimezonePreferenceSerializer,
        responses=TimezonePreferenceSerializer,
    )
    def post(self, request):
        serializer = TimezonePreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        timezone_name = store_session_timezone(
            request.session, serializer.validated_data["timezone"]
        )
        return api_success({"timezone": timezone_name}, message="時區設定已更新")
