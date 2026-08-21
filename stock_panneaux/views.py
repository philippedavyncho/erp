from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReceptionStockForm, StockGrandPanneauForm
from .models import MouvementStockGrandPanneau, PlanificationStock, StockGrandPanneau
from .services import annuler_planification, enregistrer_entree


@permission_required("stock_panneaux.view_stockgrandpanneau", raise_exception=True)
def liste(request):
    panneaux = StockGrandPanneau.objects.select_related("materiau", "epaisseur", "teinte").all()
    recherche = request.GET.get("q", "").strip()
    if recherche:
        panneaux = panneaux.filter(Q(reference__icontains=recherche) | Q(materiau__designation__icontains=recherche))
    if request.GET.get("sous_seuil"):
        panneaux = [p for p in panneaux if p.sous_seuil]
    return render(request, "stock_panneaux/liste.html", {"items": panneaux, "q": recherche})


@permission_required("stock_panneaux.view_stockgrandpanneau", raise_exception=True)
def entrees(request):
    mouvements = MouvementStockGrandPanneau.objects.filter(type=MouvementStockGrandPanneau.Type.ENTREE).select_related("panneau", "utilisateur")
    return render(request, "stock_panneaux/mouvements.html", {"titre": "Entrées de stock", "description": "Réceptions, ajouts manuels et retours en stock.", "mouvements": mouvements, "type_page": "entrees"})


@permission_required("stock_panneaux.view_stockgrandpanneau", raise_exception=True)
def sorties(request):
    mouvements = MouvementStockGrandPanneau.objects.filter(type=MouvementStockGrandPanneau.Type.SORTIE).select_related("panneau", "utilisateur")
    return render(request, "stock_panneaux/mouvements.html", {"titre": "Sorties de stock", "description": "Panneaux utilisés lors des planifications de découpe.", "mouvements": mouvements, "type_page": "sorties"})


@permission_required("stock_panneaux.manage_stock", raise_exception=True)
def creer(request):
    form = StockGrandPanneauForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        panneau = form.save()
        if panneau.quantite_en_stock:
            # L'entrée initiale fait partie de l'historique dès la création.
            quantite_initiale = panneau.quantite_en_stock
            panneau.quantite_en_stock = 0
            panneau.save(update_fields=["quantite_en_stock", "date_modification"])
            enregistrer_entree(panneau, quantite_initiale, utilisateur=request.user)
        messages.success(request, "Grand panneau ajouté au stock.")
        return redirect("stock_panneaux:liste")
    return render(request, "form.html", {"form": form, "titre": "Ajouter un grand panneau"})


@permission_required("stock_panneaux.manage_stock", raise_exception=True)
def receptionner(request, pk):
    """Ajoute des panneaux à une référence existante avec mouvement obligatoire."""
    panneau = get_object_or_404(StockGrandPanneau, pk=pk)
    form = ReceptionStockForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        enregistrer_entree(
            panneau,
            form.cleaned_data["quantite"],
            origine=form.cleaned_data["origine"],
            utilisateur=request.user,
        )
        messages.success(request, "Réception enregistrée dans l'historique du stock.")
        return redirect("stock_panneaux:liste")
    return render(request, "form.html", {
        "form": form,
        "titre": f"Réception — {panneau.reference}",
    })


@permission_required("stock_panneaux.manage_stock", raise_exception=True)
def modifier(request, pk):
    panneau = get_object_or_404(StockGrandPanneau, pk=pk)
    form = StockGrandPanneauForm(request.POST or None, instance=panneau)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Grand panneau modifié.")
        return redirect("stock_panneaux:liste")
    return render(request, "form.html", {"form": form, "titre": "Modifier le grand panneau"})


@permission_required("stock_panneaux.manage_stock", raise_exception=True)
def supprimer(request, pk):
    panneau = get_object_or_404(StockGrandPanneau, pk=pk)
    if request.method == "POST":
        try:
            panneau.delete()
            messages.success(request, "Grand panneau supprimé.")
        except Exception:
            messages.error(request, "Ce panneau possède déjà un historique et ne peut pas être supprimé.")
        return redirect("stock_panneaux:liste")
    return render(request, "stock_panneaux/confirmer_suppression.html", {"panneau": panneau})


@permission_required("stock_panneaux.view_stockgrandpanneau", raise_exception=True)
def historique(request):
    panneau_id = request.GET.get("panneau")
    mouvements = MouvementStockGrandPanneau.objects.select_related("panneau", "utilisateur")
    planifications = PlanificationStock.objects.select_related("panneau_stock", "utilisateur").all()
    if panneau_id:
        mouvements = mouvements.filter(panneau_id=panneau_id)
        planifications = planifications.filter(panneau_stock_id=panneau_id)
    return render(request, "stock_panneaux/historique.html", {
        "mouvements": mouvements,
        "planifications": planifications,
        "panneaux": StockGrandPanneau.objects.order_by("reference"),
        "panneau_selectionne": panneau_id,
    })


@permission_required("stock_panneaux.manage_stock", raise_exception=True)
def annuler(request, pk):
    planification = get_object_or_404(PlanificationStock, pk=pk)
    if request.method == "POST":
        try:
            annuler_planification(planification, request.user)
            messages.success(request, "Planification annulée : le panneau a été réajouté au stock.")
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect("stock_panneaux:historique")
