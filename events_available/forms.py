from django import forms
from bookmarks.models import Rating

class RatingForm(forms.ModelForm):
    score = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],  # Выбор от 1 до 5
        widget=forms.RadioSelect,  # Визуализируем как радио-кнопки
        label='Ваша оценка',
    )

    class Meta:
        model = Rating
        fields = ['score']
