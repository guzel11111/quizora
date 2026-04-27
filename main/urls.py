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
    
    # Новые маршруты
    path("my-quizzes/", views.my_quizzes, name="my_quizzes"),
    path("quiz/create/", views.create_quiz, name="create_quiz"),
    path("quiz/<int:quiz_id>/edit/", views.edit_quiz, name="edit_quiz"),
    path("question/<int:question_id>/edit/", views.edit_question, name="edit_question"),
    path("quiz/<int:quiz_id>/delete/", views.delete_quiz, name="delete_quiz"),
    path("friends/", views.friends, name="friends"),
    path("friend/add/<int:user_id>/", views.add_friend, name="add_friend"),
    path("friend/accept/<int:friendship_id>/", views.accept_friend, name="accept_friend"),
    path("friend/reject/<int:friendship_id>/", views.reject_friend, name="reject_friend"),
    path("friend/remove/<int:user_id>/", views.remove_friend, name="remove_friend"),
    path("search/", views.search_users, name="search_users"),
    
    path("logout/", views.logout_view, name="logout"),
    path("quiz/start/user/<int:quiz_id>/", views.start_user_quiz, name="start_user_quiz"),
]