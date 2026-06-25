import re
import json
from urllib.parse import urlparse
from difflib import SequenceMatcher


class ScamDetector:
    """
    Advanced heuristic-based scam detector to classify emails as safe or unsafe.
    Analyzes: sender information, phishing keywords, suspicious links, and patterns.
    """

    # ════════════════════════════════════════════════════════════════════════════
    # SCAM KEYWORDS - Expanded set for phishing/scam detection
    # ════════════════════════════════════════════════════════════════════════════
    PHISHING_KEYWORDS = [
        # Urgency & action-forcing words
        r'\burgent\b', r'\bimmediate\b', r'\baction required\b', r'\bconfirm now\b',
        r'\bclick here\b', r'\bverify now\b', r'\breactivate\b', r'\bupdate\b',
        
        # Credential harvesting
        r'\bpassword reset\b', r'\breset password\b', r'\bpassword expires\b',
        r'\bverify your account\b', r'\bconfirm identity\b', r'\bconfirm your password\b',
        r'\breenter password\b', r'\bupdate payment\b', r'\bupdate billing\b',
        
        # Financial/rewards (lottery/prize scams)
        r'\blottery\b', r'\bwinner\b', r'\bclaim your prize\b', r'\bcongratuations\b',
        r'\byou\'ve won\b', r'\bcongratulation\b', r'\breceived a prize\b',
        
        # Banking/financial
        r'\bbank account\b', r'\bsocial security\b', r'\bunauthorized login\b',
        r'\bwire transfer\b', r'\btransfer funds\b', r'\baccount suspended\b',
        r'\baccount locked\b', r'\baccount will be closed\b', r'\bakcount verification\b',
        
        # Cryptocurrency/suspicious finance
        r'\bbitcoin\b', r'\bcrypto\b', r'\bcryptocurrency\b', r'\bethereum\b',
        
        # Inheritance/money
        r'\binheritance\b', r'\bwill\b', r'\bbeneficiary\b', r'\bclaim money\b',
        
        # Suspicious offers
        r'\bfree money\b', r'\beasy money\b', r'\bwork from home\b', r'\bmake money fast\b',
        r'\bno experience needed\b',
        
        # Technical urgency
        r'\bmalware detected\b', r'\bvirus detected\b', r'\bsecurity alert\b',
        r'\busual activity\b', r'\bunusual sign-in\b',
    ]

    GENERIC_GREETINGS = [
        r'\bdear (user|customer|member|valued|sir|madam)\b',
        r'\bdear friend\b',
        r'\bto whom it may concern\b',
        r'\bhello there\b',
    ]

    SUSPICIOUS_TLDS = [
        '.xyz', '.click', '.loan', '.top', '.win', '.download', '.review',
        '.faith', '.webcam', '.gdn', '.party', '.date', '.stream', '.racing',
        '.space', '.science', '.work', '.holiday', '.men', '.accountant',
    ]

    # ════════════════════════════════════════════════════════════════════════════
    # LEGITIMATE DOMAINS (whitelist to reduce false positives)
    # ════════════════════════════════════════════════════════════════════════════
    TRUSTED_DOMAINS = {
        'gmail.com', 'google.com', 'apple.com', 'microsoft.com', 'amazon.com',
        'facebook.com', 'linkedin.com', 'twitter.com', 'github.com', 'stackoverflow.com',
        'reddit.com', 'wikipedia.org', 'mozilla.org', 'python.org', 'java.com',
        'edu', 'org', 'gov',  # TLD suffixes
    }

    @classmethod
    def analyze_email(cls, email_obj):
        """
        Comprehensive analysis of an Email model instance.
        Returns the updated (but not saved) email_obj.
        """
        confidence = 0.0
        reasons = []
        severity_flags = []

        # 1. SENDER ANALYSIS
        sender_analysis = cls._analyze_sender(email_obj)
        confidence += sender_analysis['score']
        reasons.extend(sender_analysis['reasons'])
        severity_flags.extend(sender_analysis.get('severity', []))

        # 2. CONTENT ANALYSIS (Keywords, patterns, urgency)
        content_analysis = cls._analyze_content(email_obj)
        confidence += content_analysis['score']
        reasons.extend(content_analysis['reasons'])
        severity_flags.extend(content_analysis.get('severity', []))

        # 3. LINK ANALYSIS
        link_analysis = cls._analyze_links(email_obj)
        confidence += link_analysis['score']
        reasons.extend(link_analysis['reasons'])
        severity_flags.extend(link_analysis.get('severity', []))

        # Normalize confidence to 0.0 - 1.0
        confidence = min(1.0, max(0.0, confidence))

        # Determine if it's a scam (High threshold: 0.5+)
        is_scam = confidence >= 0.5

        # Update Email object
        email_obj.is_scam = is_scam
        email_obj.scam_confidence = round(confidence, 2)
        email_obj.scam_reasons = json.dumps(reasons)
        email_obj.scam_severity = ','.join(severity_flags) if severity_flags else ''

        return email_obj

    # ════════════════════════════════════════════════════════════════════════════
    # ANALYSIS METHODS
    # ════════════════════════════════════════════════════════════════════════════

    @classmethod
    def _analyze_sender(cls, email_obj):
        """Analyze sender email and name for red flags."""
        score = 0.0
        reasons = []
        severity = []
        
        sender_email = email_obj.sender_email.lower()
        sender_name = email_obj.sender_name.lower()

        if not sender_email:
            score += 0.3
            reasons.append("Missing sender email")
            return {'score': score, 'reasons': reasons, 'severity': severity}

        try:
            # Extract domain from sender email
            domain = sender_email.split('@')[1] if '@' in sender_email else ''
            prefix = sender_email.split('@')[0]

            # ──────────────────────────────────────────────────────────────────
            # 1. Suspicious sender prefix (lots of numbers/randomness)
            # ──────────────────────────────────────────────────────────────────
            digit_count = len(re.findall(r'\d', prefix))
            if digit_count >= 5 and len(prefix) < 15:
                score += 0.2
                reasons.append("Sender prefix contains suspicious number of digits")

            # ──────────────────────────────────────────────────────────────────
            # 2. Free email service masquerading as legitimate org
            # ──────────────────────────────────────────────────────────────────
            free_mail_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
            if domain in free_mail_domains:
                if any(word in sender_name for word in ['bank', 'amazon', 'apple', 'microsoft', 'paypal', 'admin', 'support']):
                    score += 0.3
                    severity.append('high')
                    reasons.append("Free email service claiming to be official company")

            # ──────────────────────────────────────────────────────────────────
            # 3. Domain spoofing detection (similar but not exact legitimate domain)
            # ──────────────────────────────────────────────────────────────────
            common_domains = ['google.com', 'amazon.com', 'apple.com', 'microsoft.com']
            for legit_domain in common_domains:
                similarity = SequenceMatcher(None, domain, legit_domain).ratio()
                if 0.7 <= similarity < 0.95:  # Similar but not exact
                    score += 0.35
                    severity.append('high')
                    reasons.append(f"Domain '{domain}' suspiciously similar to '{legit_domain}'")

            # ──────────────────────────────────────────────────────────────────
            # 4. Suspicious or newly registered TLDs
            # ──────────────────────────────────────────────────────────────────
            for suspicious_tld in cls.SUSPICIOUS_TLDS:
                if domain.endswith(suspicious_tld):
                    score += 0.25
                    reasons.append(f"Suspicious TLD: {suspicious_tld}")

            # ──────────────────────────────────────────────────────────────────
            # 5. Generic greeting with mismatched sender name
            # ──────────────────────────────────────────────────────────────────
            for greeting_pattern in cls.GENERIC_GREETINGS:
                if re.search(greeting_pattern, email_obj.body_full.lower()[:200]):
                    if not sender_name or sender_name in ['noreply', 'no-reply', 'donotreply']:
                        score += 0.15
                        reasons.append("Generic greeting with automated sender")
                    break

        except Exception as e:
            print(f"Error in sender analysis: {e}")

        return {'score': min(0.5, score), 'reasons': reasons, 'severity': severity}

    @classmethod
    def _analyze_content(cls, email_obj):
        """Analyze email content for phishing/scam indicators."""
        score = 0.0
        reasons = []
        severity = []
        
        text_to_search = (email_obj.subject + " " + email_obj.body_full).lower()
        body_lower = email_obj.body_full.lower()

        # ────────────────────────────────────────────────────────────────────
        # 1. Phishing keywords detection
        # ────────────────────────────────────────────────────────────────────
        found_keywords = []
        for keyword_pattern in cls.PHISHING_KEYWORDS:
            if re.search(keyword_pattern, text_to_search):
                found_keywords.append(keyword_pattern.replace(r'\b', '').strip())
        
        if found_keywords:
            keyword_score = min(0.5, 0.1 * len(found_keywords))
            score += keyword_score
            
            # Mark as high severity if multiple urgency keywords
            urgency_words = ['urgent', 'immediate', 'action required', 'click here', 'verify now']
            urgency_count = sum(1 for w in urgency_words if w in text_to_search)
            if urgency_count >= 2:
                severity.append('high')
            
            reasons.append(f"Found {len(found_keywords)} suspicious keywords")

        # ────────────────────────────────────────────────────────────────────
        # 2. All-caps urgency text (common in scams)
        # ────────────────────────────────────────────────────────────────────
        all_caps_words = re.findall(r'\b[A-Z]{4,}\b', email_obj.subject + " " + email_obj.body_full[:500])
        if len(all_caps_words) >= 3:
            score += 0.15
            reasons.append("Multiple ALL-CAPS words indicating urgency")

        # ────────────────────────────────────────────────────────────────────
        # 3. Excessive exclamation marks (emotional manipulation)
        # ────────────────────────────────────────────────────────────────────
        exclamation_count = (email_obj.subject + " " + email_obj.body_full[:500]).count('!')
        if exclamation_count >= 5:
            score += 0.1
            reasons.append("Excessive exclamation marks (emotional manipulation)")

        # ────────────────────────────────────────────────────────────────────
        # 4. Spelling/grammar errors (common in phishing)
        # ────────────────────────────────────────────────────────────────────
        common_misspellings = [
            r'\bacount\b', r'\bverificaton\b', r'\bconfrim\b',
            r'\baccont\b', r'\bupdat\b', r'\bseccurity\b',
        ]
        misspelling_count = sum(1 for pattern in common_misspellings if re.search(pattern, body_lower))
        if misspelling_count >= 2:
            score += 0.1
            reasons.append("Multiple spelling errors (common in phishing)")

        return {'score': min(0.5, score), 'reasons': reasons, 'severity': severity}

    @classmethod
    def _analyze_links(cls, email_obj):
        """Analyze URLs and links for suspicious patterns."""
        score = 0.0
        reasons = []
        severity = []
        
        # Extract all URLs (http, https, and sometimes shortened)
        urls = re.findall(r'(https?://[^\s<>"{}|\\^`\[\]]*)', email_obj.body_full)

        if not urls:
            return {'score': 0, 'reasons': [], 'severity': []}

        suspicious_url_count = 0

        for url in urls:
            url_lower = url.lower()
            
            # ────────────────────────────────────────────────────────────────
            # 1. IP-based links (instead of domain names)
            # ────────────────────────────────────────────────────────────────
            if re.search(r'https?://\d+\.\d+\.\d+\.\d+', url_lower):
                suspicious_url_count += 1
                severity.append('high')
                reasons.append(f"IP-based URL (instead of domain): {url[:50]}...")

            # ────────────────────────────────────────────────────────────────
            # 2. Suspicious or newly registered TLDs in URL
            # ────────────────────────────────────────────────────────────────
            for tld in cls.SUSPICIOUS_TLDS:
                if tld in url_lower:
                    suspicious_url_count += 1
                    reasons.append(f"URL contains suspicious TLD {tld}: {url[:50]}...")
                    break

            # ────────────────────────────────────────────────────────────────
            # 3. Domain mismatch (URL domain ≠ sender domain)
            # ────────────────────────────────────────────────────────────────
            try:
                parsed = urlparse(url)
                url_domain = parsed.netloc.lower().replace('www.', '')
                sender_domain = email_obj.sender_email.split('@')[1].lower() if '@' in email_obj.sender_email else ''
                
                # If sender claims to be from a legitimate company but URL doesn't match
                if sender_domain and not any(trusted in sender_domain for trusted in cls.TRUSTED_DOMAINS):
                    if url_domain != sender_domain and not url_domain.endswith(sender_domain):
                        suspicious_url_count += 1
                        severity.append('high')
                        reasons.append(f"Domain mismatch: sender from '{sender_domain}' but URL to '{url_domain}'")
            except:
                pass

            # ────────────────────────────────────────────────────────────────
            # 4. Extremely long or obfuscated URLs (hide true destination)
            # ────────────────────────────────────────────────────────────────
            if len(url) > 150:
                suspicious_url_count += 1
                reasons.append("Extremely long/obfuscated URL")

        # Score based on suspicious URL count
        if suspicious_url_count > 0:
            score = min(0.4, 0.15 * suspicious_url_count)

        return {'score': score, 'reasons': reasons, 'severity': severity}
