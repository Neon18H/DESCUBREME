from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

MOODS = [
    ('alegre', 'Alegre'),
    ('chill', 'Chill'),
    ('cine', 'Cine'),
    ('comida', 'Comida'),
]

TRANSPORTS = [('a pie', 'A pie'), ('carro', 'Carro'), ('moto', 'Moto'), ('uber/taxi', 'Uber/Taxi')]

INTERESTS = [
    ('comida', 'Comida'),
    ('rumba', 'Rumba'),
    ('naturaleza', 'Naturaleza'),
    ('cine', 'Cine'),
    ('arte', 'Arte'),
    ('café', 'Café'),
    ('compras', 'Compras'),
    ('deporte', 'Deporte'),
]


class PlanGeneratorForm(forms.Form):
    city = forms.CharField(initial='Medellín', max_length=120)
    mood = forms.ChoiceField(choices=MOODS)
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    budget = forms.IntegerField(min_value=10000)
    group_size = forms.IntegerField(min_value=1, max_value=10)
    transport = forms.ChoiceField(choices=TRANSPORTS)
    interests = forms.MultipleChoiceField(choices=INTERESTS, widget=forms.CheckboxSelectMultiple)
    radius_km = forms.IntegerField(initial=5, min_value=1, max_value=40)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('start_time') and cleaned.get('end_time') and cleaned['start_time'] >= cleaned['end_time']:
            raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        return cleaned


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
