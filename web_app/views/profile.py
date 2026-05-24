from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from web_app.forms.profile_form import ProfileForm
from web_app.models import Identity


@login_required
def profile_view(request):
    if request.user.identity in (Identity.ADMIN, Identity.EMPLOYEE):
        return redirect("web_app:staff_orders")

    form = ProfileForm(instance=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("個人資料已更新"))
            return redirect("web_app:profile")

    return render(request, "profile.html", {"form": form})
