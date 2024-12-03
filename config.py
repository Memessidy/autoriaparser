from dotenv import find_dotenv, load_dotenv
import os

load_dotenv(find_dotenv())

# aiogram bot token
token = os.getenv('TOKEN')

# sqlite database
database_name = os.getenv('DB_LITE')

# parser
url = ('https://auto.ria.com/uk/search/?indexName=auto,order_auto,newauto_search&categories.main.id='
       '1&brand.id[0]=79&model.id[0]=2104&damage.not=0&country.import.usa.not=0')

cars_sections_in_page = 100
current_timezone = 'Europe/Kiev'