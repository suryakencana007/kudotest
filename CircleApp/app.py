from baka import Baka
from baka.log import log
from baka.settings import EnvSetting, database_url
from baka_tenshi.config import CONFIG as tenshi
from baka_armor.config import CONFIG as armor


ENV = [
    EnvSetting('url', 'DATABASE_URL', type=database_url),
    EnvSetting('sqlalchemy.url', 'DATABASE_URL', type=database_url)
]
options = {
    'LOGGING': True,
    'secret_key': '',
    'env': ENV
}
app = Baka(__name__, **options)

# untuk config env baka-tenshi
app.config_schema(armor)
app.config_schema(tenshi)

app.include('baka_tenshi')
app.include('baka_armor')

# modular aplikasi
app.include('.users')

@app.route('/', renderer='CircleApp:templates/index.html')
def HomePage(request):
    log.info('ok')
    return { 'Baka': 'Hello World'}


app.scan()
