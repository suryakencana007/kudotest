import colander
import re
from sqlalchemy.util import asbool

from CircleApp import forms, validators


USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = '(?i)^[A-Z0-9._]+$'
EMAIL_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 4

@colander.deferred
def email_validator(node, kw):
    request = kw.get('request')
    is_edit = request.params.get('is_edit', False)

    def validator(_node, value):
        User = request.find_model('pengguna')
        user = User.get_by_email(request.db, value)
        if not asbool(is_edit) and user and str(user.email) == request.params.get('email'):
            raise colander.Invalid(
                _node,
                u'Email is invalid or already taken',
            )
    return colander.All(validators.Email(), validator,)


@colander.deferred
def user_validator(node, kw):
    request = kw.get('request')
    is_edit = request.params.get('is_edit', False)

    def validator(_node, value):
        User = request.find_model('pengguna')
        user = User.get_by_username(request.db, value)
        username = request.params.get('username', '')
        if not re.match(USERNAME_PATTERN, username):
            raise colander.Invalid(
                _node,
                u'username must have only letters, numbers, periods, and underscores.',
            )

        if not asbool(is_edit) and user and str(user.username).lower() == username.lower():
            raise colander.Invalid(
                _node,
                u'Username is already taken',
            )
    return colander.All(validators.Length(min=USERNAME_MIN_LENGTH, max=USERNAME_MAX_LENGTH), validator,)


@colander.deferred
def password_validator(node, kw):
    request = kw.get('request')

    def validator(_node, value):
        if value and request.params.get('password_confirm') != value:
            raise colander.Invalid(
                _node,
                u'Password and confirm is not equal',
            )
    return colander.All(validators.Length(min=PASSWORD_MIN_LENGTH), validator,)


class _UserEditSchema(forms.BaseSchema):

    username = colander.SchemaNode(
        colander.String(),
        validator=user_validator
    )
    password = colander.SchemaNode(
        colander.String(),
        validator=password_validator,
        missing=None
    )
    email = colander.SchemaNode(
        colander.String(),
        validator=email_validator
    )


class _UserAddSchema(_UserEditSchema):
    password = colander.SchemaNode(
        colander.String(),
        validator=password_validator
    )
    password_confirm = colander.SchemaNode(
        colander.String()
    )



class _UserForm(forms.BaseForm):

    def submit(self, model=None):
        if not model:
            model = self.request.find_model('pengguna')()

        model.username = self._controls.get('username')
        # jika update harus cek
        if self._controls.get('password'):
            model.password = self._controls.get('password')
        model.email = self._controls.get('email')
        return model


class UserAddForm(_UserForm):
    _schema = _UserAddSchema


class UserEditForm(_UserForm):
    _schema = _UserEditSchema