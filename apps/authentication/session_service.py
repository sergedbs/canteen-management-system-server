import json
from datetime import timedelta

from django.utils import timezone

from apps.common.redis_client import redis_client

# Match this with SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] in settings
SESSION_TTL = timedelta(days=7)


class SessionService:
    @staticmethod
    def _get_session_key(jti):
        return f"session:{jti}"

    @staticmethod
    def _get_user_sessions_key(user_id):
        return f"user:{user_id}:sessions"

    @staticmethod
    def create_session(user_id, jti, request):
        """Create a new session in Redis whitelist."""
        ip = request.META.get("REMOTE_ADDR", "")
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]

        user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")

        data = {
            "user_id": str(user_id),
            "ip": ip,
            "user_agent": user_agent,
            "created_at": timezone.now().isoformat(),
            "last_used_at": timezone.now().isoformat(),
        }

        # Store session data
        key = SessionService._get_session_key(jti)
        redis_client.setex(key, SESSION_TTL, json.dumps(data))

        # Add to user's session index
        user_key = SessionService._get_user_sessions_key(user_id)
        redis_client.sadd(user_key, jti)
        redis_client.expire(user_key, SESSION_TTL)

    @staticmethod
    def validate_session(jti):
        """Check if session exists in whitelist."""
        key = SessionService._get_session_key(jti)
        return redis_client.exists(key)

    @staticmethod
    def rotate_session(old_jti, new_jti):
        """Rotate session on token refresh (delete old, create new with updated time)."""
        old_key = SessionService._get_session_key(old_jti)
        data_json = redis_client.get(old_key)

        if not data_json:
            # If old session missing, we can't rotate.
            # The view should have validated existence before calling this.
            return

        data = json.loads(data_json)
        user_id = data["user_id"]

        # Update last used
        data["last_used_at"] = timezone.now().isoformat()

        # Store new session
        new_key = SessionService._get_session_key(new_jti)
        redis_client.setex(new_key, SESSION_TTL, json.dumps(data))

        # Update user index
        user_key = SessionService._get_user_sessions_key(user_id)
        redis_client.srem(user_key, old_jti)
        redis_client.sadd(user_key, new_jti)
        redis_client.expire(user_key, SESSION_TTL)

        # Delete old session
        redis_client.delete(old_key)

    @staticmethod
    def revoke_session(jti):
        """Revoke a specific session."""
        key = SessionService._get_session_key(jti)
        data_json = redis_client.get(key)

        if data_json:
            data = json.loads(data_json)
            user_id = data["user_id"]

            # Remove from user index
            user_key = SessionService._get_user_sessions_key(user_id)
            redis_client.srem(user_key, jti)

            # Delete session data
            redis_client.delete(key)

    @staticmethod
    def list_sessions(user_id):
        """List all active sessions for a user."""
        user_key = SessionService._get_user_sessions_key(user_id)
        jtis = redis_client.smembers(user_key)

        sessions = []
        invalid_jtis = []

        for jti in jtis:
            key = SessionService._get_session_key(jti)
            data_json = redis_client.get(key)
            if data_json:
                session = json.loads(data_json)
                session["jti"] = jti
                sessions.append(session)
            else:
                invalid_jtis.append(jti)

        # Cleanup orphaned JTIs in the index
        if invalid_jtis:
            redis_client.srem(user_key, *invalid_jtis)

        return sessions

    @staticmethod
    def revoke_all_other_sessions(user_id, current_jti):
        """Revoke all sessions except the current one."""
        sessions = SessionService.list_sessions(user_id)
        for session in sessions:
            if session["jti"] != current_jti:
                SessionService.revoke_session(session["jti"])
