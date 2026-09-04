from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from decoupes.models import Decoupe
from decoupes.services import compatibles, consume, previsualiser_utilisation_chute
from .forms import (ConfirmationChuteForm, CorrectionChuteForm, DeplacementChuteForm,
                    RebutChuteForm, RechercheChuteForm, ReservationChuteForm)
from .models import Chute
from .services import (annuler_reservation, corriger, deplacer, mettre_au_rebut,
                       reserver, utiliser)


@login_required
def liste(request):
    qs = Chute.objects.select_related("emplacement", "type_verre", "epaisseur", "teinte", "modifie_par")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(numero__icontains=q) | Q(emplacement__code__icontains=q) | Q(type_verre__designation__icontains=q))
    if not request.GET.get("etat"):
        qs = qs.filter(etat=Chute.Etat.DISPONIBLE)
    for field in ("etat", "type_verre", "epaisseur", "teinte", "emplacement"):
        if value := request.GET.get(field):
            qs = qs.filter(**{f"{field}_id" if field != "etat" else field: value})
    if longueur := request.GET.get("longueur"):
        qs = qs.filter(longueur__gte=longueur)
    if largeur := request.GET.get("largeur"):
        qs = qs.filter(largeur__gte=largeur)
    return render(request, "chutes/liste.html", {
        "items": Paginator(qs.order_by("-modifie_le"), 20).get_page(request.GET.get("page")),
        "q": q, "etats": Chute.Etat.choices,
    })


@login_required
def detail(request, pk):
    chute = get_object_or_404(Chute.objects.select_related("emplacement", "type_verre", "epaisseur", "teinte", "modifie_par"), pk=pk)
    historique = chute.historique.select_related("utilisateur", "ancien_emplacement", "nouvel_emplacement")
    return render(request, "chutes/detail.html", {"chute": chute, "historique": historique})


@permission_required("chutes.move_chute", raise_exception=True)
def deplacer_chute(request, pk):
    chute = get_object_or_404(Chute, pk=pk)
    form = DeplacementChuteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            deplacer(chute.pk, form.cleaned_data["emplacement"], request.user, form.cleaned_data["commentaire"])
            messages.success(request, "Déplacement enregistré dans l'historique.")
            return redirect("chutes:detail", pk=pk)
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "chutes/action_form.html", {"form": form, "chute": chute, "titre": "Déplacer la chute", "actuel": chute.emplacement})


@permission_required("chutes.correct_chute", raise_exception=True)
def corriger_chute(request, pk):
    chute = get_object_or_404(Chute, pk=pk)
    form = CorrectionChuteForm(request.POST or None, instance=chute)
    if request.method == "POST" and form.is_valid():
        try:
            corriger(chute.pk, form.cleaned_data, request.user, form.cleaned_data["commentaire"])
            messages.success(request, "Correction enregistrée dans l'historique.")
            return redirect("chutes:detail", pk=pk)
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "chutes/action_form.html", {"form": form, "chute": chute, "titre": "Corriger la chute"})


@permission_required("chutes.reserve_chute", raise_exception=True)
def reserver_chute(request, pk):
    chute = get_object_or_404(Chute, pk=pk)
    form = ReservationChuteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            reserver(chute.pk, form.cleaned_data["reference"], request.user, form.cleaned_data["commentaire"])
            messages.success(request, "Chute réservée.")
            return redirect("chutes:detail", pk=pk)
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "chutes/action_form.html", {"form": form, "chute": chute, "titre": "Réserver la chute"})


@permission_required("chutes.reserve_chute", raise_exception=True)
def annuler_reservation_chute(request, pk):
    chute = get_object_or_404(Chute, pk=pk)
    form = ConfirmationChuteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            annuler_reservation(chute.pk, request.user, form.cleaned_data["commentaire"])
            messages.success(request, "Réservation annulée.")
            return redirect("chutes:detail", pk=pk)
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "chutes/action_form.html", {"form": form, "chute": chute, "titre": "Annuler la réservation", "confirmation": True})


@permission_required("chutes.use_chute", raise_exception=True)
def utiliser_chute(request, pk):
    chute = get_object_or_404(Chute, pk=pk)
    form = ConfirmationChuteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            utiliser(chute.pk, request.user, form.cleaned_data["commentaire"])
            messages.success(request, "Chute déclarée utilisée.")
            return redirect("chutes:detail", pk=pk)
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "chutes/action_form.html", {"form": form, "chute": chute, "titre": "Déclarer la chute utilisée", "confirmation": True})


@permission_required("chutes.discard_chute", raise_exception=True)
def rebut_chute(request, pk):
    chute = get_object_or_404(Chute, pk=pk)
    form = RebutChuteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            mettre_au_rebut(chute.pk, form.cleaned_data["motif"], request.user, form.cleaned_data["commentaire"])
            messages.success(request, "Chute mise au rebut et conservée dans l'historique.")
            return redirect("chutes:detail", pk=pk)
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "chutes/action_form.html", {"form": form, "chute": chute, "titre": "Mettre la chute au rebut", "confirmation": True})


@login_required
def entrees(request):
    return render(request, "chutes/mouvements.html", {"titre": "Entrées de chutes", "type_page": "entrees", "chutes": Chute.objects.all()})


@login_required
def sorties(request):
    decoupes = Decoupe.objects.filter(chute_source__isnull=False).select_related("chute_source", "utilisateur")
    return render(request, "chutes/mouvements.html", {"titre": "Sorties de chutes", "type_page": "sorties", "decoupes": decoupes})


@login_required
def rechercher(request):
    form = RechercheChuteForm(request.GET or None)
    resultats = []
    if form.is_valid():
        specs = {key: value for key, value in form.cleaned_data.items() if key not in ("longueur", "largeur") and value is not None}
        resultats = compatibles(form.cleaned_data["longueur"], form.cleaned_data["largeur"], **specs)
        for chute in resultats:
            chute.rotation_necessaire = previsualiser_utilisation_chute(chute, form.cleaned_data["longueur"], form.cleaned_data["largeur"])["rotation"]
    return render(request, "chutes/rechercher.html", {"form": form, "resultats": resultats})


@permission_required("decoupes.plan_cut", raise_exception=True)
def utiliser_depuis_recherche(request, chute_id):
    if request.method != "POST":
        return redirect("chutes:rechercher")
    form = RechercheChuteForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Les dimensions de découpe sont invalides.")
        return redirect("chutes:rechercher")
    chute = get_object_or_404(Chute, pk=chute_id, etat=Chute.Etat.DISPONIBLE)
    if chute not in compatibles(form.cleaned_data["longueur"], form.cleaned_data["largeur"], epaisseur=form.cleaned_data["epaisseur"], teinte=form.cleaned_data["teinte"]):
        messages.error(request, "Cette chute n'est plus compatible avec la pièce demandée.")
        return redirect("chutes:rechercher")
    try:
        _, restes = consume(chute, form.cleaned_data["longueur"], form.cleaned_data["largeur"], request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("chutes:rechercher")
    messages.success(request, f"Découpe réalisée depuis {chute.numero}. {len(restes)} chute(s) créée(s).")
    return redirect("chutes:liste")
