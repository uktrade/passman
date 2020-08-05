import factory


class SecretFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Secret-{n+1}")
    username = factory.Sequence(lambda n: f"username-{n+1}")
    url = factory.Sequence(lambda n: f"http://somesite{n+1}/")
    password = "password"
    details = "details"

    class Meta:
        model = "secret.Secret"
