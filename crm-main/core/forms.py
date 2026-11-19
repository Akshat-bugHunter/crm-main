from django import forms
from .models import Agent, Property, Lead, Deal


class AgentForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    username = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = Agent
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users that are not already assigned to an Agent
        from django.contrib.auth.models import User
        assigned_user_ids = Agent.objects.values_list("user_id", flat=True)
        if self.instance and self.instance.pk:
            assigned_user_ids = assigned_user_ids.exclude(pk=self.instance.pk)
        self.fields["user"].queryset = User.objects.exclude(id__in=assigned_user_ids)
        self.fields["user"].required = False
    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        from django.contrib.auth.models import User

        if not user:
            if not username:
                self.add_error("username", "Please provide a username or select an existing user.")
            elif User.objects.filter(username=username).exists():
                self.add_error("username", "This username is already taken.")
            if not password:
                self.add_error("password", "Password is required when creating a new user.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        from django.contrib.auth.models import User

        if not instance.user_id:
            user = User.objects.create_user(
                username=self.cleaned_data["username"],
                email=self.cleaned_data.get("email", ""),
                password=self.cleaned_data["password"],
                first_name=self.cleaned_data.get("first_name", ""),
                last_name=self.cleaned_data.get("last_name", ""),
            )
            instance.user = user

        if commit:
            instance.save()
        return instance


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
