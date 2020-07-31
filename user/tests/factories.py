import factory


from django_otp.plugins.otp_totp.models import TOTPDevice


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
