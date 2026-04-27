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

    VISIBILITY_CHOICES = [
        ('public', 'Публичный'),
        ('friends', 'Только друзьям'),
        ('private', 'Приватный (по ссылке)'),
    ]

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes', verbose_name='Автор')
    category = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES, default='general')
    visibility = models.CharField('Видимость', max_length=10, choices=VISIBILITY_CHOICES, default='public')
    is_global = models.BooleanField('Глобальный квиз', default=False, help_text='Если включено — квиз появится в общем списке "Начать квиз" (только для админов)')
    is_published = models.BooleanField('Опубликован', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Квиз'
        verbose_name_plural = 'Квизы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_question_count(self):
        return self.questions.count()

    def is_accessible_by(self, user):
        """Проверяет, доступен ли квиз для пользователя"""
        if self.visibility == 'public':
            return True
        if not user.is_authenticated:
            return False
        if self.author == user:
            return True
        if self.visibility == 'friends':
            return Friendship.objects.filter(
                from_user=self.author,
                to_user=user,
                status='accepted'
            ).exists() or Friendship.objects.filter(
                from_user=user,
                to_user=self.author,
                status='accepted'
            ).exists()
        return False


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

# ... (предыдущие модели остаются без изменений) ...

class Friendship(models.Model):
    """Дружба между пользователями"""
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ]

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendship_requests_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendship_requests_received')
    status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    accepted_at = models.DateTimeField('Принято', null=True, blank=True)

    class Meta:
        verbose_name = 'Дружба'
        verbose_name_plural = 'Дружба'
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username} ({self.status})"

    def accept(self):
        """Принять запрос на дружбу"""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()

    def reject(self):
        """Отклонить запрос на дружбу"""
        self.status = 'rejected'
        self.save()