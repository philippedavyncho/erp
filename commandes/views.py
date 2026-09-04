from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Commande
from .services import changer_statut
@permission_required("commandes.view_commande",raise_exception=True)
def liste(request): return render(request,"commandes/liste.html",{"items":Commande.objects.select_related("client").all()})
@permission_required("commandes.view_commande",raise_exception=True)
def detail(request,pk): return render(request,"commandes/detail_v2.html",{"commande":get_object_or_404(Commande.objects.select_related("client","devis"),pk=pk)})
@permission_required("commandes.validate_commande",raise_exception=True)
def valider(request,pk):
    commande=get_object_or_404(Commande,pk=pk)
    if request.method=="POST":
        changer_statut(commande,Commande.Statut.VALIDEE,request.user); messages.success(request,"Commande validée pour la production."); return redirect("commandes:detail",pk=pk)
    return render(request,"commandes/confirm.html",{"commande":commande})


@permission_required("commandes.manage_commande", raise_exception=True)
def statut(request, pk, statut):
    commande = get_object_or_404(Commande, pk=pk)
    if request.method == "POST":
        try:
            changer_statut(commande, statut, request.user, request.POST.get("commentaire", ""))
            messages.success(request, "Statut de la commande mis à jour.")
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect("commandes:detail", pk=pk)


@permission_required("commandes.view_commande", raise_exception=True)
def bon_livraison(request, pk):
    commande = get_object_or_404(Commande.objects.select_related("client", "devis").prefetch_related("lignes"), pk=pk)
    if commande.statut not in (Commande.Statut.PRETE, Commande.Statut.LIVREE):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Le bon de livraison est disponible lorsque la commande est prête.")
    return render(request, "commandes/bon_livraison.html", {"commande": commande})
