from rest_framework.permissions import BasePermission
from .models import Membership, Role


ROLE_HIERARCHY = [
    Role.CLIENT_VIEWER,
    Role.WRITER,
    Role.DESIGNER,
    Role.REVIEWER,
    Role.PROJECT_LEAD,
    Role.STUDIO_ADMIN,
]

def get_membership(user, studio_id):
    try:
        return Membership.objects.get(user=user, studio_id=studio_id)
    except Membership.DoesNotExist:
        return None

def has_role(user, studio_id, *roles):
    m = get_membership(user, studio_id)
    return m and m.role in roles

def has_min_role(user, studio_id, min_role):
    m = get_membership(user, studio_id)
    if not m:
        return False
    return ROLE_HIERARCHY.index(m.role) >= ROLE_HIERARCHY.index(min_role)



class IsStudioMember(BasePermission):
    def has_permission(self, request, view):
        studio_id = view.kwargs.get('studio_id')
        return bool(get_membership(request.user, studio_id))

class IsStudioAdmin(BasePermission):
    def has_permission(self, request, view):
        studio_id = view.kwargs.get('studio_id')
        return has_role(request.user, studio_id, Role.STUDIO_ADMIN)

class IsProjectLeadOrAbove(BasePermission):
    def has_permission(self, request, view):
        studio_id = view.kwargs.get('studio_id')
        return has_min_role(request.user, studio_id, Role.PROJECT_LEAD)

class IsReviewerOrAbove(BasePermission):
    def has_permission(self, request, view):
        studio_id = view.kwargs.get('studio_id')
        return has_min_role(request.user, studio_id, Role.REVIEWER)

class CannotWrite(BasePermission):
    def has_permission(self, request, view):
        from rest_framework.request import Request
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        studio_id = view.kwargs.get('studio_id')
        return has_min_role(request.user, studio_id, Role.WRITER)