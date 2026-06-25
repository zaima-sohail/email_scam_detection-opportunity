import re
from datetime import datetime, timedelta

class OpportunityDetector:
    """
    NLP and Heuristic-based opportunity classifier and relevance scorer.
    Member 3 Responsibilities.
    """

    OPPORTUNITY_KEYWORDS = {
        'scholarship': [r'\bscholarship\b', r'\bfellowship\b', r'\bgrant\b', r'\btuition\b', r'\bfunding\b', r'\bfunded\b'],
        'internship': [r'\binternship\b', r'\bintern\b', r'\bco-op\b', r'\bcoop\b', r'\bsummer program\b'],
        'job': [r'\bjob\b', r'\bfull-time\b', r'\bpart-time\b', r'\bcareer\b', r'\bhiring\b', r'\bopen position\b', r'\bvacancy\b'],
        'competition': [r'\bcompetition\b', r'\bhackathon\b', r'\bcontest\b', r'\bprize\b', r'\bchallenge\b'],
        'workshop': [r'\bworkshop\b', r'\bwebinar\b', r'\bseminar\b', r'\bbootcamp\b', r'\btraining\b', r'\bmasterclass\b'],
    }

    @classmethod
    def analyze_email(cls, email_obj):
        """
        Detects if an email is an opportunity, scores relevance, and extracts deadline.
        Returns updated email_obj (not saved to DB yet).
        """
        # If it's flagged as a scam with high confidence, skip opportunity detection
        if email_obj.is_scam and email_obj.scam_confidence and email_obj.scam_confidence >= 0.5:
            email_obj.opportunity_type = 'none'
            email_obj.relevance_score = 0.0
            return email_obj

        text_to_search = (email_obj.subject + " " + email_obj.body_full).lower()
        
        # 1. Determine Opportunity Type
        detected_type = 'none'
        max_matches = 0
        
        for opp_type, patterns in cls.OPPORTUNITY_KEYWORDS.items():
            matches = sum(1 for p in patterns if re.search(p, text_to_search))
            if matches > max_matches:
                max_matches = matches
                detected_type = opp_type
        
        email_obj.opportunity_type = detected_type if max_matches > 0 else 'none'
        
        # 2. Calculate Relevance Score based on StudentProfile
        relevance = 0.0
        if email_obj.opportunity_type != 'none':
            relevance = cls._calculate_relevance(text_to_search, email_obj.user)
            
        email_obj.relevance_score = round(relevance, 2)
        
        # 3. Extract Deadline
        email_obj.deadline = cls._extract_deadline(text_to_search)

        return email_obj

    @classmethod
    def _calculate_relevance(cls, text, user):
        """
        Matches text against student interests and major to calculate a score out of 10.
        """
        score = 3.0 # Base score for being an opportunity

        try:
            profile = user.student_profile
        except:
            return score # Return base score if no profile exists

        # Match major
        if profile.major:
            major_words = [w.strip().lower() for w in profile.major.split(' ')]
            for word in major_words:
                if len(word) > 3 and word in text:
                    score += 2.0
                    break

        # Match interests
        if profile.interests:
            interests = [i.strip().lower() for i in profile.interests.split(',')]
            matched_interests = 0
            for interest in interests:
                if not interest: continue
                if interest in text:
                    matched_interests += 1
            
            # Add up to 5 points based on matching interests
            score += min(5.0, matched_interests * 1.5)

        return min(10.0, score)

    @classmethod
    def _extract_deadline(cls, text):
        """
        Looks for dates near 'deadline', 'apply by', 'due', 'closes'.
        """
        deadline_keywords = [r'deadline', r'apply by', r'due', r'closes', r'ends']
        
        # Look for dates like YYYY-MM-DD or MM/DD/YYYY
        date_patterns = [
            r'(202[0-9]-[0-1][0-9]-[0-3][0-9])',
            r'([0-1]?[0-9]/[0-3]?[0-9]/202[0-9])',
            r'([A-Za-z]{3,9}\s+[0-3]?[0-9],?\s+202[0-9])'
        ]

        for keyword in deadline_keywords:
            # Check within 50 characters of a deadline keyword
            match = re.search(f'{keyword}.{{0,50}}?(' + '|'.join(date_patterns) + ')', text)
            if match:
                date_str = match.group(1)
                # Attempt to parse
                try:
                    from dateutil import parser
                    parsed_date = parser.parse(date_str, fuzzy=True)
                    if parsed_date:
                        return parsed_date.date()
                except:
                    pass
        return None
