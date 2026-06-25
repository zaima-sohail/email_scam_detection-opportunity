# 🔒 Scam Detection - Quick Reference Guide

## 📋 Quick Facts

| Aspect | Details |
|--------|---------|
| **Status** | ✅ Production Ready |
| **Detection Method** | Heuristic-based (40+ patterns) |
| **Scam Threshold** | 0.5 (50% confidence) |
| **Safe Threshold** | < 0.5 confidence |
| **Analysis Areas** | Sender, Content, Links |
| **Severity Levels** | High, Medium, Low |
| **Manual Flagging** | ✅ Supported |
| **API Endpoints** | 3 new endpoints |
| **Database Fields** | 3 new fields |

---

## 🚀 Getting Started

### 1. **Check Detection Status**
```bash
cd emailscout_project/emailscout
python manage.py shell
```

```python
from emails.models import Email
email = Email.objects.first()
print(f"Is Scam: {email.is_scam}")
print(f"Confidence: {email.scam_confidence}")
print(f"Severity: {email.scam_severity}")
print(f"Reasons: {email.scam_reasons}")
```

### 2. **Access Security Report**
```
URL: http://localhost:8000/emails/security-report/
Shows: Stats, detected threats, user-flagged emails
```

### 3. **Use API Endpoints**
```bash
# Get statistics
curl http://localhost:8000/emails/api/scam-stats/

# Flag an email
curl -X POST http://localhost:8000/emails/api/1/flag/ \
  -H "Content-Type: application/json" \
  -d '{"is_flagged": true, "flagged_reason": "Looks suspicious"}'

# Get flagged emails
curl http://localhost:8000/emails/api/flagged/
```

---

## 🔍 Detection Areas

### **Sender Analysis** 👤
- Numeric prefixes in email: `user123456@domain.com` ← RED FLAG
- Free email as official: `support@gmail.com` claiming to be Amazon
- Domain spoofing: `gooogle.com` vs `google.com`
- Suspicious TLDs: `.xyz`, `.click`, `.loan`, `.top`, `.win`

### **Content Analysis** 📝
**40+ Phishing Patterns**:
- Urgency: "URGENT", "IMMEDIATE", "ACTION REQUIRED"
- Credential harvesting: "PASSWORD RESET", "VERIFY ACCOUNT"
- Lottery scams: "YOU'VE WON", "CLAIM YOUR PRIZE"
- Financial: "BANK ACCOUNT", "WIRE TRANSFER", "UNAUTHORIZED LOGIN"
- Offers: "FREE MONEY", "EASY MONEY", "WORK FROM HOME"

**Additional Indicators**:
- ALL-CAPS words (3+): Emotional manipulation
- Excessive exclamation marks (5+)
- Spelling errors: "acount", "verificaton", "confrim"

### **Link Analysis** 🔗
- IP-based URLs: `http://192.168.1.1` instead of domain
- Suspicious TLD URLs: Links ending in `.xyz`, `.click`
- Domain mismatch: Sender `@company.com` but link to `@attacker.com`
- Long/obfuscated URLs: (150+ characters)

---

## 📊 Database Schema

```sql
-- New fields in emails_email table
scam_severity VARCHAR(100)      -- "high,medium" (comma-separated)
is_flagged BOOLEAN              -- True if user flagged
flagged_reason TEXT             -- User's reason
```

---

## 🎯 Detection Examples

### ✅ SAFE Email (Confidence: 0.1)
```
From: john@company.com
To: team@company.com
Subject: Project Update
Body: Hi team, here is this week's update...
```

### ⚠️ SUSPICIOUS Email (Confidence: 0.4)
```
From: support@gmail.com (free email)
Subject: Click here to verify account
Body: Your account needs urgent verification...
Detected: Free email, generic greeting, 4 keywords
```

### ❌ SCAM Email (Confidence: 1.0 = 100%)
```
From: noreply@456789xyz.click
Subject: URGENT!!! VERIFY YOUR ACCOUNT NOW!!!
Body: Your account COMPROMISED!!! Click here immediately!!!
      Reset password and verify identity.
      http://192.168.1.1/verify
Detected: Numeric prefix, suspicious TLD (.click), 5 keywords,
          ALL-CAPS, excessive !, IP-based URL, domain mismatch
```

---

## 🔧 Configuration

### **Change Threshold**
```python
# File: emails/scam_detection.py
# Current: is_scam = confidence >= 0.5

# More aggressive (flag more emails):
is_scam = confidence >= 0.4

# More conservative (flag fewer emails):
is_scam = confidence >= 0.6
```

### **Add Custom Keywords**
```python
# File: emails/scam_detection.py
PHISHING_KEYWORDS = [
    r'\byour custom pattern\b',
    r'\banother pattern\b',
]
```

### **Add Suspicious TLDs**
```python
SUSPICIOUS_TLDS = [
    '.newtld',
    '.suspicius',
]
```

### **Whitelist Trusted Domains**
```python
TRUSTED_DOMAINS = {
    'company.com',
    'university.edu',
}
```

---

## 🔌 API Quick Reference

### Scam Statistics
```
GET /emails/api/scam-stats/
Response:
{
  "total_analyzed": 45,
  "scam_detected": 8,
  "safe_emails": 37,
  "flagged_by_user": 3,
  "high_severity_count": 2,
  "average_scam_confidence": 0.65,
  "top_scam_reasons": [
    {"reason": "Found suspicious keywords", "count": 6},
    {"reason": "Suspicious TLD", "count": 4}
  ]
}
```

### Flag Email
```
POST /emails/api/<id>/flag/
Content-Type: application/json

{
  "is_flagged": true,
  "flagged_reason": "Domain spoofing detected"
}

Response: {"success": true, "message": "Email flagged"}
```

### Get Flagged Emails
```
GET /emails/api/flagged/
Response:
{
  "flagged_emails": [
    {
      "id": 1,
      "subject": "...",
      "sender_email": "...",
      "is_flagged": true,
      "flagged_reason": "..."
    }
  ],
  "count": 3
}
```

---

## 📈 Performance Tips

- ✅ Analysis happens automatically on email fetch
- ✅ Non-blocking, synchronous processing
- ✅ Database indexed on user + is_scam
- ✅ API limits to 50 emails per request
- ✅ Statistics generated on-demand (efficient queries)

---

## 🐛 Troubleshooting

### **Emails not being analyzed?**
```bash
python manage.py shell
from emails.models import Email
email = Email.objects.first()
print(email.is_scam)  # Should not be None
```

### **Check migrations applied?**
```bash
python manage.py showmigrations emails
# Should show: [X] 0002_email_flagged_reason_email_is_flagged_and_more
```

### **Admin interface issues?**
- Clear browser cache
- Clear Django cache: `python manage.py clear_cache`
- Restart Django server

### **API endpoint 404?**
- Check urls.py includes: `path('api/scam-stats/', ...)`
- Verify URL pattern matches exactly
- Check view function is defined

---

## 📚 Files Modified

| File | Type | Changes |
|------|------|---------|
| `scam_detection.py` | Logic | Complete rewrite |
| `models.py` | Schema | 3 new fields |
| `views.py` | API | 3 new endpoints |
| `urls.py` | Routes | 3 new paths |
| `admin.py` | UI | Enhanced interface |
| `security_report.html` | Template | New sections |
| `0002_*.py` | Migration | Auto-generated |

---

## ✅ Testing Checklist

- [ ] Django check passes: `python manage.py check`
- [ ] Migrations applied: `python manage.py migrate`
- [ ] Admin interface shows new fields
- [ ] Legitimate emails not flagged
- [ ] Phishing emails flagged correctly
- [ ] API endpoints return 200 status
- [ ] Security report displays stats
- [ ] Manual flagging works
- [ ] Test both safe and scam emails

---

## 🎓 Learning Resources

- See `SCAM_DETECTION_FEATURE.md` for full documentation
- See `SCAM_DETECTION_IMPLEMENTATION.md` for implementation details
- Check `emails/scam_detection.py` for algorithm details
- Review test cases for detection examples

---

## 🆘 Quick Help

| Question | Answer |
|----------|--------|
| How is scam determined? | Confidence ≥ 0.5 = scam |
| Can I customize threshold? | Yes, edit `scam_detection.py` |
| Can I add keywords? | Yes, edit `PHISHING_KEYWORDS` list |
| Can I whitelist domains? | Yes, edit `TRUSTED_DOMAINS` set |
| Is data sent externally? | No, entirely offline |
| Can users flag emails? | Yes, via API or future UI |
| Can I see stats? | Yes, `/emails/api/scam-stats/` |
| What's the default threshold? | 0.5 (50% confidence) |

---

**Version**: 1.0  
**Status**: 🟢 Production Ready  
**Last Updated**: June 1, 2026
