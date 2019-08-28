from random import randint

from datetimepicker.widgets import DateTimePicker
from django import forms
from django.contrib.admin import widgets
from django.contrib.admin.widgets import AdminSplitDateTime
from django.utils import timezone
from nbformat import ValidationError

from .models import Problem, SolvingAttempt, Team, Duel


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
        self.fields['team_score'] = forms.FloatField(
            disabled=True,
            initial=team.score
        )


class RequestProblemForm(GeneralTeamForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        problem_choices = tuple(map(lambda problem: (problem.id, str(problem)),
                                    Problem.objects.exclude(team__in=(self.team_id, )).filter(type='P')))
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


class RequestForDuelForm(GeneralTeamForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        to_teams = list(map(
            lambda t: (t.id, str(t)),
            filter(lambda t: t.current_duels_count() == 0, Team.objects.all().exclude(id=self.team_id))
        ))
        to_teams.insert(0, (None, '----'))
        problem_choices = list(map(
            lambda p: (p.id, str(p)),
            Problem.objects.filter(type='D')
        ))
        problem_choices.insert(0, (None, '----'))

        self.fields['to_team'] = forms.ChoiceField(choices=to_teams, label='To', required=False)
        self.fields['problem'] = forms.ChoiceField(choices=problem_choices, required=False)
        self.fields['type'] = forms.ChoiceField(
            choices=map(lambda it: (it[0], it[1]['display_name']), Duel.TYPES.items())
        )

    def clean_to_team(self):
        to_team = self.cleaned_data['to_team']
        if not to_team:
            to_teams = list(filter(lambda t: t.current_duels_count() == 0, Team.objects.exclude(id=self.team_id)))
            l = len(to_teams)
            to_team = to_teams[randint(0, l-1)]
        else:
            to_team = Team.objects.get(id=to_team)
        return to_team

    def clean_problem(self):
        problem = self.cleaned_data['problem']
        if not problem:
            problems = Problem.objects.filter(type='D').exclude(
                duel__requested_by__in=(self.team_id, self.cleaned_data['to_team']),
                duel__to__in=(self.team_id, self.cleaned_data['to_team']))
            l = len(problems)
            problem = problems[randint(0, l-1)]
        return problem

    def save(self):
        d = Duel(
            requested_by_id=self.team_id,
            to=self.cleaned_data['to_team'],
            problem=self.cleaned_data['problem'],
            type=self.cleaned_data['type']
        )
        d.save(set_duel=True)
        return d


class SetDuelWinner(forms.Form):

    def __init__(self, *args, **kwargs):
        duel = kwargs.pop('duel')
        self.duel = duel
        super().__init__(*args, **kwargs)
        self.fields['requested_by'] = forms.ChoiceField(
            choices=((duel.requested_by.id, str(duel.requested_by)), ),
            disabled=True,
            required=False
        )
        self.fields['to'] = forms.ChoiceField(
            choices=((duel.to.id, str(duel.to)), ),
            disabled=True,
            required=False
        )
        self.fields['type'] = forms.CharField(initial=duel.get_type_display(), disabled=True, required=False)
        self.fields['winner'] = forms.ChoiceField(
            choices=(
                (duel.requested_by.id, str(duel.requested_by)),
                (duel.to.id, str(duel.to))
            )
        )

    def clean_winner(self):
        return int(self.cleaned_data['winner'])

    def save(self):
        self.duel.winner_id = self.cleaned_data['winner']
        self.duel.save(set_winner=True)
        return self.duel
