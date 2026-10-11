from django.db.models import Q

from accounts.permissions import get_staff_profile, get_user_role


def get_user_lab_department(user):
    """
    Return the laboratory department assigned to the current user.
    """
    profile = get_staff_profile(user)

    if not profile:
        return None

    return profile.department


def is_lab_manager(user):
    """
    System administrators and hospital managers have full laboratory access.
    """
    role = get_user_role(user)
    return role in {"ADMIN", "MANAGER"}


def is_central_laboratory_user(user):
    """
    Central Laboratory users have broad laboratory access.
    """
    department = get_user_lab_department(user)

    if not department:
        return False

    return department.code == "LAB"


def laboratory_department_filter(user, field_name="department"):
    """
    Build a Django Q object restricting data to the user's laboratory
    department.

    ADMIN / MANAGER:
        unrestricted.

    Central Laboratory:
        unrestricted laboratory department scope.

    Other LAB users:
        only their assigned department.
    """
    if is_lab_manager(user):
        return Q()

    if is_central_laboratory_user(user):
        return Q()

    department = get_user_lab_department(user)

    if not department:
        return Q(pk__isnull=True)

    return Q(**{f"{field_name}_id": department.id})


def user_can_access_laboratory_department(user, department):
    """
    Check whether the current user can access a laboratory department.
    """
    if is_lab_manager(user):
        return True

    if not department:
        return False

    user_department = get_user_lab_department(user)

    if not user_department:
        return False

    if user_department.code == "LAB":
        return True

    return user_department.id == department.id


def user_can_access_test(user, test):
    """
    Check access to a laboratory test based on the user's laboratory department.

    Central Laboratory (code=LAB) and managers can access every test,
    including legacy tests that do not have a department.
    """

    # System/Hospital managers
    if is_lab_manager(user):
        return True

    # Central Laboratory has access to ALL laboratory tests,
    # including tests with no department assigned.
    if is_central_laboratory_user(user):
        return True

    # No test
    if not test:
        return False

    # Department laboratory users can access only their department.
    return user_can_access_laboratory_department(
        user,
        test.department,
    )



def user_can_access_order(user, order):
    """
    Check access to a laboratory order.

    Central Laboratory and managers can access all orders.
    Other laboratory users can access orders containing tests
    belonging to their laboratory department.
    """
    if is_lab_manager(user):
        return True

    user_department = get_user_lab_department(user)

    if not user_department:
        return False

    if user_department.code == "LAB":
        return True

    items = order.items.select_related("test__department").all()

    return any(
        item.test.department_id == user_department.id
        for item in items
    )


def user_can_access_order_item(user, item):
    """
    Check access to a specific laboratory order item.
    """
    if is_lab_manager(user):
        return True

    user_department = get_user_lab_department(user)

    if not user_department:
        return False

    if user_department.code == "LAB":
        return True

    if not item.test_id:
        return False

    return item.test.department_id == user_department.id
