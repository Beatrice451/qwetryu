# utils/utils.py
from aiogram import Bot
from aiogram.fsm.context import FSMContext

from db.db_utils import get_admin_by_tg_id
def is_admin(tg_user_id):
    admin = get_admin_by_tg_id(tg_user_id)
    return admin is not None


async def delete_saved_messages(bot: Bot, chat_id: int, state: FSMContext):
    data = await state.get_data()
    messages = data.get("messages_for_deletion", [])
    print(messages)

    for msg_id in messages:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

    # Очистим список
    await state.update_data(messages_to_delete=[])