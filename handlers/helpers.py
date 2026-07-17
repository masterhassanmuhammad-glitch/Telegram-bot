from telebot import types

from config import ADMIN_IDS, OWNER_ID
from database import execute_query, get_user_state

# ==========================================================
# صلاحيات المشرفين
# ==========================================================

def get_permissions(user_id):
    """
    ترجع جميع صلاحيات المستخدم.
    """

    # المالك الأساسي
    if OWNER_ID and user_id == OWNER_ID:
        return {
            "is_admin": True,
            "is_owner": True,
            "can_settings": True,
            "can_broadcast": True,
            "can_feedback": True,
            "can_count": True,
        }

    # المشرفون من قاعدة البيانات
    result = execute_query(
        """
        SELECT
            can_settings,
            can_broadcast,
            can_feedback,
            can_count
        FROM admins
        WHERE admin_id = %s;
        """,
        (user_id,),
        fetch=True,
    )

    if result:
        row = result[0]
        return {
            "is_admin": True,
            "is_owner": False,
            "can_settings": row[0],
            "can_broadcast": row[1],
            "can_feedback": row[2],
            "can_count": row[3],
        }

    # المشرفون الموجودون في config.py
    if user_id in ADMIN_IDS:
        return {
            "is_admin": True,
            "is_owner": False,
            "can_settings": True,
            "can_broadcast": True,
            "can_feedback": True,
            "can_count": True,
        }

    # مستخدم عادي
    return {
        "is_admin": False,
        "is_owner": False,
        "can_settings": False,
        "can_broadcast": False,
        "can_feedback": False,
        "can_count": False,
    }


# ==========================================================
# فلتر حالة المستخدم (State Filter)
# ==========================================================

def check_state(state_name):
    """
    يستخدم مع message_handler للتحقق من حالة المستخدم.
    """

    def wrapper(message):
        state = get_user_state(message.from_user.id)

        if not state:
            return False

        return state[0] == state_name

    return wrapper


# ==========================================================
# القائمة النشطة لكل مستخدم
# ==========================================================

# يتم حفظ آخر رسالة قائمة تم إرسالها لكل مستخدم
# حتى نستطيع حذفها عند فتح قائمة جديدة.
active_menus = {}
# ==========================================================
# إرسال الملفات ثم إعادة إنشاء القائمة
# ==========================================================

def send_files_and_recreate_menu(
    bot,
    chat_id,
    files_list,
    menu_text,
    reply_markup
):
    """
    تحذف القائمة القديمة، ثم ترسل جميع الملفات،
    ثم تنشئ قائمة جديدة أسفل الملفات مباشرة.
    """

    # حذف القائمة القديمة
    if chat_id in active_menus:
        try:
            bot.delete_message(chat_id, active_menus[chat_id])
        except Exception:
            pass

    # إرسال الملفات
    for item in files_list:

        try:
            # دعم الشكل الجديد:
            # (file_id, file_type, caption)
            if len(item) >= 3:
                file_id, file_type, caption = item[:3]

            # دعم الشكل القديم:
            # file_id فقط
            else:
                file_id = item
                file_type = "document"
                caption = None

            if file_type == "photo":
                bot.send_photo(
                    chat_id,
                    file_id,
                    caption=caption
                )

            elif file_type == "video":
                bot.send_video(
                    chat_id,
                    file_id,
                    caption=caption
                )

            elif file_type == "audio":
                bot.send_audio(
                    chat_id,
                    file_id,
                    caption=caption
                )

            elif file_type == "voice":
                bot.send_voice(
                    chat_id,
                    file_id
                )

            elif file_type == "animation":
                bot.send_animation(
                    chat_id,
                    file_id,
                    caption=caption
                )

            else:
                bot.send_document(
                    chat_id,
                    file_id,
                    caption=caption
                )

        except Exception as e:
            print(
                f"[HELPERS] Error sending file "
                f"{file_id}: {e}"
            )

    # إرسال القائمة الجديدة
    try:
        msg = bot.send_message(
            chat_id,
            menu_text,
            reply_markup=reply_markup
        )

        active_menus[chat_id] = msg.message_id

    except Exception as e:
        print(
            f"[HELPERS] Error creating menu: {e}"
            )
        # ==========================================================
# بيانات مجموعة الدفعة
# ==========================================================

# ضع Chat ID للمجموعة الخاصة
# مثال:
# BATCH_GROUP_ID = -1001234567890

BATCH_GROUP_ID = -1003244121210

# رابط الدعوة للمجموعة
GROUP_LINK = "https://t.me/+yB74ZDAEckM5NGE0"


# ==========================================================
# التحقق من عضوية المستخدم
# ==========================================================

def is_user_in_batch(bot, user_id):
    """
    ترجع True إذا كان المستخدم عضواً في المجموعة.
    """

    try:
        member = bot.get_chat_member(
            BATCH_GROUP_ID,
            user_id
        )

        return member.status in (
            "creator",
            "administrator",
            "member",
        )

    except Exception as e:
        print(
            f"[HELPERS] Membership check failed: {e}"
        )
        return False


# ==========================================================
# إرسال رسالة الانضمام للمجموعة
# ==========================================================

def send_join_request_menu(bot, chat_id):
    """
    تظهر للمستخدم إذا لم يكن عضواً في المجموعة.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        types.InlineKeyboardButton(
            "📢 الانضمام إلى مجموعة الدفعة",
            url=GROUP_LINK,
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ تم الانضمام - تحقق الآن",
            callback_data="check_membership",
        )
    )

    text = (
        "⚠️ *هذا البوت مخصص لطلاب الدفعة فقط.*\n\n"
        "يرجى الانضمام إلى مجموعة الدفعة أولاً، "
        "ثم اضغط على زر *تم الانضمام - تحقق الآن*."
    )

    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
