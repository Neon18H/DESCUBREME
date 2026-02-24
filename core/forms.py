from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from core.models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ProfileForm(forms.ModelForm):
    likes_tags = forms.CharField(required=False)
    avoid_tags = forms.CharField(required=False)
    preferred_vibes = forms.MultipleChoiceField(
        required=False,
        choices=UserProfile.VIBE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = UserProfile
        fields = (
            'display_name', 'bio', 'city_default', 'website', 'instagram',
            'avatar', 'cover', 'likes_tags', 'avoid_tags', 'budget_min_cop',
            'budget_max_cop', 'max_distance_km', 'preferred_vibes', 'is_private',
            'show_city', 'show_tags', 'allow_friend_requests',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['likes_tags'].initial = ', '.join(self.instance.likes_tags or [])
            self.fields['avoid_tags'].initial = ', '.join(self.instance.avoid_tags or [])
            self.fields['preferred_vibes'].initial = self.instance.preferred_vibes or []

        for name, field in self.fields.items():
            css = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
                continue
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'vibes-checks'})
                continue
            if isinstance(field.widget, forms.FileInput):
                css = 'form-control'
            field.widget.attrs.update({'class': css})

    @staticmethod
    def _parse_tags(raw_value):
        return [tag.strip() for tag in (raw_value or '').split(',') if tag.strip()]

    def clean_likes_tags(self):
        return self._parse_tags(self.cleaned_data.get('likes_tags'))

    def clean_avoid_tags(self):
        return self._parse_tags(self.cleaned_data.get('avoid_tags'))
