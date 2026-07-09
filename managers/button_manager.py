from services import (
    buttons_service,
    button_contents_service,
    button_media_service
)


class ButtonManager:

    @staticmethod
    def create(
        menu_id,
        text,
        emoji,
        action_type,
        action_value="",
        row=1,
        position=0,
        admin_only=False,
        visible=True
    ):

        return buttons_service.create(
            menu_id=menu_id,
            text=text,
            emoji=emoji,
            action_type=action_type,
            action_value=action_value,
            row=row,
            position=position,
            admin_only=admin_only,
            visible=visible
        )

    @staticmethod
    def update(button_id, **kwargs):
        return buttons_service.update(button_id, **kwargs)

    @staticmethod
    def delete(button_id):
        return buttons_service.delete(button_id)

    @staticmethod
    def add_content(button_id, content_id, order=0):
        return button_contents_service.add(
            button_id,
            content_id,
            order
        )

    @staticmethod
    def add_media(button_id, media_id, order=0):
        return button_media_service.add(
            button_id,
            media_id,
            order
        )

    @staticmethod
    def contents(button_id):
        return button_contents_service.by_button(button_id)

    @staticmethod
    def media(button_id):
        return button_media_service.by_button(button_id)
