import json

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from core.models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ProfileEditForm(forms.ModelForm):
    avatar = forms.ImageField(required=False)
    cover = forms.ImageField(required=False)
    likes_tags = forms.CharField(required=False, widget=forms.HiddenInput())
    hobbies_tags = forms.CharField(required=False, widget=forms.HiddenInput())
    avoid_tags = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = UserProfile
        fields = (
            'display_name',
            'about',
            'bio',
            'country',
            'city',
            'website',
            'instagram',
            'avatar',
            'cover',
            'likes_tags',
            'hobbies_tags',
            'avoid_tags',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['likes_tags'].initial = json.dumps(self.instance.likes_tags or [])
            self.fields['hobbies_tags'].initial = json.dumps(self.instance.hobbies_tags or [])
            self.fields['avoid_tags'].initial = json.dumps(self.instance.avoid_tags or [])

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.HiddenInput):
                continue
            field.widget.attrs.setdefault('class', 'form-control')

        self.fields['bio'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
        self.fields['about'].widget.attrs['maxlength'] = 160

    @staticmethod
    def _normalize_tags(raw_value):
        if isinstance(raw_value, list):
            values = raw_value
        else:
            parsed_values = []
            text_value = (raw_value or '').strip()
            if text_value:
                try:
                    json_value = json.loads(text_value)
                    if isinstance(json_value, list):
                        parsed_values = json_value
                    elif isinstance(json_value, str):
                        parsed_values = [chunk for chunk in json_value.split(',')]
                except json.JSONDecodeError:
                    parsed_values = [chunk for chunk in text_value.split(',')]
            values = parsed_values

        cleaned = []
        seen = set()
        for value in values:
            tag = str(value).strip()
            if not tag:
                continue
            normalized = tag.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(tag[:24])
            if len(cleaned) == 20:
                break
        return cleaned

    def clean_likes_tags(self):
        return self._normalize_tags(self.cleaned_data.get('likes_tags'))

    def clean_hobbies_tags(self):
        return self._normalize_tags(self.cleaned_data.get('hobbies_tags'))

    def clean_avoid_tags(self):
        return self._normalize_tags(self.cleaned_data.get('avoid_tags'))
