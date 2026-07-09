from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from services import (
    buttons_service,
    menus_service,
    contents_service,
    media_service,
    button_contents_service,
    button_media_service,  # تم إضافة الاستيراد الجديد هنا
)

from ui.renderer import render_menu


async def callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    if not query.data.startswith("btn:"):
        return

    button_id = int(query.data.split(":")[1])

    button = buttons_service.get(button_id)

    if not button:
        return

    action = button["action_type"]
    value = button["action_value"]

    # فتح قائمة
    if action == "MENU":
        await render_menu(update, int(value))
        return

    # إرسال محتوى نصي ووسائط (التعديل الجديد)
    if action == "CONTENT":
        contents = button_contents_service.by_button(
            button["id"]
        )

        for content in contents:
            if content["content_type"] == "TEXT":
                await query.message.reply_text(content["body"])

        media_list = button_media_service.by_button(
            button["id"]
        )

        for media in media_list:
            media_type = media["media_type"]

            if media_type == "photo":
                await query.message.reply_photo(
                    media["file_id"],
                    caption=media["caption"] or ""
                )

            elif media_type == "video":
                await query.message.reply_video(
                    media["file_id"],
                    caption=media["caption"] or ""
                )

            elif media_type == "document":
                await query.message.reply_document(
                    media["file_id"],
                    caption=media["caption"] or ""
                )

            elif media_type == "audio":
                await query.message.reply_audio(
                    media["file_id"],
                    caption=media["caption"] or ""
                )

            elif media_type == "voice":
                await query.message.reply_voice(
                    media["file_id"],
                    caption=media["caption"] or ""
                )

        return

    # إرسال ملف (منفرد)
    if action == "MEDIA":

        media = media_service.get(int(value))

        if not media:
            return

        media_type = media["media_type"]

        if media_type == "document":
            await query.message.reply_document(
                media["file_id"],
                caption=media["caption"] or ""
            )

        elif media_type == "photo":
            await query.message.reply_photo(
                media["file_id"],
                caption=media["caption"] or ""
            )

        elif media_type == "video":
            await query.message.reply_video(
                media["file_id"],
                caption=media["caption"] or ""
            )

        elif media_type == "audio":
            await query.message.reply_audio(
                media["file_id"],
                caption=media["caption"] or ""
            )

        return


def register(application):
    application.add_handler(
        CallbackQueryHandler(callback)
        )
    
