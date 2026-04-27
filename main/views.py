from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Quiz, Question, Answer, QuizResult, WrongAnswer, Friendship
from .forms import QuizForm, QuestionForm, AnswerForm
from django.utils import timezone
import random


def landing(request):
    return render(request, "main/landing.html")


@login_required
def dashboard(request):
    return render(request, "main/dashboard.html")


@login_required
def categories(request):
    """Страница выбора категорий"""
    from django.db.models import Count
    
    # Получаем категории с количеством вопросов
        # Получаем категории с количеством вопросов — ТОЛЬКО глобальные квизы
    categories_data = []
    for code, name in Quiz.CATEGORY_CHOICES:
        count = Question.objects.filter(
            quiz__category=code, 
            quiz__is_published=True,
            quiz__is_global=True  # ← ДОБАВЛЕНО
        ).count()
        categories_data.append({
            'code': code,
            'name': name,
            'count': count,
        })
    
    context = {
        'categories': categories_data,
    }
    
    return render(request, "main/categories.html", context)


@login_required
def quiz_start(request):
    """Страница начала квиза — показывает первый вопрос"""
    categories = request.GET.getlist('category')
    question_count = int(request.GET.get('count', 10))  # ← Получаем количество
    
    if not categories:
        return redirect('main:categories')
    
    # Получаем все вопросы из выбранных категорий
    questions = Question.objects.filter(
        quiz__category__in=categories,
        quiz__is_published=True,
        quiz__is_global=True
    ).select_related('quiz').prefetch_related('answers')
    
    if not questions.exists():
        return render(request, "main/quiz_no_questions.html", {
            'categories': categories
        })
    
    # Берём случайные вопросы (количество из параметра)
    questions_list = list(questions)
    random.shuffle(questions_list)
    questions_list = questions_list[:question_count]  # ← Берём именно столько, сколько выбрал пользователь
    
    # Сохраняем в сессии
    request.session['quiz_questions'] = [q.id for q in questions_list]
    request.session['quiz_current_index'] = 0
    request.session['quiz_score'] = 0
    request.session['quiz_start_time'] = timezone.now().isoformat()
    request.session['quiz_categories'] = categories
    
    return redirect('main:quiz_question')


@login_required
def quiz_question(request):
    """Страница вопроса квиза"""
    question_ids = request.session.get('quiz_questions', [])
    current_index = request.session.get('quiz_current_index', 0)
    
    if not question_ids or current_index >= len(question_ids):
        return redirect('main:quiz_result')
    
    question_id = question_ids[current_index]
    question = Question.objects.get(id=question_id)
    
    answers = list(question.answers.all())
    random.shuffle(answers)
    
    context = {
        'question': question,
        'answers': answers,
        'current_index': current_index + 1,
        'total_questions': len(question_ids),
    }
    
    return render(request, "main/quiz_question.html", context)


@login_required
def quiz_submit(request):
    """Обработка ответа на вопрос"""
    if request.method != 'POST':
        return redirect('main:quiz_question')
    
    question_ids = request.session.get('quiz_questions', [])
    current_index = request.session.get('quiz_current_index', 0)
    score = request.session.get('quiz_score', 0)
    
    if not question_ids or current_index >= len(question_ids):
        return redirect('main:quiz_result')
    
    question_id = question_ids[current_index]
    question = Question.objects.get(id=question_id)
    
    selected_answer_id = request.POST.get('answer')
    is_correct = False
    
    if selected_answer_id:
        try:
            selected_answer = Answer.objects.get(id=selected_answer_id)
            if selected_answer.is_correct:
                score += 1
                request.session['quiz_score'] = score
                is_correct = True
            else:
                # Сохраняем неправильный ответ
                WrongAnswer.objects.create(user=request.user, question=question)
        except Answer.DoesNotExist:
            pass
    
    request.session['quiz_current_index'] = current_index + 1
    
    # Если вопросы закончились — сохраняем результат
    if current_index + 1 >= len(question_ids):
        quiz_start_time = request.session.get('quiz_start_time')
        if quiz_start_time:
            from datetime import datetime
            start_time = datetime.fromisoformat(quiz_start_time)
            time_spent = (timezone.now() - start_time).total_seconds()
            
            # Сохраняем результат
            result = QuizResult.objects.create(
                user=request.user,
                score=score,
                total_questions=len(question_ids),
                time_spent=int(time_spent)
            )
            
            # Добавляем категории
            quiz_categories = request.session.get('quiz_categories', [])
            quizzes = Quiz.objects.filter(category__in=quiz_categories)
            result.categories.set(quizzes)
    
    return redirect('main:quiz_question')


@login_required
def quiz_result(request):
    """Страница результата квиза"""
    score = request.session.get('quiz_score', 0)
    total_questions = len(request.session.get('quiz_questions', []))
    
    # Очищаем сессию
    request.session.pop('quiz_questions', None)
    request.session.pop('quiz_current_index', None)
    request.session.pop('quiz_score', None)
    request.session.pop('quiz_start_time', None)
    request.session.pop('quiz_categories', None)
    
    percentage = round((score / total_questions) * 100) if total_questions > 0 else 0
    
    context = {
        'score': score,
        'total_questions': total_questions,
        'percentage': percentage,
        'show_confetti': percentage >= 80,
    }
    
    return render(request, "main/quiz_result.html", context)


@login_required
def wrong_answers(request):
    """Страница неправильных ответов для повторения"""
    wrong_answers = request.user.wrong_answers.filter(is_repeated=False).select_related('question__quiz')
    
    # Группируем по категориям
    categories_dict = {}
    for wa in wrong_answers:
        category = wa.question.quiz.get_category_display()
        if category not in categories_dict:
            categories_dict[category] = []
        categories_dict[category].append(wa)
    
    context = {
        'wrong_answers': wrong_answers,
        'categories_dict': categories_dict,
        'total_count': wrong_answers.count(),
    }
    
    return render(request, "main/wrong_answers.html", context)


@login_required
def repeat_wrong_answer(request, wrong_answer_id):
    """Повторение неправильного вопроса"""
    try:
        wrong_answer = WrongAnswer.objects.get(id=wrong_answer_id, user=request.user, is_repeated=False)
    except WrongAnswer.DoesNotExist:
        return redirect('main:wrong_answers')
    
    question = wrong_answer.question
    answers = list(question.answers.all())
    random.shuffle(answers)
    
    if request.method == 'POST':
        selected_answer_id = request.POST.get('answer')
        
        if selected_answer_id:
            try:
                selected_answer = Answer.objects.get(id=selected_answer_id)
                if selected_answer.is_correct:
                    # Помечаем как перепройденный
                    wrong_answer.is_repeated = True
                    wrong_answer.save()
                    return redirect('main:wrong_answers_success')
            except Answer.DoesNotExist:
                pass
        
        # Если ответ неправильный, остаёмся на странице
        return render(request, "main/repeat_question.html", {
            'question': question,
            'answers': answers,
            'wrong_answer_id': wrong_answer_id,
            'is_correct': False,
        })
    
    return render(request, "main/repeat_question.html", {
        'question': question,
        'answers': answers,
        'wrong_answer_id': wrong_answer_id,
    })


@login_required
def wrong_answers_success(request):
    """Страница успеха после повторения"""
    return render(request, "main/wrong_answers_success.html")


@login_required
def my_quizzes(request):
    """Страница "Мои квизы" """
    quizzes = Quiz.objects.filter(author=request.user).order_by('-created_at')
    
    context = {
        'quizzes': quizzes,
    }
    
    return render(request, "main/my_quizzes.html", context)


@login_required
def create_quiz(request):
    """Создание нового квиза"""
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.author = request.user
            quiz.save()
            return redirect('main:edit_quiz', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    context = {
        'form': form,
    }
    
    return render(request, "main/create_quiz.html", context)


@login_required
def edit_quiz(request, quiz_id):
    """Редактирование квиза и добавление вопросов"""
    quiz = get_object_or_404(Quiz, id=quiz_id, author=request.user)
    
    if request.method == 'POST':
        # Обработка УДАЛЕНИЯ квиза
        if 'delete_quiz' in request.POST:
            quiz.delete()
            return redirect('main:my_quizzes')
        
        # Обработка добавления вопроса
        if 'add_question' in request.POST:
            question_form = QuestionForm(request.POST)
            if question_form.is_valid():
                question = question_form.save(commit=False)
                question.quiz = quiz
                question.order = quiz.questions.count() + 1
                question.save()
                
                # Добавляем 4 пустых ответа
                for i in range(1, 5):
                    Answer.objects.create(
                        question=question,
                        text='',
                        order=i,
                        is_correct=(i == 1)
                    )
                
                return redirect('main:edit_question', question_id=question.id)
        
        # Обработка обновления квиза
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            return redirect('main:edit_quiz', quiz_id=quiz.id)
    
    form = QuizForm(instance=quiz)
    question_form = QuestionForm()
    
    context = {
        'quiz': quiz,
        'form': form,
        'question_form': question_form,
    }
    
    return render(request, "main/edit_quiz.html", context)


@login_required
def edit_question(request, question_id):
    """Редактирование вопроса и ответов"""
    question = get_object_or_404(Question, id=question_id, quiz__author=request.user)
    answers = question.answers.all().order_by('order')
    
    if request.method == 'POST':
        if 'delete_question' in request.POST:
            # Удаление вопроса
            quiz_id = question.quiz.id
            question.delete()
            return redirect('main:edit_quiz', quiz_id=quiz_id)
        
        elif 'save_question' in request.POST:
            # Сохранение вопроса и ответов
            question_form = QuestionForm(request.POST, instance=question)
            if question_form.is_valid():
                question_form.save()
            
            # Сохранение ответов
            for answer in answers:
                answer_text = request.POST.get(f'answer_text_{answer.id}')
                is_correct = request.POST.get(f'answer_correct_{answer.id}') == 'on'
                answer.text = answer_text
                answer.is_correct = is_correct
                answer.save()
            
            return redirect('main:edit_quiz', quiz_id=question.quiz.id)
    
    question_form = QuestionForm(instance=question)
    
    context = {
        'question': question,
        'question_form': question_form,
        'answers': answers,
    }
    
    return render(request, "main/edit_question.html", context)


@login_required
def delete_quiz(request, quiz_id):
    """Удаление квиза"""
    quiz = get_object_or_404(Quiz, id=quiz_id, author=request.user)
    
    if request.method == 'POST':
        quiz.delete()
        return redirect('main:my_quizzes')
    
    return redirect('main:my_quizzes')


@login_required
def friends(request):
    """Страница друзей"""
    # Получаем все запросы дружбы пользователя
    sent_requests = Friendship.objects.filter(from_user=request.user)
    received_requests = Friendship.objects.filter(to_user=request.user)
    
    # Получаем принятые дружбы
    friends = User.objects.filter(
        Q(friendship_requests_sent__to_user=request.user, friendship_requests_sent__status='accepted') |
        Q(friendship_requests_received__from_user=request.user, friendship_requests_received__status='accepted')
    ).distinct()
    
    context = {
        'sent_requests': sent_requests,
        'received_requests': received_requests,
        'friends': friends,
    }
    
    return render(request, "main/friends.html", context)


@login_required
def add_friend(request, user_id):
    """Отправить запрос на дружбу"""
    to_user = get_object_or_404(User, id=user_id)
    
    if request.user == to_user:
        return redirect('main:friends')
    
    # Проверяем, не существует ли уже запрос
    friendship, created = Friendship.objects.get_or_create(
        from_user=request.user,
        to_user=to_user
    )
    
    if not created:
        friendship.status = 'pending'
        friendship.save()
    
    return redirect('main:friends')


@login_required
def accept_friend(request, friendship_id):
    """Принять запрос на дружбу"""
    friendship = get_object_or_404(Friendship, id=friendship_id, to_user=request.user)
    friendship.accept()
    return redirect('main:friends')


@login_required
def reject_friend(request, friendship_id):
    """Отклонить запрос на дружбу"""
    friendship = get_object_or_404(Friendship, id=friendship_id, to_user=request.user)
    friendship.reject()
    return redirect('main:friends')


@login_required
def remove_friend(request, user_id):
    """Удалить друга"""
    friend = get_object_or_404(User, id=user_id)
    
    # Удаляем все запросы дружбы между пользователями
    Friendship.objects.filter(
        from_user=request.user,
        to_user=friend
    ).delete()
    
    Friendship.objects.filter(
        from_user=friend,
        to_user=request.user
    ).delete()
    
    return redirect('main:friends')


@login_required
def search_users(request):
    """Поиск пользователей по логину"""
    query = request.GET.get('q', '')
    users = []
    error_message = None
    
    if query:
        # Ищем пользователей по логину (регистронезависимо)
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
        
        if not users.exists():
            error_message = "Пользователи не найдены"
    
    context = {
        'query': query,
        'users': users,
        'error_message': error_message,
    }
    
    return render(request, "main/search_users.html", context)

@login_required
def start_user_quiz(request, quiz_id):
    """Запуск личного квиза пользователя"""
    quiz = get_object_or_404(Quiz, id=quiz_id, author=request.user)
    
    # Получаем ВСЕ вопросы из этого квиза
    questions = Question.objects.filter(
        quiz=quiz,
        quiz__is_published=True
    ).select_related('quiz').prefetch_related('answers')
    
    if not questions.exists():
        return render(request, "main/quiz_no_questions.html", {'categories': [quiz.category]})
    
    # Берём все вопросы (или ограничиваем до 30)
    questions_list = list(questions)
    random.shuffle(questions_list)
    questions_list = questions_list[:30]  # Максимум 30 вопросов
    
    # Сохраняем в сессии
    request.session['quiz_questions'] = [q.id for q in questions_list]
    request.session['quiz_current_index'] = 0
    request.session['quiz_score'] = 0
    request.session['quiz_start_time'] = timezone.now().isoformat()
    request.session['quiz_categories'] = [quiz.category]
    
    return redirect('main:quiz_question')

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("main:dashboard")
    else:
        form = UserCreationForm()

    return render(request, "main/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("main:dashboard")
    else:
        form = AuthenticationForm(request)

    return render(request, "main/login.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("main:landing")