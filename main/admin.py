from django.contrib import admin
from .models import Quiz, Question, Answer, QuizResult, WrongAnswer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    min_num = 4
    max_num = 4
    ordering = ['order']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    ordering = ['order']
    inlines = [AnswerInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['get_category_display', 'get_question_count', 'is_published']
    list_filter = ['is_published']
    search_fields = ['description']
    list_editable = ['is_published']
    inlines = [QuestionInline]

    def get_question_count(self, obj):
        return obj.get_question_count()
    get_question_count.short_description = 'Вопросов'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'time_limit', 'difficulty', 'order']
    list_filter = ['quiz', 'difficulty']
    search_fields = ['text']
    inlines = [AnswerInline]
    ordering = ['quiz', 'order']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct', 'order']
    list_filter = ['is_correct']
    search_fields = ['text']


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'score', 'total_questions', 'get_percentage', 'get_time_formatted', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['user__username']
    filter_horizontal = ['categories']
    readonly_fields = ['user', 'score', 'total_questions', 'time_spent', 'completed_at']

    def get_percentage(self, obj):
        return f"{obj.get_percentage()}%"
    get_percentage.short_description = 'Процент'

    def get_time_formatted(self, obj):
        return obj.get_time_formatted()
    get_time_formatted.short_description = 'Время'


@admin.register(WrongAnswer)
class WrongAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'is_repeated', 'answered_at']
    list_filter = ['is_repeated', 'answered_at']
    search_fields = ['user__username', 'question__text']
    readonly_fields = ['user', 'question', 'answered_at']