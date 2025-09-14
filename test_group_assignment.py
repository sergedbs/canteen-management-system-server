#!/usr/bin/env python
"""
Test script to verify the group assignment logic works correctly.
Run this with: python manage.py shell < test_group_assignment.py
"""

from django.contrib.auth.models import Group

from apps.common.constants import ROLE_GROUP_NAMES, UserRole
from apps.users.models import User


def test_group_assignment():
    print("Testing Group Assignment Logic...")

    # Groups should already exist from migrations, but create them for testing
    for group_name in ROLE_GROUP_NAMES:
        Group.objects.get_or_create(name=group_name)

    # Test 1: Create admin user
    print("\n1. Testing Admin User:")
    admin = User.objects.create_user(
        email="admin@utm.md", password="testpass123", role=UserRole.ADMIN, is_verified=True
    )
    print(f"Admin groups: {list(admin.groups.values_list('name', flat=True))}")
    print("Expected group: admin")
    print(f"Correct: {admin.is_in_role_group('admin')}")

    # Test 2: Create staff user
    print("\n2. Testing Staff User:")
    staff = User.objects.create_user(
        email="staff@utm.md", password="testpass123", role=UserRole.STAFF, is_verified=True
    )
    print(f"Staff groups: {list(staff.groups.values_list('name', flat=True))}")
    print("Expected group: staff")
    print(f"Correct: {staff.is_in_role_group('staff')}")

    # Test 3: Create unverified customer
    print("\n3. Testing Unverified Customer:")
    unverified_customer = User.objects.create_user(
        email="customer@utm.md", password="testpass123", role=UserRole.CUSTOMER, is_verified=False
    )
    print(f"Unverified customer groups: {list(unverified_customer.groups.values_list('name', flat=True))}")
    print("Expected group: customer_unverified")
    print(f"Correct: {unverified_customer.is_in_role_group('customer_unverified')}")

    # Test 4: Verify customer (simulate email verification)
    print("\n4. Testing Customer Verification:")
    unverified_customer.is_verified = True
    unverified_customer.save()  # This should trigger group reassignment
    print(f"Verified customer groups: {list(unverified_customer.groups.values_list('name', flat=True))}")
    print("Expected group: customer_verified")
    print(f"Correct: {unverified_customer.is_in_role_group('customer_verified')}")

    # Test 5: Test role change
    print("\n5. Testing Role Change (Staff -> Admin):")
    staff.role = UserRole.ADMIN
    staff.save()  # This should trigger group reassignment
    print(f"Staff->Admin groups: {list(staff.groups.values_list('name', flat=True))}")
    print("Expected group: admin")
    print(f"Correct: {staff.is_in_role_group('admin')}")

    # Test 6: Test that non-role groups are preserved
    print("\n6. Testing Non-Role Group Preservation:")
    custom_group = Group.objects.create(name="custom_group")
    admin.groups.add(custom_group)
    admin.role = UserRole.STAFF
    admin.save()  # This should trigger group reassignment
    print(f"Admin->Staff groups: {list(admin.groups.values_list('name', flat=True))}")
    print(f"Has custom group: {admin.is_in_role_group('custom_group')}")
    print(f"Has staff group: {admin.is_in_role_group('staff')}")

    print("\n✅ Group assignment tests completed!")

    # Cleanup
    User.objects.all().delete()
    Group.objects.filter(name__in=ROLE_GROUP_NAMES).delete()
    Group.objects.filter(name="custom_group").delete()


if __name__ == "__main__":
    test_group_assignment()
