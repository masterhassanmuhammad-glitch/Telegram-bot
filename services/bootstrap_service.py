from repositories import (
    bootstrap_repository,
    settings_repository
)


def initialize():

    if not bootstrap_repository.has_root():

        bootstrap_repository.create_root()

        settings_repository.set(
            "bot_name",
            "MedicalBot"
        )

        settings_repository.set(
            "welcome_message",
            "🏥 مرحباً بك"
        )

        settings_repository.set(
            "buttons_per_row",
            "2"
        )
