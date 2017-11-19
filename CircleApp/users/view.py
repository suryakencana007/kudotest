from baka.log import log
from baka.response import JSONAPIResponse

from CircleApp.app import app
from CircleApp.jsonapi import QueryBuilder
from CircleApp.users.form import UserAddForm
from CircleApp.utils import MAX_LIMIT, DEFAULT_LIMIT, mapper_alchemy


@app.resource(
    '/users/{uid:.*}',
    route_name='pengguna_form',
    renderer='CircleApp:users/templates/register.html')
class PenggunaForm(object):
    def __init__(self, request):
        self._title = 'Pengguna'
        self.user = request.find_model('pengguna')


@PenggunaForm.GET()
def pengguna_form_get(page, request):
    data = {}
    s = request.db
    user = s.query(page.user).filter_by(
        uid=request.matchdict.get('uid')).first()

    if user:
        data = mapper_alchemy(page.user, user)

    return {
        'title': page._title,
        'action': request.route_url('pengguna_form', uid=user.uid),
        **data
    }


@PenggunaForm.POST()
def pengguna_form_post(page, request):
    return {
        'title': page._title,
        'action': request.route_url('pengguna_form', uid='')
    }


@app.resource(
    '/users',
    route_name='pengguna_form_new',
    renderer='CircleApp:users/templates/register.html')
class PenggunaFormNew(object):
    def __init__(self, request):
        self._title = 'Pengguna'
        self.user = request.find_model('pengguna')


@PenggunaFormNew.GET()
def pengguna_form_new_get(page, request):
    return {
        'title': page._title
    }


@PenggunaFormNew.POST()
def pengguna_form_new_post(page, request):
    errors = None
    form = UserAddForm(request)
    if form.validate():
        user = form.submit()
        request.db.add(user)
    else:
        errors = form.errors

    return {
        'title': page._title,
        'action': request.route_url('pengguna_form', uid='00008888'),
        'errors': errors
    }


@app.route('/users/list', route_name='pengguna_list')
def pengguna_get(request):
    user = request.find_model('pengguna')
    data = {}
    with JSONAPIResponse(request.response) as resp:
        _in = u'Failed'
        code, status = JSONAPIResponse.BAD_REQUEST
        if user:
            QueryBuilder.max_limit = MAX_LIMIT
            QueryBuilder.default_limit = DEFAULT_LIMIT
            query_builder = QueryBuilder(request, user)
            query, pagination = query_builder.get_collection_query()
            rows = query.all()
            data = [mapper_alchemy(
                user, row)
                for row in rows]

            _in = u'Success'
            code, status = JSONAPIResponse.OK

    return resp.to_json(
        _in, code=code,
        status=status,
        data=data,
        total=pagination.get('total', 0))


@app.resource(
    '/login',
    route_name='pengguna_login',
    renderer='CircleApp:users/templates/login.html')
class PenggunaLogin(object):
    def __init__(self, request):
        self._title = 'Login'
        self.user = request.find_model('pengguna')


@PenggunaLogin.GET()
def login_get(page, request):
    return { 'title': page._title }


@PenggunaLogin.POST()
def login_post(page, request):
    params = request.params
    log.info(params)
    return { 'title': page._title }


# /profile/{uid:.*}
@app.resource(
    '/profile/{uid:.*}',
    route_name='profile_page',
    renderer='CircleApp:users/templates/profile.html')
class ProfilePage(object):
    def __init__(self, request):
        self._title = 'Profile'
        self.profile = request.find_model('profile')
        self.user = request.find_model('pengguna')


@ProfilePage.GET()
def profile_get(page, request):
    data = {}
    s = request.db
    user = s.query(page.user).filter_by(
        uid=request.matchdict.get('uid')).first()

    profile = user.profile
    if profile:
        data = mapper_alchemy(page.profile, profile)

    return {
        'title': page._title,
        'action': request.route_url('profile_page', uid=user.uid),
        **data
    }


@ProfilePage.POST()
def profile_post(page, request):
    s = request.db

    profile = page.profile
    profile.display_name = ' Surya Kencana Bond'
    profile.first_name = 'Surya'
    profile.last_name = 'Kencana'
    profile.description = 'Hahahahaha'
    profile.user_id = request.matchdict.get('uid')

    s.add(profile)
    return { 'title': page._title }


def includeme(config):
    config.scan()
