from django import forms
from .models import Quiz, Question, Answer


class QuizForm(forms.ModelForm):
    """Форма создания/редактирования квиза"""
    
    class Meta:
        model = Quiz
        fields = ['title', 'category', 'visibility']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название квиза',
                'maxlength': 200,
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
        }


class QuestionForm(forms.ModelForm):
    """Форма создания/редактирования вопроса"""
    
    class Meta:
        model = Question
        fields = ['text', 'time_limit']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Текст вопроса',
                'rows': 2,
                'maxlength': 500,
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 10,
                'max': 120,
            }),
        }


class AnswerForm(forms.ModelForm):
    """Форма создания/редактирования ответа"""
    
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Вариант ответа',
                'maxlength': 300,
            }),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }