from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404,redirect,render
from commandes.models import Commande
from .models import EtapeProduction,FicheProduction
from .services import changer_etape,creer_fiche
@permission_required("production.view_ficheproduction",raise_exception=True)
def liste(request): return render(request,"production/liste.html",{"items":FicheProduction.objects.select_related("commande","commande__client")})
@permission_required("production.manage_production",raise_exception=True)
def creer(request,commande_pk):
    commande=get_object_or_404(Commande,pk=commande_pk)
    if request.method=="POST":
        try: fiche=creer_fiche(commande,request.user); return redirect("production:detail",pk=fiche.pk)
        except ValueError as exc: messages.error(request,str(exc))
    return redirect("commandes:detail",pk=commande.pk)
@permission_required("production.view_ficheproduction",raise_exception=True)
def detail(request,pk): return render(request,"production/detail.html",{"fiche":get_object_or_404(FicheProduction.objects.select_related("commande"),pk=pk)})
def etape(request,pk,statut):
    item=get_object_or_404(EtapeProduction,pk=pk)
    permission = "production.control_quality" if item.type == EtapeProduction.Type.CONTROLE else "production.operate_production"
    if not request.user.has_perm(permission):
        raise PermissionDenied
    if item.operateur_id and item.operateur_id != request.user.id:
        raise PermissionDenied
    if request.method=="POST" and statut in dict(EtapeProduction.Statut.choices): changer_etape(item,statut,request.user,request.POST.get("commentaire",""),request.POST.get("probleme",""))
    return redirect("production:detail",pk=item.piece.fiche_id)
