# Scam Detection Feature - Complete Implementation Guide

## Overview

The EmailScout application now includes a comprehensive **Scam Detection System** that automatically analyzes incoming emails for phishing attempts, scam indicators, and suspicious patterns. The system provides multiple detection capabilities and allows for manual flagging of suspicious emails.

---

## Features Implemented

### 1. **Automated Scam Analysis** 🛡️

The system automatically analyzes each email and computes a **scam confidence score** (0.0 - 1.0) based on:

#### A. **Sender Analysis**
- ✅ Detects emails from numeric/random sender prefixes
- ✅ Identifies free email services masquerading as legitimate companies
- ✅ Detects domain spoofing (similar but not exact domain names)
- ✅ Flags suspicious or newly-registered TLDs (.xyz, .click, .loan, etc.)
- ✅ Analyzes sender name legitimacy

#### B. **Phishing/Scam Keyword Detection**
- ✅ Identifies urgency/action-forcing words (urgent, immediate, action required)
- ✅ Detects credential harvesting attempts (password reset, verify account)
- ✅ Flags lottery/prize scam language
- ✅ Identifies financial/banking threats
- ✅ Detects suspicious offers and cryptocurrency lures
- ✅ Flags all-caps urgent text and excessive exclamation marks
- ✅ Identifies spelling/grammar errors common in phishing

#### C. **Link and URL Analysis**
- ✅ Detects IP-based URLs (instead of domain names)
- ✅ Identifies URLs with suspicious TLDs
- ✅ Flags domain mismatches (sender domain ≠ URL domain)
- ✅ Detects extremely long/obfuscated URLs
- ✅ Analyzes URL legitimacy

#### D. **Severity Classification**
- ✅ Marks emails with "high" severity flags for immediate attention
- ✅ Tracks multiple severity indicators per email

### 2. **Manual Flagging System** 🚩

Users can manually flag emails as suspicious:
- Flag emails for review even if auto-detection score is low
- Add custom reasons for flagging
- View all user-flagged emails in security report

### 3. **Comprehensive Security Report** 📊

The security report displays:
- **Total emails scanned**
- **Safe emails** (clear signals)
- **Detected scams** (anomalies)
- **High-severity threats**
- **User-flagged emails**
- **Detailed threat log** with:
  - Email subject and sender
  - Severity badge
  - Scam confidence percentage
  - List of detected threat vectors
  - Timestamp

### 4. **API Endpoints** 🔌

#### Get Scam Statistics
```
GET /emails/api/scam-stats/
```
Returns comprehensive statistics about detected scams:
- Total analyzed
- Scam count
- Safe count
- User-flagged count
- High-severity count
- Average scam confidence
- Top scam detection reasons

#### Get Flagged Emails
```
GET /emails/api/flagged/
```
Returns all emails manually flagged by the user.

#### Flag an Email
```
POST /emails/api/<email_id>/flag/
Content-Type: application/json

{
    "is_flagged": true,
    "flagged_reason": "This looks like a phishing attempt"
}
```

#### Update Email Analysis
```
POST /emails/api/<email_id>/update/
Content-Type: application/json

{
    "is_scam": true,
    "scam_confidence": 0.95,
    "scam_reasons": ["Found suspicious keywords", "High severity detected"]
}
```

---

## Database Schema

### New Email Model Fields

```python
# Scam Detection Fields
is_scam: BooleanField           # True=scam, False=safe, None=not analyzed
scam_confidence: FloatField     # 0.0 to 1.0 confidence score
scam_reasons: TextField         # JSON list of detection reasons
scam_severity: CharField        # Comma-separated severity flags (high, medium, low)

# User Flagging Fields
is_flagged: BooleanField        # True if user manually flagged this email
flagged_reason: TextField       # User's reason for flagging
```

---

## Scam Detection Algorithm

### Confidence Score Calculation

The system combines multiple detection methods:

1. **Sender Analysis** (max 0.5 points)
   - Numeric prefix: +0.2
   - Free email masquerading: +0.3
   - Domain spoofing: +0.35
   - Suspicious TLD: +0.25

2. **Content Analysis** (max 0.5 points)
   - Phishing keywords: +0.1 per keyword (max 0.5)
   - ALL-CAPS urgency: +0.15
   - Excessive exclamation marks: +0.1
   - Spelling errors: +0.1 per error

3. **Link Analysis** (max 0.4 points)
   - IP-based URL: +0.15
   - Suspicious TLD URL: +0.15
   - Domain mismatch: +0.35
   - Long/obfuscated URL: +0.15

**Classification Rule:**
- Confidence ≥ 0.5 → Marked as scam (is_scam = True)
- Confidence < 0.5 → Marked as safe (is_scam = False)

---

## Usage Examples

### Python/Django

```python
from emails.scam_detection import ScamDetector
from emails.models import Email

# Analyze an email
email = Email.objects.get(id=1)
email = ScamDetector.analyze_email(email)
email.save(update_fields=['is_scam', 'scam_confidence', 'scam_reasons', 'scam_severity'])

# Check results
print(f"Is Scam: {email.is_scam}")
print(f"Confidence: {email.scam_confidence}")
print(f"Severity: {email.scam_severity}")
print(f"Reasons: {email.scam_reasons}")
```

### JavaScript/Frontend

```javascript
// Get scam statistics
fetch('/emails/api/scam-stats/')
    .then(r => r.json())
    .then(data => console.log(data));

// Flag an email
fetch('/emails/api/42/flag/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        is_flagged: true,
        flagged_reason: "Suspicious domain and links"
    })
}).then(r => r.json()).then(data => console.log(data));

// Get flagged emails
fetch('/emails/api/flagged/')
    .then(r => r.json())
    .then(data => console.log(data.flagged_emails));
```

### cURL

```bash
# Get statistics
curl http://localhost:8000/emails/api/scam-stats/

# Flag an email
curl -X POST http://localhost:8000/emails/api/42/flag/ \
  -H "Content-Type: application/json" \
  -d '{"is_flagged": true, "flagged_reason": "Phishing attempt"}'

# Get flagged emails
curl http://localhost:8000/emails/api/flagged/
```

---

## Admin Interface

The Django admin interface now includes enhanced scam detection fields:

**List View Displays:**
- Email subject
- Sender email
- Received date
- Is Scam status
- Scam Confidence (%)
- Severity Flags
- User Flagged status
- Opportunity Type

**List Filters:**
- Is Scam (Yes/No)
- User Flagged
- Severity Flags
- Opportunity Type
- Is Read

**Detailed View Sections:**
1. Email Content
2. Scam Detection (collapsible)
3. User Flagging (collapsible)
4. Opportunity Detection (collapsible)

---

## Threshold Configuration

To adjust the scam detection threshold, modify the `analyze_email()` method in `scam_detection.py`:

```python
# Current threshold: 0.5 (50% confidence)
is_scam = confidence >= 0.5

# More aggressive: flag more emails
is_scam = confidence >= 0.4

# More conservative: flag fewer emails
is_scam = confidence >= 0.6
```

---

## Customization

### Add Custom Keywords

Edit the `PHISHING_KEYWORDS` list in `scam_detection.py`:

```python
PHISHING_KEYWORDS = [
    # ... existing keywords
    r'\byour custom pattern\b',
]
```

### Add Suspicious TLDs

Edit the `SUSPICIOUS_TLDS` list:

```python
SUSPICIOUS_TLDS = [
    # ... existing TLDs
    '.newtld',
]
```

### Whitelist Trusted Domains

Edit the `TRUSTED_DOMAINS` set to reduce false positives:

```python
TRUSTED_DOMAINS = {
    # ... existing domains
    'company.com',
}
```

---

## Performance Considerations

- Email analysis happens automatically on fetch
- Analysis is non-blocking and synchronous
- Database queries are optimized with proper indexing
- Security report generates stats on-demand

**Recommended Database Indexes:**
```python
class Meta:
    indexes = [
        models.Index(fields=['user', 'is_scam']),
        models.Index(fields=['user', 'is_flagged']),
        models.Index(fields=['user', '-received_at']),
    ]
```

---

## Security Notes

🔒 **Security Considerations:**

1. **User Isolation**: Each user only sees their own emails
2. **Field Validation**: Only specific fields can be updated via API
3. **Input Sanitization**: Regex patterns prevent injection
4. **No Third-Party Services**: Entirely offline analysis
5. **Data Privacy**: No emails sent to external services

---

## Future Enhancements

Possible improvements for future versions:

- 🤖 Machine Learning integration
- 🌐 Real-time domain reputation lookup
- 📊 Advanced analytics and trends
- 🔔 Real-time alerts for high-severity threats
- 📧 Integration with email providers' spam reports
- 🗺️ Geographical origin analysis
- 🔗 Safe link rewriting
- 📱 Mobile app support
- ⚙️ User-configurable detection sensitivity
- 📚 Threat intelligence feed integration

---

## Migration History

### Version 1.0 (Current)
- Initial implementation
- Sender analysis
- Phishing keyword detection
- URL analysis
- Manual flagging system
- Security reporting
- API endpoints

---

## Testing

### Test Flagging
```python
# Test manual flag
email = Email.objects.first()
email.is_flagged = True
email.flagged_reason = "Test flag"
email.save()
```

### Test API Endpoints
```bash
# Test scam stats
curl -H "Cookie: sessionid=YOUR_SESSION" \
  http://localhost:8000/emails/api/scam-stats/

# Test flag endpoint
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION" \
  -d '{"is_flagged": true, "flagged_reason": "Test"}' \
  http://localhost:8000/emails/api/1/flag/
```

---

## Support & Documentation

For more information:
- Django Documentation: https://docs.djangoproject.com/
- Project README: See main project documentation
- Admin Panel: /admin/ (Django admin interface)

---

## License

This feature is part of the EmailScout project and follows the same license terms.

---

**Last Updated:** June 2026
**Feature Status:** ✅ Production Ready
