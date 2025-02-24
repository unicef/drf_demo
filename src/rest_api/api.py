from django.contrib.auth.models import User
from django.utils.functional import cached_property
from rest_framework import (
    serializers,
    permissions,
    viewsets,
    filters,
    exceptions,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from .models import Office, Program, Plan, Record
from rest_framework_nested.relations import (
    NestedHyperlinkedIdentityField,
)
from rest_framework_nested.viewsets import NestedViewSetMixin


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email"]


class UserFullSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class OfficeSerializer(serializers.HyperlinkedModelSerializer):
    programs = serializers.HyperlinkedIdentityField(
        view_name="office-program-list", lookup_url_kwarg="office_pk"
    )

    class Meta:
        model = Office
        fields = ["pk", "url", "name", "programs"]


class ProgramSerializer(NestedHyperlinkedModelSerializer):
    url = serializers.SerializerMethodField()
    office = serializers.SerializerMethodField()
    plans = NestedHyperlinkedIdentityField(
        view_name="office-program-plan-list",
        lookup_url_kwarg="program_pk",
        parent_lookup_kwargs={"office_pk": "office__pk"},
    )

    class Meta:
        model = Program
        fields = ["pk", "url", "name", "office", "plans"]

    def get_office(self, obj: Program):
        return {
            "id": obj.office.pk,
            "url": reverse(
                "office-detail", args=[obj.office.pk], request=self.context["request"]
            ),
        }

    def get_url(self, obj: Program):
        return reverse(
            "office-program-detail",
            kwargs={"office_pk": obj.office.pk, "pk": obj.pk},
            request=self.context["request"],
        )


class PlanSerializer(NestedHyperlinkedModelSerializer):
    url = serializers.SerializerMethodField()
    program = serializers.SerializerMethodField()
    records = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = ["pk", "url", "name", "program", "records"]

    def get_records(self, obj):
        return reverse(
            "office-program-plan-record-list",
            kwargs={
                "office_pk": obj.program.office.pk,
                "program_pk": obj.program.pk,
                "plan_pk": obj.pk,
            },
            request=self.context["request"],
        )

    def get_program(self, obj: Plan):
        return {
            "id": obj.program.pk,
            "url": reverse(
                "office-program-detail",
                kwargs={"office_pk": obj.program.office.pk, "pk": obj.program.pk},
                request=self.context["request"],
            ),
        }

    def get_url(self, obj):
        return reverse(
            "office-program-plan-detail",
            kwargs={
                "office_pk": obj.program.office.pk,
                "program_pk": obj.program.pk,
                "pk": obj.pk,
            },
            request=self.context["request"],
        )


class RecordSerializer(NestedHyperlinkedModelSerializer):
    url = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ["pk", "url", "name", "plan"]

    def get_plan(self, obj: Record):
        return {
            "id": obj.plan.pk,
            "url": reverse(
                "office-program-plan-detail",
                kwargs={
                    "office_pk": obj.plan.program.office.pk,
                    "program_pk": obj.plan.program.pk,
                    "pk": obj.pk,
                },
                request=self.context["request"],
            ),
        }

    def get_plan2(self, obj: Record):
        return PlanSerializer(obj.plan, context=self.context).data

    def get_plan1(self, obj: Record):
        return reverse(
            "office-program-plan-detail",
            kwargs={
                "office_pk": obj.plan.program.office.pk,
                "program_pk": obj.plan.program.pk,
                "pk": obj.pk,
            },
            request=self.context["request"],
        )

    def get_url(self, obj: Record):
        return reverse(
            "office-program-plan-record-detail",
            kwargs={
                "office_pk": obj.plan.program.office.pk,
                "program_pk": obj.plan.program.pk,
                "plan_pk": obj.plan.pk,
                "pk": obj.pk,
            },
            request=self.context["request"],
        )


ALLOWED_OFFICES = [1,2]
ALLOWED_PROGRAMS = [1,2,3]


def user_has_perm(user, perm, obj=None):
    print(111.1, 3333, perm, obj)
    if obj is None:
        return perm in ["aa", "approve"]
    if isinstance(obj, Office) and obj.pk in ALLOWED_OFFICES:
        return perm in ["aa"]
    if isinstance(obj, Program) and obj.pk in ALLOWED_PROGRAMS:
        if perm == "approve":
            return obj.pk == 1
        return perm in ["aa"]
    return False


class VisibilityFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if view.selected_office:
            pass
        return queryset.filter()


class BasePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return any(
            [user_has_perm(request.user, perm, obj) for perm in view.PERMISSIONS]
        )

    def has_permission(self, request, view):
        return any(
            [user_has_perm(request.user, perm) for perm in view.PERMISSIONS]
        )

class BaseViewSet(viewsets.ModelViewSet):
    authentication_classes = []
    permission_classes = [BasePermission]
    serializer_classes = {"full": UserFullSerializer}
    serializer_classes_by_action = {}
    PERMISSIONS = []

    def get_serializer_class(self):
        if ser := self.serializer_classes_by_action.get(self.action):
            return ser
        elif self.action in ["retrieve", "list"] and (
            ser := self.serializer_classes.get(self.request.GET.get("ser"))
        ):
            return ser
        return super().get_serializer_class()


class SelectedOfficeMixin(BaseViewSet):
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @cached_property
    def selected_office(self):
        return Office.objects.get(pk=self.kwargs["office_pk"])


class SelectedProgramMixin(SelectedOfficeMixin):
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @cached_property
    def selected_office(self) -> Program:
        if not (ret := self.selected_program):
            raise exceptions.NotFound()
        return ret

    @cached_property
    def selected_program(self) -> Program:
        if not (
            ret := Program.objects.select_related("office").get(
                pk=self.kwargs["program_pk"], office_id=self.kwargs["office_pk"]
            )
        ):
            raise exceptions.NotFound()
        return ret


class UserViewSet(BaseViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer


class OfficeViewSet(BaseViewSet):
    queryset = Office.objects.none()
    serializer_class = OfficeSerializer
    PERMISSIONS = ["aa"]

    def get_queryset(self):
        return Office.objects.filter(id__in=ALLOWED_OFFICES)


class ProgramViewSet(SelectedOfficeMixin, NestedViewSetMixin, BaseViewSet):
    queryset = Program.objects.none()
    serializer_class = ProgramSerializer
    parent_lookup_kwargs = {"office_pk": "office"}
    PERMISSIONS = ["aa"]

    def get_queryset(self):
        return self.selected_office.program_set.filter(id__in=ALLOWED_PROGRAMS)


class PlanViewSet(SelectedProgramMixin, BaseViewSet):
    queryset = Plan.objects.none()
    serializer_class = PlanSerializer
    PERMISSIONS = ["aa"
                   ]

    def get_queryset(self):
        return self.selected_program.plan_set.filter()

    def check_object_permissions(self, request, obj):
        # we check perm on the linked program
        return super().check_object_permissions(request, obj.program)

    @action(
        detail=True,
        methods=["get"],
        PERMISSIONS=["approve"],
        permission_classes=[BasePermission]
    )
    def approve(self, request, pk, **kwargs):
        plan: Plan = self.get_object()
        plan.approve()
        return Response(status=status.HTTP_200_OK, data={"message": "Approved"})


class RecordViewSet(SelectedProgramMixin, BaseViewSet):
    queryset = Record.objects.none()
    serializer_class = RecordSerializer
    PERMISSIONS = ["aa"]

    def get_queryset(self):
        return Record.objects.select_related("plan__program__office").filter(
            plan__program=self.selected_program
        )

    def check_object_permissions(self, request, obj):
        # we check perm on the linked program
        return super().check_object_permissions(request, obj.plan.program)
