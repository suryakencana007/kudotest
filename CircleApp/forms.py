# -*- coding: utf-8 -*-
"""
    Core Form
    ~~~~~~~~~

    :author: nanang.jobs@gmail.com
    :copyright: (c) 2017 by Nanang Suryadi.
    :license: BSD, see LICENSE for more details.

    forms.py
"""
import colander


class SelectEnumInt(colander.String):
    def __init__(self, enum, msg=None):
        self.request = None
        self.enums = enum
        self.msg = msg or u'Object does not exists'

    def enum(self, val):
        try:
            values = list(map(lambda x: x[0], self.enums))
            if val not in values:
                return None
            return val
        except:
            return None

    def serialize(self, node, appstruct):
        if appstruct is colander.null:
            return colander.null

        val = self.enum(appstruct)
        if not val:
            raise colander.Invalid(node, self.msg)
        return str(val)

    def deserialize(self, node, cstruct):
        if cstruct != 0 and not cstruct:
            return colander.null

        val = self.enum(cstruct)
        if not val:
            raise colander.Invalid(node, self.msg)
        return val


@colander.deferred
def csrf_token_validator(node, kw):
    request = kw.get('request')

    def validator(_node, value):
        if value != request.session.get_csrf_token():
            raise colander.Invalid(
                _node,
                u'Invalid CSRF token',
            )

    return colander.All(colander.Length(max=255), validator, )


class CSRFSchema(colander.Schema):
    csrf_token = colander.SchemaNode(
        colander.String(),
        validator=csrf_token_validator
    )


class APISchema(colander.Schema):
    csrf_token = colander.SchemaNode(
        colander.String(),
        validator=csrf_token_validator
    )


class BaseSchema(colander.Schema):
    pass


class BaseForm(object):
    _schema = None
    _controls = None
    _errors = None

    def __init__(self, request):
        assert self._schema, u'Set _schema class attribute'
        self.request = request
        self.schema = self._schema().bind(request=self.request)

    def validate(self):
        try:
            self._controls = self.schema.deserialize(
                self.request.params.mixed()
            )
            return True
        except colander.Invalid as e:
            self._errors = e.asdict()
            return False

    @property
    def errors(self):
        return self._errors

    def submit(self, obj=None):
        raise NotImplementedError(u'Submit method must be implemented')
