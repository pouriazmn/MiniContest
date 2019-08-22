from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Problem(models.Model):
    REWARDS = {
        'E': 400,
        'M': 600,
        'H': 800
    }

    DARSADS = {
        'E': 0.06,
        'M': 0.08,
        'H': 0.10
    }

    LEVELS = (
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard')
    )
    id = models.IntegerField(primary_key=True)
    title = models.TextField()
    level = models.CharField(max_length=2, choices=LEVELS)
    is_mystery = models.BooleanField(default=False)
    cost = models.IntegerField(default=0)

    def __str__(self):
        if self.is_mystery:
            return f"mystery-{self.id}"
        else:
            return f"problem-{self.id}({self.level})"

    def get_reward(self, cost=None, grade=100):
        if not self.is_mystery:
            return self.__class__.REWARDS[self.level]*(grade/30)
        return 0

    def get_darsad(self):
        if not self.is_mystery:
            return self.__class__.DARSADS[self.level]
        return 0


class Team(models.Model):

    name = models.TextField()
    strength = models.FloatField(default=0)
    is_deleted = models.BooleanField(default=False)
    problems = models.ManyToManyField(Problem, through='SolvingAttempt', related_name='teams',
                                      related_query_name='team')

    class Meta:
        ordering = ('-strength', )

    @property
    def pending_duels(self):
        return self.duels.filter(pending=True).count()

    @property
    def pending_duels_display(self):
        return f'{self.pending_duels} -> ' + ', '.join(map(lambda x: str(x.problem), self.duels.filter(pending=True)))

    @property
    def active_problems(self):
        return self.solvingattempt_set.filter(state='S').count()

    @property
    def active_problems_display(self):
        return f'{self.active_problems} -> ' + ', '.join(map(lambda x: f"{str(x.problem)} \"{x.state}\"",
                                                             self.solvingattempt_set.exclude(state='SD')))

    def __str__(self):
        return f"T-{self.id}"


class SolvingAttempt(models.Model):
    STATES = (
        ('S', 'Solving'),
        ('C', 'Checking'),
        ('SD', 'Solved')
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    grade = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(30)])
    start_time = models.DateTimeField(blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_purchased = models.BooleanField(default=False, blank=True)
    purchased_from = models.ForeignKey("self", default=None, null=True, blank=True, on_delete=models.CASCADE)
    purchased_timedelta = models.DurationField(null=True, blank=True)
    purchased_grade = models.IntegerField(null=True, blank=True)
    purchase_cost = models.IntegerField(default=0, blank=True)
    state = models.CharField(default='S', max_length=2, choices=STATES, blank=True)
    mystery_cost = models.IntegerField(default=0, blank=True)

    class Meta:
        unique_together = (('team', 'problem'), )

    def solve_duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        else:
            return None

    def clean(self):
        if not getattr(self, 'start_time', None):
            # mystery cost must decrease from team strength
            self.check_for_problem_acceptance()
            self.start_time = timezone.now()
        if self.grade is not None and not self.end_time:
            self.end_time = timezone.now()
            self.mark_as_solved()
        elif self.end_time and self.grade is None:
            self.state = 'C'
        elif self.end_time and self.grade is not None and self.state != 'SD':
            self.mark_as_solved()

        try:
            if self.purchased_timedelta and self.purchased_timedelta < self.get_duration:
                raise ValidationError("Purchase timedelta can not be shorter than actual solving time.")
            if self.purchased_grade and self.purchased_grade > self.grade:
                raise ValidationError("Purchase grade can not be better than actual grade.")
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError("Team should solve the problem first then they can submit purchase trade.")
        if self.purchased_from and not self.is_purchased and self.state == 'SD':
            self.is_purchased = True
            self.team.strength -= self.purchased_from.purchase_cost
            self.purchased_from.team.strength += self.purchased_from.purchase_cost
            self.team.save()
            self.purchased_from.team.save()
        elif self.purchased_from and not self.is_purchased:
            raise ValidationError("Team can not purchase problem before submitting it.")

    def save(self, *args, **kwargs):
        x = super().save(*args, **kwargs)
        if self.state == 'SD':
            for duel in self.team.duels.filter(pending=True, problem_id=self.problem.id):
                duel.clean()
                duel.save()
        return x

    def check_for_problem_acceptance(self):
        if self.team.pending_duels:
            f = False
            pending_duels = self.team.duels.filter(pending=True)
            for duel in pending_duels:
                f = f or duel.problem_id == self.problem_id or duel.problem in self.team.problems.all()
            if not f:
                raise ValidationError("Team have pending duels.")
        if self.team.active_problems >= 4:
            raise ValidationError("Team cannot get another Problem before solving other 2 active problems")

    def mark_as_solved(self):
        self.state = 'SD'
        self.team.strength += self.problem.get_reward(grade=self.grade)
        self.team.save()

    @property
    def get_duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        else:
            return None

    def __str__(self):
        return f'{str(self.problem)} -> {str(self.team)}'


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