from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Studio, Membership
from .serializers import StudioSerializer, MembershipSerializer
from .permissions import IsStudioAdmin, IsStudioMember

class StudioViewSet(viewsets.ModelViewSet):
    serializer_class = StudioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Studio.objects.filter(
            memberships__user=self.request.user,
            is_active=True
        ).distinct()

    def perform_create(self, serializer):
        studio = serializer.save()
        Membership.objects.create(
            studio=studio,
            user=self.request.user,
            role='studio_admin'
        )

    @action(detail=True, methods=['get'], permission_classes=[IsStudioMember])
    def members(self, request, pk=None):
        studio = self.get_object()
        qs = studio.memberships.select_related('user').all()
        return Response(MembershipSerializer(qs, many=True).data)

    @action(detail=True, methods=['patch'], url_path='members/(?P<membership_id>[^/.]+)',
            permission_classes=[IsStudioAdmin])
    def update_member_role(self, request, pk=None, membership_id=None):
        membership = get_object_or_404(Membership, id=membership_id, studio_id=pk)
        serializer = MembershipSerializer(membership, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='members/(?P<membership_id>[^/.]+)',
            permission_classes=[IsStudioAdmin])
    def remove_member(self, request, pk=None, membership_id=None):
        membership = get_object_or_404(Membership, id=membership_id, studio_id=pk)
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[IsStudioAdmin])
    def add_member(self, request, pk=None):
        studio = self.get_object()
        email = request.data.get('email')
        role  = request.data.get('role', 'designer')

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'No user with that email exists.'}, status=404)

        membership, created = Membership.objects.get_or_create(
            studio=studio,
            user=user,
            defaults={'role': role, 'invited_by': request.user}
        )
        if not created:
            return Response({'detail': 'User is already a member.'}, status=400)

        return Response(MembershipSerializer(membership).data, status=201)

