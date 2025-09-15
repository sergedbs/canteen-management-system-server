from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.users.models import User

# admin.site.register(User)


class UserAdmin(ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "role")
    exclude = ("deleted_at",)


admin.site.register(User, UserAdmin)
