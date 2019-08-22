from django import forms
from .models import Team


class RequestProblemForm(forms.Form):
    team_id = forms.ChoiceField(choices=[], required=True, label='Team')
