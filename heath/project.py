class Project:
    def __init__(
        self, key: str, name: str = "", description: str = "", all_day: bool = False
    ) -> None:
        self.key = key
        self.name = name
        self.description = description
        self.all_day = all_day
