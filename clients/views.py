from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ClientForm
from .models import Client
@permission_required("clients.view_client", raise_exception=True)
def liste(request):
    q=request.GET.get("q",""); items=Client.objects.filter(Q(nom__icontains=q)|Q(reference__icontains=q)|Q(ville__icontains=q)) if q else Client.objects.all()
    return render(request,"clients/liste.html",{"items":items,"q":q})
@permission_required("clients.manage_client", raise_exception=True)
def creer(request):
    form=ClientForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        client=form.save(commit=False); client.cree_par=request.user; client.save(); return redirect("clients:detail",pk=client.pk)
    return render(request,"form.html",{"form":form,"titre":"Nouveau client"})
@permission_required("clients.view_client", raise_exception=True)
def detail(request,pk): return render(request,"clients/detail.html",{"client":get_object_or_404(Client,pk=pk)})
