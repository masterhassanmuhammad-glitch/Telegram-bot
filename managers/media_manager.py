from services import media_service


class MediaManager:

    @staticmethod
    def save_document(message):

        document = message.document

        return media_service.create(
            media_type="document",
            file_id=document.file_id,
            file_unique_id=document.file_unique_id,
            file_name=document.file_name,
            mime_type=document.mime_type,
            file_size=document.file_size,
            caption=message.caption or ""
        )

    @staticmethod
    def save_photo(message):

        photo = message.photo[-1]

        return media_service.create(
            media_type="photo",
            file_id=photo.file_id,
            file_unique_id=photo.file_unique_id,
            file_name="",
            mime_type="image/jpeg",
            file_size=photo.file_size,
            caption=message.caption or ""
        )

    @staticmethod
    def save_video(message):

        video = message.video

        return media_service.create(
            media_type="video",
            file_id=video.file_id,
            file_unique_id=video.file_unique_id,
            file_name=video.file_name or "",
            mime_type=video.mime_type,
            file_size=video.file_size,
            caption=message.caption or ""
        )

    @staticmethod
    def save_audio(message):

        audio = message.audio

        return media_service.create(
            media_type="audio",
            file_id=audio.file_id,
            file_unique_id=audio.file_unique_id,
            file_name=audio.file_name or "",
            mime_type=audio.mime_type,
            file_size=audio.file_size,
            caption=message.caption or ""
        )

    @staticmethod
    def save_voice(message):

        voice = message.voice

        return media_service.create(
            media_type="voice",
            file_id=voice.file_id,
            file_unique_id=voice.file_unique_id,
            file_name="",
            mime_type="audio/ogg",
            file_size=voice.file_size,
            caption=""
      )
