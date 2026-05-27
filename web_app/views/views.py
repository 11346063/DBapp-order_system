from django.shortcuts import render
from ..decorators import admin_required
from ..forms.type_form import TypeForm


@admin_required
def typeCreate(request):
    form = TypeForm()

    if request.method == "POST":
        form = TypeForm(request.POST)
        if form.is_valid():
            form.save()

    return render(request, "type/create.html", {"form": form})
