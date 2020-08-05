import factory

from django_otp.plugins.otp_totp.models import TOTPDevice


class GroupFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Group {n+1}")

    class Meta:
        model = "auth.Group"


class UserFactory(factory.django.DjangoModelFactory):
    email = factory.Sequence(lambda n: f"user{n+1}@example.com")
    first_name = factory.Sequence(lambda n: f"Name {n+1}")
    last_name = factory.Sequence(lambda n: f"Surname {n+1}")

    class Meta:
        model = "user.User"

    @factory.post_generation
    def two_factor_enabled(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            TOTPDevice.objects.create(
                user=self, name="test-device", confirmed=True,
            )

    @factory.post_generation
    def create_groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group_name in extracted:
                self.groups.add(GroupFactory(name=group_name))
