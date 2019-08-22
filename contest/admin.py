from django.contrib import admin
from django import forms
from .models import *


# @admin.register(Team)
# class TeamAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'strength', 'pending_duels_display', 'active_problems_display')


# # class SolvingAttemptForm(forms.ModelForm):
# #     purchase_from = forms.ModelChoiceField(queryset=SolvingAttempt.objects.filter(problem=))
# #

# @admin.register(SolvingAttempt)
# class SolvingAttemptAdmin(admin.ModelAdmin):
#     readonly_fields = ('is_purchased', 'get_duration')
#     list_display = ('id', 'team_id', 'problem', 'state', 'grade', 'get_duration',
#                     'purchased_from', 'purchased_timedelta', 'purchased_grade', 'purchase_cost')
#     list_filter = ('team', 'problem', 'state')


# @admin.register(Duel)
# class DuelAdmin(admin.ModelAdmin):
#     list_display = ('id', 'requested_by', 'to', 'problem', 'pending', 'worth', 'winner')


admin.site.register(Problem)
