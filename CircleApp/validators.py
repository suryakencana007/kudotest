import colander
import re


class BaseEmail(object):
    """
    Email validator shamelessly stolen from Django
    """
    USER_REGEX = (
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)'  # quoted-string
    )
    # max length for domain name labels is 63 characters per RFC 1034
    DOMAIN_REGEX = r'((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))\Z'

    def __init__(self, msg=None):
        if msg is None:
            msg = "Invalid email address"
        self.msg = msg
        self.user_regex = re.compile(self.USER_REGEX, re.IGNORECASE)
        self.domain_regex = re.compile(self.DOMAIN_REGEX, re.IGNORECASE)

    def __call__(self, node, value):
        if not value or '@' not in value:
            raise colander.Invalid(node, self.msg)

        user_part, domain_part = value.rsplit('@', 1)

        if not self.user_regex.match(user_part):
            raise colander.Invalid(node, self.msg)

        if not self.domain_regex.match(domain_part):
            # Try for possible IDN domain-part
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
                if self.domain_regex.match(domain_part):
                    return
            except UnicodeError:
                pass
            raise colander.Invalid(node, self.msg)


class Email(BaseEmail):
    def __init__(self, *args, **kwargs):
        if 'msg' not in kwargs:
            kwargs['msg'] = "Invalid email address."
        super(Email, self).__init__(*args, **kwargs)


class BaseUrl(object):
    """
    URL validator shamelessly stolen from http://validators.readthedocs.io/en/latest/_modules/validators/url.html#url
    """
    ip_middle_octet = u"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5]))"
    ip_last_octet = u"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"

    regex = re.compile(
        u"^"
        # protocol identifier
        u"(?:(?:https?|ftp)://)"
        # user:pass authentication
        u"(?:\S+(?::\S*)?@)?"
        u"(?:"
        u"(?P<private_ip>"
        # IP address exclusion
        # private & local networks
        u"(?:(?:10|127)" + ip_middle_octet + u"{2}" + ip_last_octet + u")|"
        u"(?:(?:169\.254|192\.168)" + ip_middle_octet + ip_last_octet + u")|"
        u"(?:172\.(?:1[6-9]|2\d|3[0-1])" + ip_middle_octet + ip_last_octet + u"))"
        u"|"
        # IP address dotted notation octets
        # excludes loopback network 0.0.0.0
        # excludes reserved space >= 224.0.0.0
        # excludes network & broadcast addresses
        # (first & last IP address of each class)
        u"(?P<public_ip>"
        u"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
        u"" + ip_middle_octet + u"{2}"
        u"" + ip_last_octet + u")"
        u"|"
        # host name
        u"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
        # domain name
        u"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
        # TLD identifier
        u"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
        u")"
        # port number
        u"(?::\d{2,5})?"
        # resource path
        u"(?:/\S*)?"
        # query string
        u"(?:\?\S*)?"
        u"$",
        re.UNICODE | re.IGNORECASE
    )


    def __init__(self, msg=None):
        if msg is None:
            msg = "Invalid URL address"
        self.msg = msg
        self.pattern = re.compile(self.regex)


    def __call__(self, node, value):
        if not self.pattern.match(value):
            raise colander.Invalid(node, self.msg)

        return


class Url(BaseUrl):
    def __init__(self, *args, **kwargs):
        if 'msg' not in kwargs:
            kwargs['msg'] = "Invalid url address. eg.http://pinjam.co.id or https://www.pinjam.co.id"
        super(Url, self).__init__(*args, **kwargs)


class Length(colander.Length):
    def __init__(self, *args, **kwargs):
        if 'min_err' not in kwargs:
            kwargs['min_err'] = "Must be ${min} characters or more."
        if 'max_err' not in kwargs:
            kwargs['max_err'] = "Must be ${max} characters or less."
        super(Length, self).__init__(*args, **kwargs)