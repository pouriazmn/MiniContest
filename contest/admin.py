from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import re_path, reverse
from django.utils.html import format_html

from .forms import RequestProblemForm
from .models import *


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'score', 'team_actions')
    readonly_fields = (
        'id',
        'team_actions'
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            re_path(
                r'^(?P<team_id>.+)/solve-attempt/$',
                self.admin_site.admin_view(self.process_solve_attempt),
                name='solve-attempt',
            ),
            re_path(
                r'^(?P<team_id>.+)/return-problem/$',
                self.admin_site.admin_view(self.process_return_problem),
                name='return-problem',
            ),
        ]
        return custom_urls + urls

    def team_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">request problem</a>&nbsp;'
            '<a class="button" href="{}">request problem</a>&nbsp;',
            reverse('admin:solve-attempt', args=[obj.pk]),
            reverse('admin:return-problem', args=[obj.pk])
        )

    team_actions.short_description = 'Team Actions'
    team_actions.allow_tags = True

    def proccess_return_problem(self, request, team_id, *args, **kwargs):
        self.procces_actioni(
            request=request,
            team_id=team_id,
            action_form=
        )

    def process_solve_attempt(self, request, team_id, *args, **kwargs):
        return self.process_action(
            request=request,
            team_id=team_id,
            action_form=RequestProblemForm,
            action_title='Request Problem',
        )

    def process_action(self, request,
                       team_id,
                       action_form,
                       action_title):

        team = self.get_object(request, team_id)

        if request.method == 'POST':
            form = action_form(request.POST, team_id=team_id)
            if form.is_valid():
                try:
                    form.save()
                except Exception as e:
                    self.message_user(request, f'sth went wrong: {str(e)}', level=messages.ERROR)
                else:
                    self.message_user(request, 'Success')
                    url = reverse(
                        'admin:contest_team_changelist',
                        # args=[team_id],
                        current_app=self.admin_site.name,
                    )
                    return HttpResponseRedirect(url)

        form = action_form(team_id=team_id)
        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['team'] = team
        context['title'] = action_title

        return TemplateResponse(
            request,
            'admin/team/team_action.html',
            context,
        )


# class SolvingAttemptForm(forms.ModelForm):
#     purchase_from = forms.ModelChoiceField(queryset=SolvingAttempt.objects.filter(problem=))
#

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
