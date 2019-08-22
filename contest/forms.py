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
        super().__init__(*args, **kwargs)
        team = Team.objects.get(id=self.team_id)
        self.fields['team'] = forms.CharField(
            max_length=100,
            disabled=True,
            strip=False,
            initial=str(team)
        )
        self.fields['team_score'] = forms.IntegerField(
            disabled=True,
            initial=team.score
        )


class RequestProblemForm(GeneralTeamForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        problem_choices = tuple(map(lambda problem: (problem.id, str(problem)),
                                    Problem.objects.exclude(team__in=(self.team_id, ))))
        self.fields['problem'] = forms.ChoiceField(choices=problem_choices, required=True)
        self.fields['start_time'] = forms.DateTimeField(required=False)
        self.fields['cost'] = forms.IntegerField(min_value=50, max_value=320, required=True)

    def clean_start_time(self):
        data = self.cleaned_data.get('start_time')
        if not data:
            data = timezone.now()
        return data

    def save(self):
        obj = SolvingAttempt(
            team_id=self.team_id,
            problem_id=self.cleaned_data['problem'],
            start_time=self.cleaned_data['start_time'],
            cost=self.cleaned_data['cost'])
        obj.save(buy_problem=True)
        return obj


class ReturnProblemForm(GeneralTeamForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        problem_choices = tuple(map(lambda satt: (satt.problem.id, str(satt.problem)),
                                    SolvingAttempt.objects.filter(team__in=(self.team_id,), state='S')))
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
        sattp.state = 'C'
        sattp.save()


class SetGradeForm(GeneralTeamForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        problem_choices = tuple(map(lambda satt: (satt.problem.id, str(satt)),
                                    SolvingAttempt.objects.filter(team__in=(self.team_id, )).exclude(state='SD')))
        self.fields['problem'] = forms.ChoiceField(choices=problem_choices, required=True)
        self.fields['end_time'] = forms.DateTimeField(required=False)
        self.fields['grade'] = forms.IntegerField(min_value=0, max_value=100, required=True)

    def clean_end_time(self):
        end_time = self.cleaned_data.get('end_time')
        if not end_time:
            end_time = timezone.now()
        return end_time

    def save(self):
        sattp = SolvingAttempt.objects.get(team_id=self.team_id, problem_id=int(self.cleaned_data['problem']))
        sattp.end_time = self.cleaned_data['end_time']
        sattp.state = 'SD'
        sattp.grade = self.cleaned_data['grade']
        sattp.save(cal_reward=True)


class ChangeScore(GeneralTeamForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        team = Team.objects.get(id=self.team_id)
        self.fields['change_score'] = forms.FloatField()

    def clean_change_score(self):
        s = self.cleaned_data.get('change_score')
        if s is None:
            s = 0
        return s

    def save(self):
        team = Team.objects.get(id=self.team_id)
        team.score += self.cleaned_data['change_score']
        print(team, team.score, self.cleaned_data['change_score'])
        team.save()
