from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.crypto import get_random_string

from chutes.models import Chute
from panneaux.models import Panneau
from types_verres.models import Epaisseur, Teinte, TypeVerre
from .forms import DecoupeForm, PlanificationForm
from .services import Rectangle, appliquer_plan_panneau, compatibles, consume, consume_batch, planifier_panneau, previsualiser_utilisation_chute
from stock_panneaux.services import StockInsuffisantError, consommer_pour_planification


@permission_required("decoupes.plan_cut", raise_exception=True)
def creer(request):
    form = DecoupeForm(request.POST or None)
    suggestions = []
    if request.method == "POST" and form.is_valid():
        source = form.cleaned_data["chute"] or form.cleaned_data["panneau"]
        try:
            resultats = consume_batch(source, form.cleaned_data["lignes"], request.user, form.cleaned_data["emplacement"])
            messages.success(request, f"{len(resultats)} decoupe(s) enregistree(s).")
            return redirect("chutes:liste")
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, "decoupes/creer.html", {"form": form, "suggestions": suggestions})


def _specifications_plan(data, create=False):
    type_verre = data.get("materiau")
    if type_verre is None:
        if create:
            type_verre, _ = TypeVerre.objects.get_or_create(designation="Verre standard")
        else:
            type_verre = TypeVerre.objects.filter(designation="Verre standard").first()
    if create:
        epaisseur, _ = Epaisseur.objects.get_or_create(valeur=data["epaisseur"])
        teinte, _ = Teinte.objects.get_or_create(designation=data["teinte"].strip())
    else:
        epaisseur = Epaisseur.objects.filter(valeur=data["epaisseur"]).first()
        teinte = Teinte.objects.filter(designation=data["teinte"].strip()).first()
    return {"type_verre": type_verre, "epaisseur": epaisseur, "teinte": teinte}


def _creer_panneau(data):
    specifications = _specifications_plan(data, create=True)
    return Panneau.objects.create(
        reference=f"PLAN-{get_random_string(8).upper()}",
        longueur=data["longueur_panneau"],
        largeur=data["largeur_panneau"],
        **specifications,
    )


def _suggestions_chutes(demandes, specifications):
    """Compatible offcuts for every requested piece, in increasing waste order."""
    suggestions = []
    for index, (longueur, largeur) in enumerate(demandes):
        candidates = compatibles(longueur, largeur, **specifications)
        for chute in candidates:
            prevision = previsualiser_utilisation_chute(chute, longueur, largeur)
            chute.rotation_necessaire = prevision["rotation"]
            chute.restes_prevus = prevision["restes"]
        suggestions.append({
            "index": index,
            "longueur": longueur,
            "largeur": largeur,
            "candidates": candidates,
        })
    return suggestions


def _lire_affectations(request, suggestions):
    """Validate submitted selections and ensure that an offcut is used once only."""
    affectations = {}
    deja_choisies = set()
    for suggestion in suggestions:
        valeur = request.POST.get(f"chute_{suggestion['index']}")
        if not valeur:
            continue
        try:
            chute_id = int(valeur)
        except (TypeError, ValueError):
            raise ValueError("La chute selectionnee est invalide.")
        chute = next((item for item in suggestion["candidates"] if item.pk == chute_id), None)
        if chute is None:
            raise ValueError("La chute selectionnee n'est plus compatible ou n'est plus disponible.")
        if chute.pk in deja_choisies:
            raise ValueError("Une meme chute ne peut pas etre affectee a plusieurs pieces.")
        deja_choisies.add(chute.pk)
        affectations[suggestion["index"]] = chute
    return affectations


@permission_required("decoupes.plan_cut", raise_exception=True)
def planifier(request):
    chute_preselectionnee = None
    initial = {}
    chute_id = request.POST.get("chute_0") if request.method == "POST" else request.GET.get("chute")
    if chute_id:
        try:
            chute_preselectionnee = Chute.objects.select_related(
                "type_verre", "epaisseur", "teinte", "emplacement"
            ).get(pk=chute_id, etat=Chute.Etat.DISPONIBLE)
        except (Chute.DoesNotExist, ValueError):
            chute_preselectionnee = None

    if request.method == "GET" and chute_preselectionnee:
        longueur = request.GET.get("longueur", chute_preselectionnee.longueur)
        largeur = request.GET.get("largeur", chute_preselectionnee.largeur)
        initial = {
            "materiau": chute_preselectionnee.type_verre_id,
            "longueur_panneau": chute_preselectionnee.longueur,
            "largeur_panneau": chute_preselectionnee.largeur,
            "epaisseur": chute_preselectionnee.epaisseur.valeur,
            "teinte": chute_preselectionnee.teinte.designation,
            "emplacement": chute_preselectionnee.emplacement_id,
            "decoupes": f"{longueur} x {largeur}",
        }

    form = PlanificationForm(request.POST or None, initial=initial)
    plan = restes = None
    chute_principale = panneau_plan = None
    plans_chutes = []
    suggestions = []
    affectations = {}
    consommations_integrales = set()
    apercu_disponible = False

    if request.method == "POST" and form.is_valid():
        demandes = form.cleaned_data["decoupes"]
        specifications = _specifications_plan(form.cleaned_data)
        suggestions = _suggestions_chutes(demandes, specifications)
        try:
            affectations = _lire_affectations(request, suggestions)
            consommations_integrales = {
                index for index in affectations
                if request.POST.get(f"consommer_integralement_{index}") == "1"
            }
            for suggestion in suggestions:
                suggestion["selected_chute"] = affectations.get(suggestion["index"])
                suggestion["selected_id"] = getattr(suggestion["selected_chute"], "pk", None)
                suggestion["consommer_integralement"] = suggestion["index"] in consommations_integrales
            demandes_panneau = [demande for index, demande in enumerate(demandes) if index not in affectations]

            # Une chute sélectionnée est elle aussi une matière à découper : son
            # aperçu doit être aussi lisible que celui d'un panneau neuf.
            for index, chute in affectations.items():
                longueur, largeur = demandes[index]
                prevision = previsualiser_utilisation_chute(chute, longueur, largeur)
                plans_chutes.append({
                    "chute": chute,
                    "longueur": longueur,
                    "largeur": largeur,
                    "plan_longueur": largeur if prevision["rotation"] else longueur,
                    "plan_largeur": longueur if prevision["rotation"] else largeur,
                    "rotation": prevision["rotation"],
                    "restes": [] if index in consommations_integrales else prevision["restes"],
                    "consommer_integralement": index in consommations_integrales,
                })
            if request.POST.get("action") == "valider":
                with transaction.atomic():
                    emplacement = form.cleaned_data["emplacement"]
                    restes_depuis_chutes = []
                    details_chutes = []
                    for index, chute in affectations.items():
                        longueur, largeur = demandes[index]
                        _, nouveaux_restes = consume(
                            chute, longueur, largeur, request.user, emplacement,
                            stocker_restes=index not in consommations_integrales,
                        )
                        if index in consommations_integrales:
                            details_chutes.append(
                                f"{chute.numero} entièrement consommée après la coupe {longueur} × {largeur} mm"
                            )
                        else:
                            restes_depuis_chutes.extend(nouveaux_restes)
                            details_chutes.append(
                                f"{chute.numero} : coupe {longueur} × {largeur} mm, "
                                f"{len(nouveaux_restes)} reste(s) stocké(s)"
                            )

                    chutes = []
                    if demandes_panneau:
                        panneau = _creer_panneau(form.cleaned_data)
                        consommer_pour_planification(
                            longueur=panneau.longueur, largeur=panneau.largeur,
                            materiau=panneau.type_verre, epaisseur=panneau.epaisseur.valeur,
                            teinte=panneau.teinte.designation, panneau_utilise=panneau,
                            utilisateur=request.user,
                        )
                        _, chutes = appliquer_plan_panneau(panneau, demandes_panneau, emplacement, request.user)
                nouvelles_chutes = len(restes_depuis_chutes) + len(chutes)
                details_stock = [
                    f"{reste.longueur} × {reste.largeur} mm" for reste in restes_depuis_chutes
                ] + [f"{chute.longueur} × {chute.largeur} mm" for chute in chutes]
                parties = ["Découpe enregistrée."]
                if details_chutes:
                    parties.append("Chutes utilisées : " + " ; ".join(details_chutes) + ".")
                if demandes_panneau:
                    parties.append(f"Panneau neuf : {len(demandes_panneau)} pièce(s) découpée(s).")
                if nouvelles_chutes:
                    parties.append(
                        f"{nouvelles_chutes} nouvelle(s) chute(s) stockée(s) à {emplacement.code} : "
                        + ", ".join(details_stock) + "."
                    )
                else:
                    parties.append("Aucune nouvelle chute n’a été stockée.")
                messages.success(request, " ".join(parties))
                return redirect("chutes:liste")

            apercu_disponible = True
            # Ne pas calculer un « panneau » vide : lorsque toutes les pièces
            # viennent de chutes, ce calcul renvoyait la chute source entière
            # comme reste à stocker.
            if demandes_panneau:
                panneau_plan = Rectangle(form.cleaned_data["longueur_panneau"], form.cleaned_data["largeur_panneau"])
                plan, restes = planifier_panneau(panneau_plan.longueur, panneau_plan.largeur, demandes_panneau)
                chute_principale = max(restes, key=lambda chute: chute.longueur * chute.largeur, default=None)
            else:
                plan, restes = [], []
        except StockInsuffisantError as exc:
            form.add_error(None, str(exc))
        except ValueError as exc:
            form.add_error(None, str(exc))

    return render(request, "decoupes/planifier.html", {
        "form": form,
        "plan": plan,
        "restes": restes,
        "panneau_plan": panneau_plan,
        "chute_principale": chute_principale,
        "suggestions": suggestions,
        "affectations": affectations,
        "apercu_disponible": apercu_disponible,
        "chute_preselectionnee": chute_preselectionnee,
        "plans_chutes": plans_chutes,
    })
