from core.models import FriendRequest


def social_counts(request):
    if not request.user.is_authenticated:
        return {'pending_requests_count': 0}
    count = FriendRequest.objects.filter(to_user=request.user, status=FriendRequest.Status.PENDING).count()
    return {'pending_requests_count': count}
