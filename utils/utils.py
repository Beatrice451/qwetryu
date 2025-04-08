# utils/utils.py

from db.db_utils import get_admin_by_tg_id

def is_admin(tg_user_id):
    admin = get_admin_by_tg_id(tg_user_id)
    return admin is not None