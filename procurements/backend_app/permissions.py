from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsShopUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.type == 'shop'

class IsOrderOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user