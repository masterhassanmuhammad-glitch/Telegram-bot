import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.user_service import UserService
from services.session_service import SessionService
from database import DatabaseManager

logger = logging.getLogger(__name__)

class BroadcastPlugin:
    @staticmethod
    def get_broadcast_menu(user_id: int) -> InlineKeyboardMarkup:
        """توليد لوحة تحكم الإذاعة الفوقية للآدمن"""
        keyboard = [
            [InlineKeyboardButton("📝 إذاعة نصية", callback_data="bc_type_text"),
             InlineKeyboardButton("🖼️ إذاعة وسائط (صورة/ملف)", callback_data="bc_type_media")],
            [InlineKeyboardButton("📊 إذاعة استطلاع رأي (Poll)", callback_data="bc_type_poll")],
            [InlineKeyboardButton("🔙 عودة للوحة التحكم", callback_data="btn_back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """معالجة الضغط على أزرار قسم الإذاعة"""
        query = update.callback_query
        user_id = query.from_user.id

        # التحقق من أن المستخدم آدمن وله صلاحية الإذاعة
        if not UserService.is_admin(user_id):
            await query.answer("✖️ عذراً، لا تمتلك صلاحيات الإذاعة.", show_alert=True)
            return

        if data == "manage_broadcast":
            reply_markup = BroadcastPlugin.get_broadcast_menu(user_id)
            await query.edit_message_text(
                text="📢 **قسم الإذاعة الشاملة:**\n\nاختر نوع الإذاعة التي تريد إرسالها للمستخدمين الآن:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return

        # تحديد نوع الإذاعة وتغيير حالة الجلسة (FSM) لانتظار المدخلات
        if data == "bc_type_text":
            SessionService.update_session(user_id, state="BC_WAITING_TEXT")
            await query.edit_message_text(
                text="📝 حسناً، أرسل الآن **النص** الذي تريد إذاعته لجميع المستخدمين بـرسالة واحدة:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="manage_broadcast")]])
            )
        elif data == "bc_type_media":
            SessionService.update_session(user_id, state="BC_WAITING_MEDIA")
            await query.edit_message_text(
                text="🖼️ حسناً، قم برفع **الوسائط** (صورة، فيديو، ملف، صوت) مع الشرح (Caption) ليتم توجيهها فوراً:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="manage_broadcast")]])
            )

    @staticmethod
    async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
        """استقبال المحتوى الفعلي المراد إذاعته من الآدمن وإرساله بالخلفية بكفاءة"""
        user_id = update.effective_user.id
        state = session['current_state']
        
        # جلب قائمة كافة مستخدمي البوت المسجلين في Neon
        users_list = DatabaseManager.execute_query("SELECT user_id FROM users WHERE is_banned = False", fetch='all')
        if not users_list:
            await context.bot.send_message(chat_id=user_id, text="❌ لا يوجد مستخدمين مسجلين لإرسال الإذاعة إليهم.")
            return

        # تعديل الرسالة الفوقية لتبين للآدمن بدء العملية
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=session['last_message_id'],
            text=f"⏳ جاري بدء الإذاعة إلى `{len(users_list)}` مستخدم... يرجى الانتظار.",
            parse_mode="Markdown"
        )

        success_count = 0
        fail_count = 0

        # حلقة الإرسال مع تفادي الحظر من سيرفرات تليجرام (Anti-Flood Rate Limit)
        for u in users_list:
            target_id = u['user_id']
            try:
                if state == "BC_WAITING_TEXT":
                    await context.bot.send_message(chat_id=target_id, text=update.message.text)
                elif state == "BC_WAITING_MEDIA":
                    # التحقق من نوع الميديا المرفوعة عبر الـ file_id
                    if update.message.photo:
                        await context.bot.send_photo(chat_id=target_id, photo=update.message.photo[-1].file_id, caption=update.message.caption)
                    elif update.message.document:
                        await context.bot.send_document(chat_id=target_id, document=update.message.document.file_id, caption=update.message.caption)
                    elif update.message.video:
                        await context.bot.send_video(chat_id=target_id, video=update.message.video.file_id, caption=update.message.caption)
                
                success_count += 1
                # تأخير بسيط جداً (0.05 ثانية) لحماية البوت من الفلود
                await asyncio.sleep(0.05)
            except Exception:
                fail_count += 1

        # تصفير حالة الجلسة والعودة للرئيسية
        SessionService.clear_session_context(user_id)
        reply_markup = BroadcastPlugin.get_broadcast_menu(user_id)
        
        # تحديث نفس الرسالة الفوقية بنتيجة تقرير الإذاعة النهائي!
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=session['last_message_id'],
            text=f"📢 **تقرير انتهاء الإذاعة الشاملة:**\n\n✅ تم الإرسال بنجاح إلى: `{success_count}` مستخدم.\n✖️ فشل الإرسال (بوت محظور): `{fail_count}`.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
      )
          
