from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import Quiz, Question, Answer, QuizResult, WrongAnswer
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
    categories_data = []
    for code, name in Quiz.CATEGORY_CHOICES:
        count = Question.objects.filter(quiz__category=code, quiz__is_published=True).count()
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
    is_mix = request.GET.get('mix') == 'true'
    
    if not categories:
        return redirect('main:categories')
    
    # Получаем все вопросы из выбранных категорий
    questions = Question.objects.filter(
        quiz__category__in=categories,
        quiz__is_published=True
    ).select_related('quiz').prefetch_related('answers')
    
    if not questions.exists():
        return render(request, "main/quiz_no_questions.html", {
            'categories': categories
        })
    
    # Берём случайные 10 вопросов
    questions_list = list(questions)
    random.shuffle(questions_list)
    questions_list = questions_list[:10]
    
    # Сохраняем вопросы в сессии
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