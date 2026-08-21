from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Panneau
from .forms import PanneauForm
@login_required
def liste(request): return render(request,"panneaux/liste.html",{"items":Panneau.objects.all()})
@login_required
def creer(request):
    form=PanneauForm(request.POST or None)
    if form.is_valid(): form.save(); return redirect("panneaux:liste")
    return render(request,"form.html",{"form":form,"titre":"Nouveau panneau"})
