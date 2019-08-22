from django import forms
from django.contrib.admin import widgets
from django.contrib.admin.widgets import AdminSplitDateTime
from django.utils import timezone
from datetimepicker.widgets import DateTimePicker
from .models import Problem, SolvingAttempt, Team


class GeneralTeamForm(forms.Form):

    def __init__(self, *args, **kwargs):
        team_id = kwargs.pop('team_id')
        self.team_id = team_id
        return super().__init__(*args, **kwargs)


class RequestProblemForm(GeneralTeamForm):

    def __init__(self, *args, **kwargs):
        r = super().__init__(*args, **kwargs)
        problem_choices = tuple(map(lambda problem: (problem.id, str(problem)),
                                    Problem.objects.exclude(team__in=(self.team_id, ))))
        self.fields['problem'] = forms.ChoiceField(choices=problem_choices, required=True)
        self.fields['start_time'] = forms.DateTimeField(widget=widgets.AdminSplitDateTime, required=False)
        self.fields['cost'] = forms.IntegerField(min_value=50, max_value=320, required=True)
        return r

    def clean_start_time(self):
        data = self.cleaned_data.get('start_time')
        if not data:
            data = timezone.now()
        return data

    def save(self):
        obj = SolvingAttempt.objects.create(
            team_id=self.team_id,
            problem_id=self.cleaned_data['problem'],
            start_time=self.cleaned_data['start_time'],
            cost=self.cleaned_data['cost'])
        return obj


class ReturnProblemForm(GeneralTeamForm):

    def __init__(self, *args, **kwargs):
        r = super().__init__(*args, **kwargs)
        problem_choices = tuple(map(lambda satt: (satt.problem.id, str(satt.problem)),
                                    SolvingAttempt.objects.filter(team__in=(self.team_id, )).exclude(state='SD')))
        self.fields['team'] = forms.CharField(
            max_length=100,
            disabled=True,
            initial=str(Team.objects.get(id=self.team_id)))
        self.fields['problem'] = forms.ChoiceField(choices=problem_choices, required=True)
        self.fields['end_time'] = forms.DateTimeField(required=False)

    def clean_end_time(self):
        end_time = self.cleaned_data.get('end_time')
        if not end_time:
            end_time = timezone.now()
        return end_time

    def save(self):
        sattp = SolvingAttempt.objects.get(team_id=self.team_id, problem_id=int(self.cleaned_data['problem']))
        sattp.end_time = self.cleaned_data['end_time']
        sattp.state = 'SD'
        sattp.save()

