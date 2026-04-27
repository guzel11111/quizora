from django.contrib import admin
from .models import Quiz, Question, Answer, QuizResult, WrongAnswer, Friendship


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
    list_display = ['title', 'author', 'category', 'visibility', 'is_global', 'is_published', 'get_question_count', 'created_at']
    list_filter = ['category', 'visibility', 'is_published', 'created_at']
    search_fields = ['title', 'description', 'author__username']
    list_editable = ['is_published', 'visibility', 'is_global']
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


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'created_at', 'accepted_at']
    list_filter = ['status', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']
    readonly_fields = ['created_at', 'accepted_at']