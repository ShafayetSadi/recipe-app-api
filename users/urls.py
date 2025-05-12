from django.urls import path

from users import views

app_name = "users"
urlpatterns = [
    path("create/", views.UserCreateView.as_view(), name="create"),
    path("token/", views.UserTokenView.as_view(), name="token"),
    path("me/", views.UserManageView.as_view(), name="me"),
]
