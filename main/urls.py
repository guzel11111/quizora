from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("categories/", views.categories, name="categories"),
    path("quiz/start/", views.quiz_start, name="quiz_start"),
    path("quiz/question/", views.quiz_question, name="quiz_question"),
    path("quiz/submit/", views.quiz_submit, name="quiz_submit"),
    path("quiz/result/", views.quiz_result, name="quiz_result"),
    path("wrong-answers/", views.wrong_answers, name="wrong_answers"),
    path("wrong-answers/repeat/<int:wrong_answer_id>/", views.repeat_wrong_answer, name="repeat_wrong_answer"),
    path("wrong-answers/success/", views.wrong_answers_success, name="wrong_answers_success"),
    path("logout/", views.logout_view, name="logout"),
]