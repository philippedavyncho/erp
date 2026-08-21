from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from chutes.models import Chute, MouvementChute
from decoupes.models import Decoupe
from mouvements.models import Mouvement
from panneaux.models import Panneau
from stock_panneaux.models import MouvementStockGrandPanneau, StockGrandPanneau


def _surface_decoupes(decoupes):
    return sum((Decimal(item.longueur) * Decimal(item.largeur) / Decimal(1_000_000) for item in decoupes), Decimal())


@login_required
def index(request):
    today = timezone.localdate()
    decoupes_today = list(Decoupe.objects.filter(cree_le__date=today))
    stock = list(StockGrandPanneau.objects.select_related("materiau"))
    stock_total = sum(item.quantite_en_stock for item in stock)
    low_stock = [item for item in stock if item.sous_seuil]
    available_offcuts = Chute.objects.filter(etat=Chute.Etat.DISPONIBLE)
    offcut_surface = available_offcuts.aggregate(total=Sum("surface"))["total"] or Decimal()
    reusable_offcuts = available_offcuts.filter(surface__gte=Decimal("0.10")).count()
    cut_surface = _surface_decoupes(decoupes_today)
    waste_surface = Chute.objects.filter(etat=Chute.Etat.REBUT).aggregate(total=Sum("surface"))["total"] or Decimal()
    yield_percent = int(cut_surface * 100 / (cut_surface + waste_surface)) if cut_surface + waste_surface else 0

    stock_by_glass = list(
        StockGrandPanneau.objects.values("materiau__designation")
        .annotate(quantity=Sum("quantite_en_stock"))
        .order_by("materiau__designation")
    )
    maximum = max((row["quantity"] for row in stock_by_glass), default=1)
    for row in stock_by_glass:
        row["percent"] = max(8, int(row["quantity"] * 100 / maximum)) if row["quantity"] else 0

    recent_activity = []
    for movement in Mouvement.objects.select_related("utilisateur")[:5]:
        recent_activity.append({"date": movement.date, "label": movement.action.replace("_", " ").title(), "detail": movement.objet, "kind": "movement"})
    for movement in MouvementStockGrandPanneau.objects.select_related("panneau", "utilisateur")[:5]:
        recent_activity.append({"date": movement.date, "label": movement.get_type_display(), "detail": f"{movement.quantite} × {movement.panneau.reference}", "kind": movement.type.lower()})
    for cut in Decoupe.objects.select_related("panneau", "chute_source")[:5]:
        source = cut.panneau.reference if cut.panneau else cut.chute_source.numero if cut.chute_source else "stock"
        recent_activity.append({"date": cut.cree_le, "label": "Découpe terminée", "detail": f"{cut.longueur} × {cut.largeur} mm · {source}", "kind": "cut"})
    recent_activity.sort(key=lambda item: item["date"], reverse=True)

    return render(request, "dashboard.html", {
        "stock_total": stock_total,
        "low_stock": low_stock,
        "decoupes_today": len(decoupes_today),
        "offcut_count": available_offcuts.count(),
        "reserved_offcuts": Chute.objects.filter(etat=Chute.Etat.RESERVEE).count(),
        "used_offcuts": Chute.objects.filter(etat=Chute.Etat.UTILISEE).count(),
        "discarded_offcuts": Chute.objects.filter(etat=Chute.Etat.REBUT).count(),
        "recent_moves": MouvementChute.objects.filter(action=MouvementChute.Action.DEPLACEMENT).count(),
        "recent_corrections": MouvementChute.objects.filter(action=MouvementChute.Action.CORRECTION).count(),
        "waste_by_reason": MouvementChute.objects.filter(action=MouvementChute.Action.REBUT).values("motif").annotate(total=Count("id")).order_by("-total")[:3],
        "alert_count": len(low_stock),
        "stock_by_glass": stock_by_glass,
        "cut_surface": cut_surface,
        "offcut_surface": offcut_surface,
        "reusable_offcuts": reusable_offcuts,
        "waste_surface": waste_surface,
        "yield_percent": yield_percent,
        "recent_activity": recent_activity[:6],
    })
