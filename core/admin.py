from django.contrib import admin
from .models import Item, Claim

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'category', 'location', 'reported_by', 'status', 'incident_date', 'created_at')
    list_filter = ('item_type', 'status', 'category', 'incident_date')
    search_fields = ('title', 'description', 'location', 'reported_by__username')
    readonly_fields = ('verification_answer_hash', 'created_at')

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('item', 'claimant', 'status', 'verification_passed', 'created_at', 'reviewed_at')
    list_filter = ('status', 'verification_passed', 'created_at')
    search_fields = ('item__title', 'claimant__username', 'claim_note')
    readonly_fields = ('created_at',)
