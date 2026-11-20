from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('ELECTRONICS', 'Electronics & Gadgets'),
        ('BOOKS', 'Books, Notebooks & Stationary'),
        ('ID_CARDS', 'Cards, IDs & Wallets'),
        ('CLOTHING', 'Clothing, Bags & Accessories'),
        ('KEYS', 'Keys & Keychain Sets'),
        ('JEWELRY', 'Watches & Jewelry'),
        ('BOTTLES', 'Bottles, Umbrellas & Personal Gear'),
        ('OTHER', 'Other Belongings'),
    ]

    ITEM_TYPE_CHOICES = [
        ('LOST', 'Lost Item (I lost something)'),
        ('FOUND', 'Found Item (I found something)'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLAIMED', 'Claimed (Pending Transfer)'),
        ('RETURNED', 'Returned to Owner'),
    ]

    title = models.CharField(max_length=200, help_text="Short, clear title describing the item")
    description = models.TextField(help_text="Provide public visual details without giving away the secret verification answer")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='OTHER')
    location = models.CharField(max_length=150, help_text="Specific campus building, room, or landmark")
    incident_date = models.DateField(help_text="Date when item was lost or found")
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='LOST')
    image = models.ImageField(upload_to='items/%Y/%m/', blank=True, null=True, help_text="Optional photograph of the item")
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_items')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='OPEN')
    
    # Cryptographic verification for FOUND items
    verification_question = models.CharField(
        max_length=255,
        blank=True,
        help_text="For FOUND items: A question only the genuine owner can answer (e.g., 'What sticker is on the laptop back lid?')"
    )
    verification_answer_hash = models.CharField(
        max_length=255,
        blank=True,
        help_text="Secure PBKDF2/Argon2 cryptographic hash of the expected answer"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.title} ({self.get_status_display()})"

    def set_verification_answer(self, raw_answer):
        """Hashes the verification answer using Django's standard secure password hasher."""
        if raw_answer:
            cleaned = raw_answer.strip().lower()
            self.verification_answer_hash = make_password(cleaned)
        else:
            self.verification_answer_hash = ''

    def check_verification_answer(self, candidate_answer):
        """Verifies candidate answer against the stored cryptographic hash."""
        if not self.verification_answer_hash or not candidate_answer:
            return False
        cleaned = candidate_answer.strip().lower()
        return check_password(cleaned, self.verification_answer_hash)


class Claim(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Admin Review'),
        ('APPROVED', 'Approved (Ready for Handover)'),
        ('REJECTED', 'Rejected'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='claims')
    claimant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_claims')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    verification_passed = models.BooleanField(
        default=False,
        help_text="Indicates whether claimant solved the secret verification question"
    )
    claim_note = models.TextField(
        blank=True,
        help_text="Additional proof or explanation provided by claimant during verification"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Claim by {self.claimant.username} on {self.item.title} ({self.get_status_display()})"

    def clean(self):
        # Prevent reporting user from claiming their own item
        if self.item.reported_by == self.claimant:
            raise ValidationError("You cannot claim an item that you reported yourself.")
        
        # Prevent claiming items that are already returned
        if self.item.status == 'RETURNED':
            raise ValidationError("This item has already been marked as returned.")
