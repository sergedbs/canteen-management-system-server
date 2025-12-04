from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path

from apps.authentication.session_service import SessionService

User = get_user_model()


def get_admin_urls(admin_site):
    """Add custom session admin URL to the admin site."""

    def sessions_view(request):
        """View all active sessions from Redis."""
        # Get filter parameters
        user_filter = request.GET.get("user", "")

        # Get all users for the filter dropdown
        all_users = User.objects.all().order_by("email")

        all_sessions = []

        if user_filter:
            # Filter by specific user
            try:
                user = User.objects.get(id=user_filter)
                sessions = SessionService.list_sessions(user.id)
                for session in sessions:
                    session["user_email"] = user.email
                    session["user_id_display"] = str(user.id)
                    all_sessions.append(session)
            except User.DoesNotExist:
                pass
        else:
            # Show all sessions
            for user in all_users:
                sessions = SessionService.list_sessions(user.id)
                for session in sessions:
                    session["user_email"] = user.email
                    session["user_id_display"] = str(user.id)
                    all_sessions.append(session)

        context = {
            **admin_site.each_context(request),
            "title": "Active Sessions",
            "sessions": all_sessions,
            "all_users": all_users,
            "user_filter": user_filter,
        }
        return TemplateResponse(
            request,
            "admin/authentication/usersession/change_list.html",
            context,
        )

    def revoke_session_view(request, jti):
        """Revoke a specific session."""
        SessionService.revoke_session(jti)
        messages.success(request, f"Session {jti[:8]}... has been revoked.")

        # Redirect back to sessions list, preserving any filters
        redirect_url = request.META.get("HTTP_REFERER", "/admin/authentication/sessions/")
        return HttpResponseRedirect(redirect_url)

    return [
        path("authentication/sessions/", admin_site.admin_view(sessions_view), name="auth_sessions"),
        path(
            "authentication/sessions/revoke/<str:jti>/",
            admin_site.admin_view(revoke_session_view),
            name="auth_session_revoke",
        ),
    ]


# Monkey-patch the default admin site to include our custom URLs
original_get_urls = admin.site.get_urls


def custom_get_urls():
    custom_urls = get_admin_urls(admin.site)
    return custom_urls + original_get_urls()


admin.site.get_urls = custom_get_urls
