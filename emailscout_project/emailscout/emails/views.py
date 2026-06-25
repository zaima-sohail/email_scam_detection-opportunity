"""
emails/views.py

Two types of views here:
1. HTML views — for the browser (Member 4 will replace these with their dashboard)
2. API views — JSON endpoints that Member 2, 3, 4 will call from their code
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Email
from .gmail_service import GmailService
from accounts.models import GmailToken
from .scam_detection import ScamDetector


# ─── HTML VIEWS ───────────────────────────────────────────────────────────────

@login_required
def email_list(request):
    """
    Main inbox page — shows all fetched emails.
    Member 4 will redesign this view with their dashboard.
    """
    import json as json_lib
    gmail_connected = GmailToken.objects.filter(user=request.user).exists()

    from .models import Task
    emails = Email.objects.filter(user=request.user).order_by('-received_at')
    
    # Add dynamic Priority Rating logic and parse scam reasons for display
    from datetime import date
    today = date.today()
    for email in emails:
        # Priority rating for opportunities
        if email.opportunity_type and email.opportunity_type != 'none':
            priority = 'low'
            if email.deadline:
                days_left = (email.deadline - today).days
                if days_left <= 7 and getattr(email, 'relevance_score', 0) >= 5.0:
                    priority = 'high'
                elif days_left <= 14 or getattr(email, 'relevance_score', 0) >= 7.0:
                    priority = 'medium'
            elif (email.relevance_score or 0) >= 8.0:
                priority = 'medium'
            email.priority_rating = priority

        # Parse scam reasons for template display
        if email.scam_reasons:
            try:
                email.parsed_reasons = json_lib.loads(email.scam_reasons)
            except Exception:
                email.parsed_reasons = []
        else:
            email.parsed_reasons = []
        
        # Parse severity flags
        email.severity_list = [s.strip() for s in email.scam_severity.split(',') if s.strip()] if email.scam_severity else []

    tasks = Task.objects.filter(user=request.user, is_completed=False)

    context = {
        'emails': emails,
        'gmail_connected': gmail_connected,
        'total_count': emails.count(),
        'unread_count': emails.filter(is_read=False).count(),
        'scam_count': emails.filter(is_scam=True).count(),
        'safe_count': emails.filter(is_scam=False).count(),
        'tasks': tasks,
    }
    return render(request, 'emails/email_list.html', context)


@login_required
def email_detail(request, email_id):
    """Show a single email's full content."""
    try:
        email = Email.objects.get(id=email_id, user=request.user)
        email.is_read = True
        email.save(update_fields=['is_read'])
    except Email.DoesNotExist:
        messages.error(request, 'Email not found.')
        return redirect('/emails/')

    return render(request, 'emails/email_detail.html', {'email': email})

@login_required
def security_report(request):
    """
    Shows statistics about scam and safe emails.
    """
    import json
    emails = Email.objects.filter(user=request.user)
    
    # Exclude those that haven't been analyzed (is_scam is null)
    analyzed_emails = emails.exclude(is_scam__isnull=True)
    total_scanned = analyzed_emails.count()
    safe_count = analyzed_emails.filter(is_scam=False).count()
    scam_count = analyzed_emails.filter(is_scam=True).count()
    flagged_count = emails.filter(is_flagged=True).count()
    high_severity_count = analyzed_emails.filter(scam_severity__icontains='high').count()
    
    recent_scams = analyzed_emails.filter(is_scam=True).order_by('-received_at')[:10]
    flagged_by_user = emails.filter(is_flagged=True).order_by('-received_at')[:10]

    for email in recent_scams:
        if email.scam_reasons:
            try:
                email.parsed_reasons = json.loads(email.scam_reasons)
            except:
                email.parsed_reasons = []
        else:
            email.parsed_reasons = []
        
        # Parse severity flags
        email.severity_list = email.scam_severity.split(',') if email.scam_severity else []

    context = {
        'total_scanned': total_scanned,
        'safe_count': safe_count,
        'scam_count': scam_count,
        'flagged_count': flagged_count,
        'high_severity_count': high_severity_count,
        'recent_scams': recent_scams,
        'flagged_by_user': flagged_by_user,
    }
    return render(request, 'emails/security_report.html', context)


@login_required
def opportunities_board(request):
    """
    Dedicated dashboard for showing detected opportunities (Member 3).
    Sorts by relevance score.
    """
    emails = Email.objects.filter(
        user=request.user, 
        is_scam=False
    ).exclude(
        opportunity_type__isnull=True
    ).exclude(
        opportunity_type='none'
    ).order_by('-relevance_score', '-received_at')

    from datetime import date
    today = date.today()
    for email in emails:
        priority = 'low'
        # Safely handle relevance_score; treat None as 0
        relevance = email.relevance_score or 0
        if email.deadline:
            days_left = (email.deadline - today).days
            if days_left <= 7 and relevance >= 5.0:
                priority = 'high'
            elif days_left <= 14 or relevance >= 7.0:
                priority = 'medium'
        elif relevance >= 8.0:
            priority = 'medium'
        email.priority_rating = priority

    context = {
        'opportunities': emails,
        'total_opportunities': emails.count(),
        'top_matches': emails.filter(relevance_score__gte=7.0).count()
    }
    return render(request, 'emails/opportunities_board.html', context)


@login_required
@require_POST
def add_task(request):
    """Adds a new task to the user's checklist."""
    from .models import Task
    title = request.POST.get('title')
    email_id = request.POST.get('email_id')
    priority = request.POST.get('priority', 'medium')
    
    if title:
        task = Task(user=request.user, title=title, priority=priority)
        if email_id:
            try:
                task.email = Email.objects.get(id=email_id, user=request.user)
                if task.email.deadline:
                    task.due_date = task.email.deadline
            except Email.DoesNotExist:
                pass
        task.save()
        messages.success(request, 'Task added to your checklist.')
    
    # Redirect back to where they came from
    next_url = request.POST.get('next', '/emails/')
    return redirect(next_url)


@login_required
def toggle_task(request, task_id):
    """Toggles a task's completion status."""
    from .models import Task
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        task.is_completed = not task.is_completed
        task.save()
    except Task.DoesNotExist:
        pass
    
    return redirect('/emails/')

# ─── FETCH ACTION ─────────────────────────────────────────────────────────────

@login_required
def fetch_emails(request):
    """
    Trigger a Gmail fetch. Can be called from a button in the UI.
    Fetches up to 20 unread emails and saves new ones to DB.
    """
    gmail_service = GmailService(request.user)

    if not gmail_service.is_connected():
        messages.error(request, 'Connect your Gmail first.')
        return redirect('/emails/')

    raw_emails = gmail_service.fetch_unread_emails(max_results=20)

    new_count = 0
    rejected_count = 0
    for email_data in raw_emails:
        # get_or_create: don't save duplicates
        # gmail_id is unique — if we already have it, skip
        obj, created = Email.objects.get_or_create(
            gmail_id=email_data['gmail_id'],
            defaults={
                'user': request.user,
                **email_data  # Unpack all the fields
            }
        )
        if created:
            new_count += 1
            # Run Scam Detection
            obj = ScamDetector.analyze_email(obj)
            
            # Automatically flag or reject scam messages
            if obj.is_scam:
                if obj.scam_confidence >= 0.8:
                    # Auto-reject (delete) very high confidence scams
                    obj.delete()
                    rejected_count += 1
                    new_count -= 1  # Since we deleted it, don't count as a new fetched email
                    continue
                else:
                    # Auto-flag suspicious but not guaranteed scams
                    obj.is_flagged = True
                    obj.flagged_reason = "Auto-flagged by ScamDetector"
            
            # Run Opportunity Detection
            from .opportunity_detection import OpportunityDetector
            obj = OpportunityDetector.analyze_email(obj)

            # Save all the fields at once
            obj.save(update_fields=[
                'is_scam', 'scam_confidence', 'scam_reasons', 'scam_severity', 
                'is_flagged', 'flagged_reason',
                'opportunity_type', 'relevance_score', 'deadline'
            ])

    messages.success(request, f'Fetched {new_count} new emails. Auto-rejected {rejected_count} high-confidence scams.')
    return redirect('/emails/')


# ─── API VIEWS (for Members 2, 3, 4) ─────────────────────────────────────────

@login_required
def api_email_list(request):
    """
    GET /emails/api/list/
    
    Returns all emails as JSON.
    Member 2 uses this to get emails for scam detection.
    Member 3 uses this to get emails for opportunity classification.
    Member 4 uses this to populate the dashboard.
    
    Query params:
        ?analyzed=false   → only emails not yet analyzed
        ?type=scholarship → filter by opportunity type
        ?scam=false       → filter out scams
    """
    emails = Email.objects.filter(user=request.user)

    # Optional filters
    analyzed = request.GET.get('analyzed')
    if analyzed == 'false':
        emails = emails.filter(is_scam__isnull=True)

    opp_type = request.GET.get('type')
    if opp_type:
        emails = emails.filter(opportunity_type=opp_type)

    scam_filter = request.GET.get('scam')
    if scam_filter == 'false':
        emails = emails.filter(is_scam=False)

    data = [email_to_dict(e) for e in emails[:50]]  # Max 50 at a time
    return JsonResponse({'emails': data, 'count': len(data)})


@login_required
def api_email_detail(request, email_id):
    """
    GET /emails/api/<id>/
    Returns single email as JSON.
    """
    try:
        email = Email.objects.get(id=email_id, user=request.user)
        return JsonResponse(email_to_dict(email))
    except Email.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


@login_required
@require_POST
def api_update_email(request, email_id):
    """
    POST /emails/api/<id>/update/
    
    Allows Member 2 and Member 3 to write their results back.
    They POST JSON with the fields they've analyzed.
    
    Example from Member 2:
        POST {"is_scam": true, "scam_confidence": 0.95, "scam_reasons": ["suspicious link"]}
    
    Example from Member 3:
        POST {"opportunity_type": "scholarship", "relevance_score": 8.5}
    """
    import json as json_lib
    try:
        email = Email.objects.get(id=email_id, user=request.user)
        data = json_lib.loads(request.body)

        # Only allow updating specific fields (security: don't let anyone change anything)
        allowed_fields = [
            'is_scam', 'scam_confidence', 'scam_reasons', 'scam_severity',
            'is_flagged', 'flagged_reason',
            'opportunity_type', 'relevance_score', 'deadline', 'is_read'
        ]

        updated = []
        for field in allowed_fields:
            if field in data:
                setattr(email, field, data[field])
                updated.append(field)

        if updated:
            email.save(update_fields=updated)

        return JsonResponse({'success': True, 'updated_fields': updated})

    except Email.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def api_flag_email(request, email_id):
    """
    POST /emails/api/<id>/flag/
    
    Manually flag an email as suspicious/scam.
    
    Request JSON:
        {
            "is_flagged": true,
            "flagged_reason": "This looks like a phishing attempt"
        }
    """
    import json as json_lib
    try:
        email = Email.objects.get(id=email_id, user=request.user)
        data = json_lib.loads(request.body)

        email.is_flagged = data.get('is_flagged', False)
        email.flagged_reason = data.get('flagged_reason', '')
        email.save(update_fields=['is_flagged', 'flagged_reason'])

        return JsonResponse({
            'success': True,
            'message': 'Email flagged' if email.is_flagged else 'Flag removed'
        })

    except Email.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_flagged_emails(request):
    """
    GET /emails/api/flagged/
    
    Returns all emails flagged as suspicious by the user.
    """
    emails = Email.objects.filter(user=request.user, is_flagged=True).order_by('-received_at')
    data = [email_to_dict(e) for e in emails]
    return JsonResponse({'flagged_emails': data, 'count': len(data)})


@login_required
def api_scam_statistics(request):
    """
    GET /emails/api/scam-stats/
    
    Returns comprehensive scam detection statistics.
    """
    emails = Email.objects.filter(user=request.user)
    analyzed = emails.exclude(is_scam__isnull=True)

    total_scanned = analyzed.count()
    scam_count = analyzed.filter(is_scam=True).count()
    safe_count = analyzed.filter(is_scam=False).count()
    flagged_count = emails.filter(is_flagged=True).count()

    # Count severity flags
    high_severity = analyzed.filter(scam_severity__icontains='high').count()
    
    # Average confidence of detected scams
    scam_emails = analyzed.filter(is_scam=True)
    avg_confidence = 0
    if scam_emails.exists():
        avg_confidence = sum(e.scam_confidence or 0 for e in scam_emails) / scam_emails.count()

    # Top reasons for flagging
    import json as json_lib
    reason_counts = {}
    for email in analyzed.filter(is_scam=True):
        if email.scam_reasons:
            try:
                reasons = json_lib.loads(email.scam_reasons)
                for reason in reasons:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
            except:
                pass

    top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return JsonResponse({
        'total_analyzed': total_scanned,
        'scam_detected': scam_count,
        'safe_emails': safe_count,
        'flagged_by_user': flagged_count,
        'high_severity_count': high_severity,
        'average_scam_confidence': round(avg_confidence, 2),
        'top_scam_reasons': [{'reason': r[0], 'count': r[1]} for r in top_reasons],
    })


# ─── HELPER ───────────────────────────────────────────────────────────────────

def email_to_dict(email):
    """Convert an Email model instance to a JSON-serializable dict."""
    return {
        'id': email.id,
        'gmail_id': email.gmail_id,
        'sender_name': email.sender_name,
        'sender_email': email.sender_email,
        'subject': email.subject,
        'body_preview': email.body_preview,
        'body_full': email.body_full,
        'received_at': email.received_at.isoformat() if email.received_at else None,
        'fetched_at': email.fetched_at.isoformat(),
        'is_read': email.is_read,
        # Member 2 fields (Scam Detection)
        'is_scam': email.is_scam,
        'scam_confidence': email.scam_confidence,
        'scam_reasons': email.scam_reasons,
        'scam_severity': email.scam_severity,
        'is_flagged': email.is_flagged,
        'flagged_reason': email.flagged_reason,
        # Member 3 fields (Opportunity Detection)
        'opportunity_type': email.opportunity_type,
        'relevance_score': email.relevance_score,
        'deadline': email.deadline.isoformat() if email.deadline else None,
    }
