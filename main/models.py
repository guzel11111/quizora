from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Quiz(models.Model):
    """Квиз (категория)"""
    CATEGORY_CHOICES = [
        ('general', 'Общие знания'),
        ('science', 'Наука'),
        ('history', 'История'),
        ('geography', 'География'),
        ('literature', 'Литература'),
        ('movies', 'Фильмы'),
        ('music', 'Музыка'),
        ('sports', 'Спорт'),
        ('technology', 'Технологии'),
        ('astronomy', 'Астрономия'),
        ('art', 'Искусство'),
        ('food', 'Еда и кулинария'),
        ('animals', 'Животные'),
        ('mythology', 'Мифология'),
        ('other', 'Другое'),
    ]

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes', verbose_name='Автор')
    category = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES, default='general', unique=True)
    is_published = models.BooleanField('Опубликован', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['category']

    def __str__(self):
        return self.get_category_display()

    def get_question_count(self):
        return self.questions.count()


class Question(models.Model):
    """Вопрос с 4 вариантами ответа"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name='Категория')
    text = models.TextField('Текст вопроса')
    time_limit = models.IntegerField('Время на ответ (секунды)', default=30)
    order = models.IntegerField('Порядок', default=0)
    difficulty = models.IntegerField('Сложность (1-5)', default=3, choices=[(i, str(i)) for i in range(1, 6)])

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]

    def get_correct_answer(self):
        return self.answers.filter(is_correct=True).first()


class Answer(models.Model):
    """Вариант ответа (всего 4 на вопрос)"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос')
    text = models.CharField('Текст ответа', max_length=300)
    is_correct = models.BooleanField('Правильный ответ', default=False)
    order = models.IntegerField('Порядок (1-4)', default=1)

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        ordering = ['order']

    def __str__(self):
        return f"{self.text} {'✓' if self.is_correct else ''}"


class QuizResult(models.Model):
    """Результат прохождения квиза"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results', verbose_name='Пользователь')
    categories = models.ManyToManyField(Quiz, related_name='results', verbose_name='Категории')
    score = models.IntegerField('Правильных ответов', default=0)
    total_questions = models.IntegerField('Всего вопросов', default=0)
    time_spent = models.IntegerField('Затраченное время (секунды)', default=0)
    completed_at = models.DateTimeField('Завершено', default=timezone.now)

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} — {self.score}/{self.total_questions}"

    def get_percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100)
    
    def get_time_formatted(self):
        minutes = self.time_spent // 60
        seconds = self.time_spent % 60
        return f"{minutes:02d}:{seconds:02d}"


class WrongAnswer(models.Model):
    """Неправильные ответы пользователя для повторения"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wrong_answers', verbose_name='Пользователь')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='wrong_answers', verbose_name='Вопрос')
    answered_at = models.DateTimeField('Отвечено', default=timezone.now)
    is_repeated = models.BooleanField('Перепройден', default=False)

    class Meta:
        verbose_name = 'Неправильный ответ'
        verbose_name_plural = 'Неправильные ответы'
        ordering = ['-answered_at']

    def __str__(self):
        return f"{self.user.username} — {self.question.text[:30]}"