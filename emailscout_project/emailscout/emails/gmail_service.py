"""
emails/gmail_service.py
Handles all Gmail API calls using the manually saved token.
"""
import json
import base64
import re
from email.utils import parsedate_to_datetime

import requests as http_requests
from django.conf import settings

from accounts.models import GmailToken


class GmailService:
    def __init__(self, user):
        self.user = user
        self.access_token = None
        self._load_token()

    def _load_token(self):
        try:
            token_obj = GmailToken.objects.get(user=self.user)
            token_data = json.loads(token_obj.token_data)
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            self.token_obj = token_obj
            self.token_data = token_data
        except GmailToken.DoesNotExist:
            self.access_token = None

    def _headers(self):
        return {'Authorization': f'Bearer {self.access_token}'}

    def _refresh_if_needed(self):
        """Try to refresh the access token using the refresh token."""
        if not self.refresh_token:
            return False
        from accounts.views import _load_client_secrets
        import json as json_lib
        client_id, client_secret = _load_client_secrets()
        resp = http_requests.post('https://oauth2.googleapis.com/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
        })
        new_data = resp.json()
        if 'access_token' in new_data:
            self.access_token = new_data['access_token']
            # Merge and save
            self.token_data.update(new_data)
            self.token_obj.token_data = json_lib.dumps(self.token_data)
            self.token_obj.save()
            return True
        return False

    def fetch_recent_emails(self, max_results=10):
        """Fetch recent emails (read or unread) with full details — used as fallback."""
        if not self.is_connected():
            return []
        try:
            url = "https://www.googleapis.com/gmail/v1/users/me/messages"
            params = {'maxResults': max_results}
            resp = self._gmail_get(url, params=params)
            messages_list = resp.json().get('messages', [])
            emails = []
            for msg in messages_list:
                email_data = self._fetch_single_email(msg['id'])
                if email_data:
                    emails.append(email_data)
            return emails
        except Exception as e:
            print(f"Error fetching recent emails: {e}")
            return []

    def fetch_unread_emails(self, max_results=20):
        """Fetch unread inbox emails. Falls back to recent emails if none are unread."""
        if not self.is_connected():
            return []
        try:
            url = "https://www.googleapis.com/gmail/v1/users/me/messages"
            params = {'q': 'is:unread in:inbox', 'maxResults': max_results}
            resp = self._gmail_get(url, params=params)
            messages_list = resp.json().get('messages', [])
            if not messages_list:
                # No unread emails — fall back to recent emails
                return self.fetch_recent_emails(max_results)
            emails = []
            for msg in messages_list:
                email_data = self._fetch_single_email(msg['id'])
                if email_data:
                    emails.append(email_data)
            return emails
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def is_connected(self):
        return bool(self.access_token)

    def _gmail_get(self, url, params=None):
        """Make a Gmail API GET request, refreshing token if 401."""
        resp = http_requests.get(url, headers=self._headers(), params=params)
        if resp.status_code == 401:
            if self._refresh_if_needed():
                resp = http_requests.get(url, headers=self._headers(), params=params)
        return resp

    def _fetch_single_email(self, gmail_id):
        """Fetch a single email by its Gmail ID and return a dict of parsed fields."""
        try:
            resp = self._gmail_get(
                f'https://www.googleapis.com/gmail/v1/users/me/messages/{gmail_id}',
                params={'format': 'full'}
            )
            message = resp.json()
            headers = {
                h['name'].lower(): h['value']
                for h in message.get('payload', {}).get('headers', [])
            }
            sender_raw = headers.get('from', '')
            sender_name, sender_email = parse_sender(sender_raw)
            subject = headers.get('subject', '(No Subject)')
            received_at = parse_date(headers.get('date', ''))
            body = extract_body(message.get('payload', {}))
            return {
                'gmail_id': gmail_id,
                'sender_name': sender_name,
                'sender_email': sender_email,
                'subject': subject,
                'body_preview': body[:500],
                'body_full': body,
                'received_at': received_at,
            }
        except Exception as e:
            print(f"Error fetching email {gmail_id}: {e}")
            return None



# ─── HELPERS ──────────────────────────────────────────────────────────────────

def parse_sender(sender_raw):
    if '<' in sender_raw and '>' in sender_raw:
        name = sender_raw[:sender_raw.index('<')].strip().strip('"')
        email_addr = sender_raw[sender_raw.index('<')+1:sender_raw.index('>')]
        return name, email_addr
    return '', sender_raw.strip()


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def extract_body(payload):
    mime_type = payload.get('mimeType', '')
    if mime_type == 'text/plain':
        data = payload.get('body', {}).get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace').strip()
    elif mime_type == 'text/html':
        data = payload.get('body', {}).get('data', '')
        if data:
            html = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            return strip_html(html)
    elif 'multipart' in mime_type:
        for part in payload.get('parts', []):
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace').strip()
        for part in payload.get('parts', []):
            result = extract_body(part)
            if result:
                return result
    return ''


def strip_html(html_text):
    clean = re.sub(r'<[^>]+>', ' ', html_text)
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&')
    clean = clean.replace('&lt;', '<').replace('&gt;', '>')
    return re.sub(r'\s+', ' ', clean).strip()
