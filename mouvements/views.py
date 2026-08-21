from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Mouvement


@login_required
def liste(request):
    mouvements = Mouvement.objects.select_related("utilisateur").all()
    return render(request, "mouvements/liste.html", {"items": Paginator(mouvements, 30).get_page(request.GET.get("page"))})
