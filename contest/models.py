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

    DRAW_DURATION = timedelta(seconds=20)

    requested_by = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='duel_requests',
                                     related_query_name='duel_request')
    to = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='duels',
                           related_query_name='duel')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    winner = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='duel_wins',
                               related_query_name='win_duel', null=True, blank=True)
    worth = models.FloatField(null=True, blank=True)
    pending = models.BooleanField(default=False, blank=True)

    def delete(self, *args, **kwargs):
        loser = self.requested_by if self.requested_by_id != self.winner_id else self.to
        loser.strength += self.worth
        self.winner.strength -= self.worth
        loser.save()
        self.winner.save()
        return super().delete(*args, **kwargs)

    def get_pending(self):
        return self.pending

    def clean(self):
        self.check_if_can_set_duel()
        winner, pending = self.get_winner()
        if winner:
            self.winner = winner
            self.worth, loser = self.cal_worth()
            self.trade_strength(loser)
        self.pending = pending

    def check_if_can_set_duel(self):
        c = 0
        for duel in self.requested_by.duel_requests.all():
            if duel.problem_id == self.problem_id and duel != self:
                c += 1
        if c >= 2:
            raise ValidationError("Team cannot request for duel on same problem more than 2 times")

        if self.requested_by.strength < 0:
            raise ValidationError("Team cannot request for duel with less than 2000 strength")

    def get_winner(self):
        try:
            solve_p1 = self.requested_by.solvingattempt_set.get(problem_id=self.problem.id)
        except SolvingAttempt.DoesNotExist:
            raise ValidationError(f"Team {str(self.requested_by)} should solve the problem themselves.")
        try:
            solve_p2 = self.to.solvingattempt_set.get(problem_id=self.problem.id)
        except SolvingAttempt.DoesNotExist:
            return None, True
        if solve_p1.state != 'SD':
            raise ValidationError(f"Team {str(self.requested_by)} should solve the problem themselves.")
        if solve_p2.state != 'SD':
            return None, True
        p1_score = int(solve_p1.purchased_from.grade if solve_p1.purchased_from else solve_p1.grade)
        p2_score = int(solve_p2.purchased_from.grade if solve_p2.purchased_from else solve_p2.grade)
        if p1_score > p2_score:
            return self.requested_by, False
        elif p2_score > p1_score:
            return self.to, False
        else:
            p1_time = solve_p1.purchased_from.get_duration if solve_p1.purchased_from else \
                solve_p1.get_duration
            p2_time = solve_p2.purchased_from.get_duration if solve_p2.purchased_from else \
                solve_p2.get_duration
            if p1_time - p2_time > Duel.DRAW_DURATION:
                return self.to, False
            elif p2_time - p1_time > Duel.DRAW_DURATION:
                return self.requested_by, False
            else:
                return None, False

    def cal_worth(self):
        loser = self.requested_by if self.requested_by != self.winner else self.to
        return loser.strength * self.problem.get_darsad(), loser

    def trade_strength(self, loser):
        loser.strength -= self.worth
        self.winner.strength += self.worth
        loser.save()
        self.winner.save()
