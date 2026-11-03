from django import forms
from .models import Agent, Property, Lead, Deal


class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = "__all__"


class EditAgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        exclude = ["user"]


class PropertyForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Property
        fields = "__all__"


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = "__all__"


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = "__all__"
        widgets = {
            "expected_closing_date": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "actual_closing_date": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
        }
