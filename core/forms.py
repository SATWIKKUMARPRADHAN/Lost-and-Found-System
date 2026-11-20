from django import forms
from django.contrib.auth.models import User
from .models import Item, Claim

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create secure password (min 6 characters)'
        }),
        label="Password"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        }),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. s_kumar'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. student@campus.edu'}),
        }
        help_texts = {
            'username': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("A valid campus email is required.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ItemReportForm(forms.ModelForm):
    verification_answer = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Green sticker with initials AK on back corner'
        }),
        label="Expected Verification Answer (Secret)",
        help_text="Will be cryptographically hashed. Never visible to students."
    )

    class Meta:
        model = Item
        fields = [
            'item_type',
            'title',
            'category',
            'location',
            'incident_date',
            'description',
            'image',
            'verification_question',
        ]
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Sony WH-1000XM4 Headphones in Black Case'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Library 2nd Floor Silent Study Area'}),
            'incident_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe general appearance, brand, color without revealing the secret detail.'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'verification_question': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. What keychain or decal is attached to this item?'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        item_type = cleaned_data.get('item_type')
        v_question = cleaned_data.get('verification_question')
        v_answer = cleaned_data.get('verification_answer')

        # When reporting a FOUND item, require verification question and answer
        if item_type == 'FOUND':
            if not v_question or not v_question.strip():
                self.add_error('verification_question', 'Please provide a verification question so the genuine owner can identify it.')
            if not v_answer or not v_answer.strip():
                self.add_error('verification_answer', 'Please provide the expected verification answer. This will be stored as a secure hash.')
        return cleaned_data

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user:
            instance.reported_by = user

        raw_answer = self.cleaned_data.get('verification_answer')
        if raw_answer and instance.item_type == 'FOUND':
            instance.set_verification_answer(raw_answer)

        if commit:
            instance.save()
        return instance


class ClaimVerificationForm(forms.Form):
    verification_answer = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your verification answer'
        }),
        label="Your Answer",
        help_text="Case-insensitive match checked against the cryptographic hash."
    )
    claim_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Provide any additional ownership evidence (serial number, distinctive marks, proof of purchase).'
        }),
        label="Additional Details / Proof (Optional)"
    )
