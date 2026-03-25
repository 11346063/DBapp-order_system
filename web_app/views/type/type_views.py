from django.shortcuts import render, get_object_or_404, redirect
from ...forms.type_form import TypeForm
from ...models.type import Type
from django.contrib.auth.decorators import login_required
from django.utils import timezone



def typeCreate(request):
    form = TypeForm()

    if request.method == "POST":
        form = TypeForm(request.POST)
        if form.is_valid():
            form.save()
        
    return render(request, "type/create.html", {"form": form})