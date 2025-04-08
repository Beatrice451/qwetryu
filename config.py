# import os
#
# BOT_TOKEN = os.environ.get("7870605879:AAEj5XKR9Z7zir7e1qD6bVSobS2HV4AtLFQ")
# DB_HOST = os.environ.get("localhost")
# DB_USER = os.environ.get("5Vkusov_adm")
# DB_PASSWORD = os.environ.get("5Vkusov5555")
# DB_NAME = os.environ.get("fivevkusov")
# ADMIN_PASSWORD = os.environ.get("5Vkusov5555")
# ADMIN_USER_ID = int(os.environ.get("xercesm", 0))

### Это всё конечно хорошо, но я решил использовать файл .env
from dotenv import load_dotenv
import os
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID")

