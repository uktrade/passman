import factory


class UserFactory(factory.django.DjangoModelFactory):
    email = factory.Sequence(lambda n: f"user{n+1}@example.com")
    first_name = factory.Sequence(lambda n: f"Name {n+1}")
    last_name = factory.Sequence(lambda n: f"Surname {n+1}")

    class Meta:
        model = "user.User"
