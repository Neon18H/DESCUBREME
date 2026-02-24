from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from core.models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class UserProfileForm(forms.ModelForm):
    likes_tags = forms.CharField(required=False, help_text='Separa por comas')
    fears_tags = forms.CharField(required=False, help_text='Separa por comas')

    class Meta:
        model = UserProfile
        fields = ('display_name', 'bio', 'city_default', 'likes_tags', 'fears_tags')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['likes_tags'].initial = ', '.join(self.instance.likes_tags or [])
            self.fields['fears_tags'].initial = ', '.join(self.instance.fears_tags or [])

    @staticmethod
    def _parse_tags(raw_value):
        return [tag.strip() for tag in (raw_value or '').split(',') if tag.strip()]

    def clean_likes_tags(self):
        return self._parse_tags(self.cleaned_data.get('likes_tags'))

    def clean_fears_tags(self):
        return self._parse_tags(self.cleaned_data.get('fears_tags'))
