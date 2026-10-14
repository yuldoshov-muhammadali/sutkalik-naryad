"""Platforma sahifalari (5-bosqich: bosh sahifa, kirish, parol)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.shortcuts import render
from django.urls import reverse_lazy

from . import permissions as perms, stats
from .auth import LoginForm
from .dashboard import cadet_dashboard, fmt_day, staff_dashboard


@perms.role_required("home.view")
def home(request):
    role = perms.user_role(request.user)
    if role == perms.CADET:
        data = cadet_dashboard(request.user)
        return render(request, "naryad/home_cadet.html", {"data": data, "fmt_day": fmt_day})
    data = staff_dashboard(request.user)
    fairness = stats.fairness_all(stats.Period()) if perms.can(request.user, "history.all") else []
    return render(request, "naryad/home_staff.html", {"data": data, "fairness": fairness})


class LoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


class PasswordChangeView(perms.RoleRequiredMixin, auth_views.PasswordChangeView):
    permission = "account.password_change"
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.user.must_change_password = False
        response = super().form_valid(form)
        messages.success(self.request, "Parolingiz almashtirildi.")
        return response


def permission_denied(request, exception=None):
    return render(request, "403.html", {"reason": str(exception or "")}, status=403)
