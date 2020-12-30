from django.urls                import path
from kiwimarket                 import settings
from django.conf.urls.static    import static

from user.views  import (
                            SMSVerificationView,
                            VerificationCodeView,
                            CheckNickNameView,
                            SignUpView,
                            SelectMyAddressView,
                            GetNearAddressView,
                            AddMyAddressView,
                            DeleteMyAddressView,
                            UserProfileView,
                            SalesHistoryView,
                            ChangeOrderStatusView,
                        )

urlpatterns = [
    path('/smscheck', SMSVerificationView.as_view()),
    path('/checknum', VerificationCodeView.as_view()),
    path('/checknickname', CheckNickNameView.as_view()),
    path('/signup', SignUpView.as_view()),
    path('/selectmyaddress', SelectMyAddressView.as_view()),
    path('/getnearaddress/<int:code>', GetNearAddressView.as_view()),
    path('/addmyaddress', AddMyAddressView.as_view()),
    path('/deletemyaddress', DeleteMyAddressView.as_view()),
    path('/profile', UserProfileView.as_view()),
    path('/saleshistory', SalesHistoryView.as_view()),
    path('/changestatus/<int:product_id>', ChangeOrderStatusView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)