from django import forms
# from bookmarks.models import Rating

# class RatingForm(forms.ModelForm):
#     score = forms.ChoiceField(
#         choices=[(i, str(i)) for i in range(1, 6)],  # Выбор от 1 до 5
#         widget=forms.RadioSelect,  # Визуализируем как радио-кнопки
#         label='Ваша оценка',
#     )

#     class Meta:
#         model = Rating
#         fields = ['score']

from .models import EventOnlineGallery

class EventOnlineGalleryForm(forms.ModelForm):
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = EventOnlineGallery
        fields = ('image',)

    def save(self, commit=True, event=None):
        images = self.files.getlist('image')
        objects = []
        for img in images:
            obj = EventOnlineGallery(event=event, image=img)
            if commit:
                obj.save()
            objects.append(obj)
        return objects
    