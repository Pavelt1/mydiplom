from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsInGroup(BasePermission):
    def has_permission(self, request, view):
        required_groups = getattr(view, 'required_groups', [])
        user_groups = request.user.groups.values_list('name', flat=True)
        return any(group in user_groups for group in required_groups)
    
class IsOwnerOrReadOnly(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user