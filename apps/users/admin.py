from django.contrib import admin

from apps.users.models import User

# admin.site.register(User)


class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "role")


admin.site.register(User, UserAdmin)
