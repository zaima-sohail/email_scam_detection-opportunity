"""
emails/models.py

This is the central database table for storing emails.
ALL other members (2, 3, 4) will read from this table.

Design decision: We store raw email data here.
Member 2 will add is_scam field.
Member 3 will add opportunity_type and relevance_score fields.
Member 4 will read all fields to display in the dashboard.
"""
from django.db import models
from django.contrib.auth.models import User


class Email(models.Model):
    """
    Stores a single email fetched from Gmail.
    
    This is the SHARED model — all team members work with this.
    """

    # Which user owns this email?
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='emails'
    )

    # ── Core Email Fields (Member 1 fills these) ──────────────────────────────
    gmail_id = models.CharField(
        max_length=200,
        unique=True,
        help_text="Unique ID from Gmail API — prevents duplicate fetching"
    )
    sender_name = models.CharField(max_length=300, blank=True)
    sender_email = models.EmailField(max_length=300, blank=True)
    subject = models.CharField(max_length=500, blank=True)
    body_preview = models.TextField(
        blank=True,
        help_text="First 500 chars of email body"
    )
    body_full = models.TextField(
        blank=True,
        help_text="Full email body text"
    )
    received_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When the email was originally sent"
    )
    fetched_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When we pulled it from Gmail"
    )
    is_read = models.BooleanField(default=False)

    # ── Member 2 Fields (Scam Detection) ──────────────────────────────────────
    # Member 2: fill these with your scam detector
    is_scam = models.BooleanField(
        null=True,   # null = not yet analyzed
        blank=True,
        help_text="True=scam, False=safe, None=not analyzed yet"
    )
    scam_confidence = models.FloatField(
        null=True, blank=True,
        help_text="0.0 to 1.0 — how confident the model is"
    )
    scam_reasons = models.TextField(
        blank=True,
        help_text="JSON list of reasons why flagged as scam"
    )
    scam_severity = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Comma-separated severity flags (high, medium, low)"
    )
    is_flagged = models.BooleanField(
        default=False,
        help_text="User manually flagged this email as scam/suspicious"
    )
    flagged_reason = models.TextField(
        blank=True,
        null=True,
        default='',
        help_text="User's reason for flagging the email"
    )

    # ── Member 3 Fields (Opportunity Detection) ───────────────────────────────
    # Member 3: fill these with your NLP classifier
    OPPORTUNITY_TYPES = [
        ('scholarship', 'Scholarship'),
        ('internship', 'Internship'),
        ('job', 'Job'),
        ('competition', 'Competition'),
        ('workshop', 'Workshop'),
        ('other', 'Other'),
        ('none', 'Not an Opportunity'),
    ]
    opportunity_type = models.CharField(
        max_length=50,
        choices=OPPORTUNITY_TYPES,
        blank=True,
        help_text="Category of opportunity (if any)"
    )
    relevance_score = models.FloatField(
        null=True, blank=True,
        help_text="0.0 to 10.0 — how relevant to this student"
    )
    deadline = models.DateField(
        null=True, blank=True,
        help_text="Application deadline if found in email"
    )

    def __str__(self):
        return f"[{self.user.username}] {self.subject[:60]}"

    class Meta:
        ordering = ['-received_at']
        verbose_name = "Email"
        verbose_name_plural = "Emails"

class Task(models.Model):
    """
    Task/Reminder management system for Member 4.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    email = models.ForeignKey(Email, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', help_text="Optional link to an email/opportunity")
    title = models.CharField(max_length=500)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    priority = models.CharField(max_length=20, choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    class Meta:
        ordering = ['is_completed', 'due_date', '-created_at']

