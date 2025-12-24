from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Review
from .serializers import ReviewSerializer

class ReviewListCreateView(generics.ListCreateAPIView):
    queryset = Review.objects.filter(is_published=True).order_by('-date_created')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ReviewDeleteView(generics.DestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response({'error': 'У вас нет разрешения на удаление этого отзыва.'}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)