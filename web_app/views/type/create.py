from django.shortcuts import render
from ...forms.type_form import TypeForm


def announcementCreate(request):
    form = TypeForm()

    if request.method == "POST":
        form = TypeForm(request.POST)
        if form.is_valid():
            form.save()

    return render(request, "type/create.html", {"form": form})
