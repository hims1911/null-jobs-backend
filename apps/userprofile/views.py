from rest_framework import (
    viewsets, 
    permissions, 
    status, 
    exceptions,
    parsers
)
from django.db.models import Case, When, Value, BooleanField
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.userprofile.models import UserProfile
from apps.accounts import permissions as custom_permissions
from apps.userprofile.serializers import UserProfileSerializer, UploadFilesSerializer
from apps.utils.responses import InternalServerError, Response201Created


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    UserProfile object viewsets
    API: /api/v1/user
    Database: tbl_user_profile
    Functions:
        1. create or update user
        2. list users/specific user
        3. check jobs applied by a specific user
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["user profile"])
    def create(self, request, *args, **kwargs):
        """ A job seeker has a user profile so when a user 
        wants to update a user this has to be accessed only by
        job seeker whose profile it is
        """
        user = request.user

        # check if the user is of valid type only the 
        # job seekers can update their profiles
        if user.user_type == "Employer":
            raise exceptions.PermissionDenied()  

        serializer = UserProfileSerializer(data = request.data)
        serializer.is_valid(raise_exception = True)

        # updating user name when its not the same as the previous name
        if request.user.name != serializer.get_name():
            print("Updating the name with {}".format(serializer.name))
            # only name can be changed in the auth user itself
            users_updated = User.objects.filter(
                id = request.user.id
            ).update(name = serializer.get_name())

            if not users_updated:
                raise InternalServerError()
            
        # updating user profile data
        user_profile_data = serializer.data
        user_profile, created = UserProfile.objects.get_or_create(
            user=user, 
            defaults=user_profile_data
        )

        # updating the user profile wiht the rest of the data
        if not created:
            for key, value in user_profile_data.items():
                setattr(user_profile, key, value)

        user_profile.save()

        return Response(
            UserProfileSerializer(user_profile).data, 
            status = status.HTTP_201_CREATED
        )


    @extend_schema(tags=["user profile"])
    def list(self, request):
        """List job seeker profiles for the employers to view
        Rest users dont have the access to this view yet
        """
        if request.user.user_type == "Job Seeker":
            raise exceptions.PermissionDenied()
        
        user_profiles = UserProfile.objects.annotate(
            is_favorite=Case(
                When(favoriteprofiles__employer=request.user, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        )

        return Response(
            UserProfileSerializer(user_profiles, many=True).data, 
            status = status.HTTP_200_OK
        )

    @extend_schema(tags=["user profile"])
    def retrieve(self, request, pk = None):
        instance = self.get_object()

        # TODO: the object should also contain if the profile is shortlisted by the
        # employer fetching the data
        return Response(UserProfileSerializer(instance).data)

    @extend_schema(tags=["user profile"])
    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        API: /user/me
        Returns user profile data in the response based on
        user_id present in the Authorization Header
        """
        # this view is for job seekers for their profile
        if request.user.user_type == "Employer":
            raise exceptions.PermissionDenied()
        
        user_profile = UserProfile.objects.get(user = request.user)
        print(user_profile.resume)
        
        return Response(
            UserProfileSerializer(user_profile).data,
            status = status.HTTP_200_OK
        )
    

    @extend_schema(exclude=True)
    def destroy(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("DELETE")
    
    @extend_schema(tags=["user profile"], exclude=True)
    def update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PUT")
    
    
class UplaodDocumentsView(APIView):
    permission_classes = [permissions.IsAuthenticated, custom_permissions.IsJobSeeker]
    parser_classes = [parsers.MultiPartParser]

    @extend_schema(request = UploadFilesSerializer, tags=["user profile"])
    def post(self, request):
        serializer = UploadFilesSerializer(data = request.data)
        serializer.is_valid(raise_exception = True)

        try:
            user_profile = UserProfile.objects.get(user = request.user)
        except UserProfile.DoesNotExist:
            raise exceptions.NotFound("The profile for this user is absent")
        except Exception as e:
            print(e)
            raise InternalServerError(str(e))
        
        # set is_profile_completed to done
        if "resume" in serializer.data:
            users_updated = User.objects.filter(
                id = request.user.id
            ).update(is_profile_completed = True)

            user_profile.resume = serializer.data.get("resume")

        if "cover_letter" in  serializer.data:
            user_profile.cover_letter = serializer.data.get("cover_letter")

        if "profile_picture" in serializer.data:
            user_profile.profile_picture = serializer.data.get("profile_picture")

        user_profile.save()

        return Response201Created(request.user.id)
