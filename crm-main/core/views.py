from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Agent, Property, Lead, Deal
from .forms import AgentForm, DealForm, LeadForm, PropertyForm, EditAgentForm
import json, re
from decimal import Decimal


# Create your views here.
def home(request):
    properties_count = Property.objects.count()
    closed_deals_count = Deal.objects.filter(status=Deal.DealStatus.DONE).count()
    leads_count = Lead.objects.count()
    agents_count = Agent.objects.count()
    recent_leads = Lead.objects.all().order_by("-id")[:5]
    recent_deals = Deal.objects.all().order_by("-id")[:5]
    context = {
        "properties_count": properties_count,
        "closed_deals_count": closed_deals_count,
        "leads_count": leads_count,
        "agents_count": agents_count,
        "leads": recent_leads,
        "recent_deals": recent_deals,
    }
    return render(request, "home.html", context)


def agents(request):
    form = AgentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("agents")

    queryset = Agent.objects.all()
    context = {"agents": queryset, "form": form if request.method == "POST" else AgentForm()}
    return render(request, "pages/agents.html", context)


def properties(request):
    form = PropertyForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("properties")

    queryset = Property.objects.all()
    context = {"properties": queryset, "form": form if request.method == "POST" else PropertyForm()}
    return render(request, "pages/properties.html", context)


def leads(request):
    form = LeadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("leads")

    queryset = Lead.objects.all()
    context = {"leads": queryset, "form": form if request.method == "POST" else LeadForm()}
    return render(request, "pages/leads.html", context)


def deals(request):
    form = DealForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("deals")

    queryset = Deal.objects.all()
    context = {"deals": queryset, "form": form if request.method == "POST" else DealForm()}
    return render(request, "pages/deals.html", context)


def edit_agent(request, id):
    instance = get_object_or_404(Agent, id=id)
    form = EditAgentForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("agents")

    context = {"editform": form, "id": id}
    return render(request, "pages/editagent.html", context)


def edit_property(request, id):
    instance = get_object_or_404(Property, id=id)
    form = PropertyForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("properties")

    context = {"editform": form, "id": id}
    return render(request, "pages/editproperty.html", context)


def edit_lead(request, id):
    instance = get_object_or_404(Lead, id=id)
    form = LeadForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("leads")

    context = {"editform": form, "id": id}
    return render(request, "pages/editleads.html", context)


def edit_deal(request, id):
    instance = get_object_or_404(Deal, id=id)
    form = DealForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("deals")

    context = {"editform": form, "id": id}
    return render(request, "pages/editdeal.html", context)


# ── AI Chat ────────────────────────────────────────────────────
def _fmt_currency(val):
    """Format a Decimal / float as $1,234,567"""
    try:
        return f"${int(val):,}"
    except (TypeError, ValueError):
        return str(val)


def _build_crm_context():
    agents = Agent.objects.select_related("user").all()
    properties = Property.objects.select_related("listing_agent__user").all()
    leads = Lead.objects.select_related("assigned_agent__user").all()
    deals = Deal.objects.select_related("lead", "property").all()
    return {
        "agents": agents,
        "properties": properties,
        "leads": leads,
        "deals": deals,
        "counts": {
            "agents": agents.count(),
            "properties": properties.count(),
            "leads": leads.count(),
            "deals": deals.count(),
            "available_properties": properties.filter(status="available").count(),
            "closed_deals": deals.filter(status="done").count(),
            "new_leads": leads.filter(status="new").count(),
        },
    }


def _answer(message, ctx):
    msg = message.lower().strip()
    c = ctx["counts"]

    # Help
    if msg in ("help", "?", "commands"):
        return (
            "Here's what I can help with:\n"
            "• **summary / dashboard** – quick CRM snapshot\n"
            "• **leads** – list active leads\n"
            "• **new leads** – leads with status 'New'\n"
            "• **deals** – list all deals\n"
            "• **pending deals** – deals still pending\n"
            "• **properties** – list properties\n"
            "• **agents / top agents** – agent info\n"
            "• **stats** – key numbers\n"
            "Type any of the above to get started!"
        )

    # Summary / dashboard
    if re.search(r"summar|dashboard|overview|snapshot", msg):
        return (
            f"📊 **CRM Snapshot**\n"
            f"• **{c['agents']}** agents registered\n"
            f"• **{c['properties']}** properties ({c['available_properties']} available)\n"
            f"• **{c['leads']}** leads ({c['new_leads']} new)\n"
            f"• **{c['deals']}** deals ({c['closed_deals']} closed)"
        )

    # Stats
    if re.search(r"\bstats?\b|\bnumbers?\b|\bmetrics?\b", msg):
        total_revenue = sum(d.amount for d in ctx["deals"].filter(status="done"))
        return (
            f"📈 **Key Metrics**\n"
            f"• Total revenue (closed): **{_fmt_currency(total_revenue)}**\n"
            f"• Properties listed: **{c['properties']}**\n"
            f"• Conversion: **{c['closed_deals']}** / **{c['deals']}** deals closed\n"
            f"• Active leads: **{c['leads'] - ctx['leads'].filter(status__in=['done','lost']).count()}**"
        )

    # Leads
    if re.search(r"\bnew leads?\b", msg):
        new = ctx["leads"].filter(status="new")
        if not new.exists():
            return "No leads with status **New** right now."
        lines = [f"🆕 **New Leads** ({new.count()})"]
        for l in new[:10]:
            lines.append(f"• **{l.full_name}** – {l.preferred_location}, budget {_fmt_currency(l.min_budget)}–{_fmt_currency(l.max_budget)}")
        return "\n".join(lines)

    if re.search(r"\bleads?\b", msg):
        qs = ctx["leads"]
        if not qs.exists():
            return "No leads in the system yet."
        lines = [f"👥 **All Leads** ({qs.count()})"]
        for l in qs[:10]:
            lines.append(f"• **{l.full_name}** – *{l.get_status_display()}* – {l.preferred_location}")
        return "\n".join(lines)

    # Deals
    if re.search(r"pending deal", msg):
        pending = ctx["deals"].filter(status="pending")
        if not pending.exists():
            return "No pending deals right now. 🎉"
        lines = [f"⏳ **Pending Deals** ({pending.count()})"]
        for d in pending[:10]:
            lines.append(f"• **{d.property.title}** → {d.lead.full_name} – {_fmt_currency(d.amount)}")
        return "\n".join(lines)

    if re.search(r"\bdeals?\b", msg):
        qs = ctx["deals"]
        if not qs.exists():
            return "No deals recorded yet."
        lines = [f"🤝 **All Deals** ({qs.count()})"]
        for d in qs[:10]:
            lines.append(f"• **{d.property.title}** → {d.lead.full_name} – {_fmt_currency(d.amount)} (*{d.get_status_display()}*)")
        return "\n".join(lines)

    # Properties
    if re.search(r"\bproperties\b|\blistings?\b", msg):
        qs = ctx["properties"]
        if not qs.exists():
            return "No properties listed yet."
        lines = [f"🏠 **Properties** ({qs.count()})"]
        for p in qs[:10]:
            lines.append(f"• **{p.title}** – {p.city}, {_fmt_currency(p.price)} (*{p.get_status_display()}*)")
        return "\n".join(lines)

    # Agents
    if re.search(r"\bagents?\b|\btop agents?\b|\bteam\b", msg):
        qs = ctx["agents"]
        if not qs.exists():
            return "No agents registered yet."
        lines = [f"👤 **Agents** ({qs.count()})"]
        for a in qs[:10]:
            lines.append(f"• **{a.user.get_full_name() or a.user.username}** – {a.region}, target {_fmt_currency(a.monthly_target)}")
        return "\n".join(lines)

    # Fallback
    return (
        "I'm not sure how to answer that. Try:\n"
        "• **summary** – CRM snapshot\n"
        "• **leads** / **deals** / **properties** / **agents**\n"
        "• **stats** – key numbers\n"
        "• **help** – full command list"
    )


@csrf_exempt
@require_POST
def ai_chat(request):
    try:
        body = json.loads(request.body)
        message = body.get("message", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"reply": "Invalid request."}, status=400)

    if not message:
        return JsonResponse({"reply": "Please type a message."})

    ctx = _build_crm_context()
    reply = _answer(message, ctx)
    return JsonResponse({"reply": reply})
