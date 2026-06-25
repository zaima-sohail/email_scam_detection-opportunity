from django.contrib import admin
from .models import Email

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender_email', 'received_at', 'is_scam', 'scam_confidence', 'scam_severity', 'is_flagged', 'opportunity_type']
    list_filter = ['is_scam', 'is_flagged', 'scam_severity', 'opportunity_type', 'is_read']
    search_fields = ['subject', 'sender_email', 'body_preview', 'scam_reasons', 'flagged_reason']
    readonly_fields = ['gmail_id', 'fetched_at']
    fieldsets = (
        ('Email Content', {
            'fields': ('gmail_id', 'user', 'sender_name', 'sender_email', 'subject', 'body_preview', 'body_full', 'received_at', 'fetched_at', 'is_read')
        }),
        ('Scam Detection', {
            'fields': ('is_scam', 'scam_confidence', 'scam_reasons', 'scam_severity'),
            'classes': ('collapse',)
        }),
        ('User Flagging', {
            'fields': ('is_flagged', 'flagged_reason'),
            'classes': ('collapse',)
        }),
        ('Opportunity Detection', {
            'fields': ('opportunity_type', 'relevance_score', 'deadline'),
            'classes': ('collapse',)
        }),
    )
