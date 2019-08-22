from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Problem(models.Model):
    LEVELS = {
        "E": {
            "display_name": "easy",
            "min_cost": 50,
            "max_cost": 150,
            "reward": 1.4
        },
        "M": {
            "display_name": "medium",
            "min_cost": 100,
            "max_cost": 200,
            "reward": 1.6
        },
        "H": {
            "display_name": "hard",
            "min_cost": 150,
            "max_cost": 320,
            "reward": 1.9
        }
    }
    id = models.IntegerField(primary_key=True)
    level = models.CharField(
        max_length=2,
        choices=map(lambda it: (it[0], it[1]['display_name']), LEVELS.items())
    )
    type = models.CharField(max_length=1, choices=(('P', 'Problem'), ('D', 'Duel')))

    def level_display(self):
        return self.__class__.LEVELS[self.level]['display_name']

    def calculate_reward(self, cost):
        return self.__class__.LEVELS[self.level]['reward'] * cost

    def validate_cost(self, cost):
        l = self.__class__.LEVELS[self.level]
        if cost < l['min_cost']:
            raise ValidationError(f"Min cost of problem type {l['display_name']} is {l['min_cost']}")
        elif cost > l['max_cost']:
            raise ValidationError(f"Max cost of problem type {l['display_name']} is {l['max_cost']}")

    def __str__(self):
        return f"P-{self.id}({self.level_display()})"


class Team(models.Model):

    name = models.TextField()
    score = models.FloatField(default=500)
    problems = models.ManyToManyField(Problem, through='SolvingAttempt', related_name='teams',
                                      related_query_name='team')

    class Meta:
        ordering = ('-score', )

    def clean(self):
        if self.score < 0:
            raise ValidationError("Team score cannot set to negative!")
        if self.solvingattempt_set.filter(state='S').count() > 2:
            raise ValidationError("Team cannot have more than 2 active problems!")

    def can_request_problem(self):
        if self.solvingattempt_set.filter(state='S').count() >= 2:
            raise ValidationError("Team cannot have more than 2 active problems!")

    def __str__(self):
        return f"{self.name}(T-{self.id})"


class SolvingAttempt(models.Model):
    STATES = (
        ('S', 'Solving'),
        ('C', 'Checking'),
        ('SD', 'Solved')
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    start_time = models.DateTimeField(blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    cost = models.IntegerField()
    grade = models.IntegerField(validators=(MinValueValidator(0), MaxValueValidator(100)), null=True, blank=True)
    state = models.CharField(default='S', max_length=2, choices=STATES, blank=True)

    class Meta:
        unique_together = (('team', 'problem'), )

    def save(self, *args, **kwargs):
        cal_reward = kwargs.pop('cal_reward', False)
        buy_problem = kwargs.pop('buy_problem', False)
        if buy_problem:
            self.problem.validate_cost(self.cost)
            self.team.can_request_problem()
            self.team.score -= self.cost
            self.team.save()
        if cal_reward:
            price = self.problem.calculate_reward(self.cost) * (self.grade/100)
            self.team.score += price
            self.team.save()
        super().save(*args, **kwargs)

    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        else:
            return None

    def __str__(self):
        return f'{str(self.problem)} of {str(self.team)} for {self.cost}'


class Duel(models.Model):
    TYPES = {
        '1': {
            'display_name': 'Type1 8%',
            'factor': 0.08
        },
        '2': {
            'display_name': 'Type2 12%',
            'factor': 0.12
        },
        '3': {
            'display_name': 'Type3 16%',
            'factor': 0.16
        }
    }
    requested_by = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='duel_requests',
                                     related_query_name='duel_request')
    to = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='duels',
                           related_query_name='duel')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    winner = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='duel_wins',
                               related_query_name='win_duel', null=True, blank=True)
    type = models.CharField(max_length=1,
                            choices=map(lambda it: (it[0], it[1]['display_name']), TYPES.items()))
    pending = models.BooleanField(default=False, blank=True)

    def delete(self, *args, **kwargs):
        # todo: return exchanged scores
        pass

