# -*- coding: utf-8 -*-
"""

    ~~~~~~~~~

    :author: nanang.jobs@gmail.com
    :copyright: (c) 2017 by Nanang Suryadi.
    :license: BSD, see LICENSE for more details.

    jsonapi.py
"""
import functools
import re

from pyramid.httpexceptions import HTTPBadRequest
import sqlalchemy
from sqlalchemy.orm import RelationshipProperty, load_only


class QueryBuilder(object):
    def __init__(self, request, model,
                 collection_name=None):
        self.request = request
        self.model = model
        self.attributes = {}
        self.fields = {}
        self.key_column = sqlalchemy.inspect(model).primary_key[0]
        self.collection_name = model.__tablename__ if collection_name is None else collection_name
        self.session = request.db

    def allowed_object(self, obj):
        '''Whether or not current action is allowed on object.

        Returns:
            bool:
        '''
        return True

    @property
    def allowed_fields(self):
        '''Set of fields to which current action is allowed.

        Returns:
            set: set of allowed field names.
        '''
        return set(self.fields)

    @property
    @functools.lru_cache(maxsize=128)
    def requested_field_names(self):
        '''Get the sparse field names from request.

        **Query Parameters**

            **fields[<collection>]:** comma separated list of fields
            (attributes or relationships) to include in data.

        Returns:
            set: set of field names.
        '''
        param = self.request.params.get(
            'fields[{}]'.format(self.collection_name)
        )
        if param is None:
            return self.attributes.keys() | self.relationships.keys()
        if param == '':
            return set()
        return set(param.split(','))

    @property
    def requested_attributes(self):
        '''Return a dictionary of attributes.

        **Query Parameters**

            **fields[<collection>]:** comma separated list of fields
            (attributes or relationships) to include in data.

        Returns:
            dict: dict in the form:

                .. parsed-literal::

                    {
                        <colname>: <column_object>,
                        ...
                    }
        '''
        return {
            k: v for k, v in self.attributes.items()
            if k in self.requested_field_names
        }

    @property
    def allowed_requested_query_columns(self):
        '''All columns required in query to fetch allowed requested fields from
        db.

        Returns:
            dict: Union of allowed requested_attributes and
            allowed_requested_relationships_local_columns
        '''
        ret = {
            k: v for k, v in self.requested_attributes.items()
            if k in self.allowed_fields
        }
        return ret

    def get_fields(self, expose_fields):
        atts = {}
        fields = {}
        for key, col in sqlalchemy.inspect(self.model).mapper.columns.items():
            if key == self.key_column.name:
                continue
            if len(col.foreign_keys) > 0:
                continue
            if expose_fields is None or key in expose_fields:
                atts[key] = col
                fields[key] = col
            self.attributes = atts
            rels = {}
            fields.update(rels)
            self.fields = fields

    def query_add_sorting(self, q):
        '''Add sorting to query.

        Use information from the ``sort`` query parameter (via
        :py:func:`collection_query_info`) to contruct an ``order_by`` clause on
        the query.

        See Also:
            ``_sort`` key from :py:func:`collection_query_info`

        **Query Parameters**
            **sort:** comma separated list of sort keys.

        Parameters:
            q (sqlalchemy.orm.query.Query): query

        Returns:
            sqlalchemy.orm.query.Query: query with ``order_by`` clause.
        '''
        # Get info for query.
        qinfo = self.collection_query_info(self.request, self.key_column)

        # Sorting.
        for key_info in qinfo['_sort']:
            sort_keys = key_info['key'].split('.')
            # We are using 'id' to stand in for the key column, whatever that
            # is.
            main_key = sort_keys[0]
            if main_key == 'id':
                main_key = self.key_column.name
            order_att = getattr(self.model, main_key)
            if key_info['ascending']:
                q = q.order_by(order_att)
            else:
                q = q.order_by(order_att.desc())

        return q

    def query_add_filtering(self, q):
        '''Add filtering clauses to query.

        Use information from the ``filter`` query parameter (via
        :py:func:`collection_query_info`) to filter query results.

        Filter parameter structure:

            ``filter[<attribute>:<op>]=<value>``

        where:

            ``attribute`` is an attribute of the queried object type.

            ``op`` is the comparison operator.

            ``value`` is the value the comparison operator should compare to.

        Valid comparison operators:

            * ``eq`` as sqlalchemy ``__eq__``
            * ``ne`` as sqlalchemy ``__ne__``
            * ``startswith`` as sqlalchemy ``startswith``
            * ``endswith`` as sqlalchemy ``endswith``
            * ``contains`` as sqlalchemy ``contains``
            * ``lt`` as sqlalchemy ``__lt__``
            * ``gt`` as sqlalchemy ``__gt__``
            * ``le`` as sqlalchemy ``__le__``
            * ``ge`` as sqlalchemy ``__ge__``
            * ``like`` or ``ilike`` as sqlalchemy ``like`` or ``ilike``, except
              replace any '*' with '%' (so that '*' acts as a wildcard)

        See Also:
            ``_filters`` key from :py:func:`collection_query_info`

        **Query Parameters**
            **filter[<attribute>:<op>]:** filter operation.

        Parameters:
            q (sqlalchemy.orm.query.Query): query

        Returns:
            sqlalchemy.orm.query.Query: filtered query.

        Examples:

            Get people whose name is 'alice'

            .. parsed-literal::

                http GET http://localhost:6543/people?filter[name:eq]=alice

            Get posts published after 2015-01-03:

            .. parsed-literal::

                http GET http://localhost:6543/posts?filter[published_at:gt]=2015-01-03

        Todo:
            Support dotted (relationship) attribute specifications.
        '''
        qinfo = self.collection_query_info(self.request, self.key_column)
        # Filters
        for p, finfo in qinfo['_filters'].items():
            val = finfo['value']
            colspec = finfo['colspec']
            op = finfo['op']
            prop = getattr(self.model, colspec[0])
            if isinstance(prop.property, RelationshipProperty):
                # TODO(Colin): deal with relationships properly.
                pass
            if op == 'eq':
                op_func = getattr(prop, '__eq__')
            elif op == 'ne':
                op_func = getattr(prop, '__ne__')
            elif op == 'startswith':
                op_func = getattr(prop, 'startswith')
            elif op == 'endswith':
                op_func = getattr(prop, 'endswith')
            elif op == 'contains':
                op_func = getattr(prop, 'contains')
            elif op == 'lt':
                op_func = getattr(prop, '__lt__')
            elif op == 'gt':
                op_func = getattr(prop, '__gt__')
            elif op == 'le':
                op_func = getattr(prop, '__le__')
            elif op == 'ge':
                op_func = getattr(prop, '__ge__')
            elif op == 'like' or op == 'ilike':
                op_func = getattr(prop, op)
                val = re.sub(r'\*', '%', val)
            else:
                raise HTTPBadRequest(
                    "No such filter operator: '{}'".format(op)
                )
            _filters = op_func(val)
            if isinstance(val, list):
                _ops = []
                for _v in val:
                    _ops.append(op_func(_v))
                _filters = sqlalchemy.or_(*_ops)
            q = q.filter(_filters)

        return q

    @classmethod
    @functools.lru_cache(maxsize=128)
    def collection_query_info(cls, request, key_column):
        '''Return dictionary of information used during DB query.

        Args:
            request (pyramid.request): request object.

        Returns:
            dict: query info in the form::

                {
                    'page[limit]': maximum items per page,
                    'page[offset]': offset for current page (in items),
                    'sort': sort param from request,
                    '_sort': [
                        {
                            'key': sort key ('field' or 'relationship.field'),
                            'ascending': sort ascending or descending (bool)
                        },
                        ...
                    },
                    '_filters': {
                        filter_param_name: {
                            'colspec': list of columns split on '.',
                            'op': filter operator,
                            'value': value of filter param,
                        }
                    },
                    '_page': {
                        paging_param_name: value,
                        ...
                    }
                }

            Keys beginning with '_' are derived.
        '''

        info = {'page[limit]': min(
            cls.max_limit,
            int(request.params.get('page[limit]', cls.default_limit))
        ), 'page[offset]': int(request.params.get('page[offset]', 0))}

        # Paging by limit and offset.
        # Use params 'page[limit]' and 'page[offset]' to comply with spec.

        # Sorting.
        # Use param 'sort' as per spec.
        # Split on '.' to allow sorting on columns of relationship tables:
        #   sort=name -> sort on the 'name' column.
        #   sort=owner.name -> sort on the 'name' column of the target table
        #     of the relationship 'owner'.
        # The default sort column is 'id'.
        sort_param = request.params.get('sort', key_column.name)
        info['sort'] = sort_param

        # Break sort param down into components and store in _sort.
        info['_sort'] = []
        for sort_key in sort_param.split(','):
            key_info = {}
            # Check to see if it starts with '-', which indicates a reverse
            # sort.
            ascending = True
            if sort_key.startswith('-'):
                ascending = False
                sort_key = sort_key[1:]
            key_info['key'] = sort_key
            key_info['ascending'] = ascending
            info['_sort'].append(key_info)

        # Find all parametrised parameters ( :) )
        info['_filters'] = {}
        info['_page'] = {}
        # print(request.params)
        # print({k: [ val for val in request.params.getall(k)] for k, v in request.params.items()})
        _params = {k: [val for val in request.params.getall(k)] for k, v in request.params.items()}

        # for p in request.params.keys():
        for p in _params.keys():
            match = re.match(r'(.*?)\[(.*?)\]', p)
            if not match:
                continue
            val = request.params.get(p) if len(request.params.getall(p)) < 2 else request.params.getall(p)
            # Filtering.
            # Use 'filter[<condition>]' param.
            # Format:
            #   filter[<column_spec>:<operator>] = <value>
            #   where:
            #     <column_spec> is either:
            #       <column_name> for an attribute, or
            #       <relationship_name>.<column_name> for a relationship.
            # Examples:
            #   filter[name:eq]=Fred
            #      would find all objects with a 'name' attribute of 'Fred'
            #   filter[author.name:eq]=Fred
            #      would find all objects where the relationship author pointed
            #      to an object with 'name' 'Fred'
            #
            # Find all the filters.
            if match.group(1) == 'filter':
                colspec, op = match.group(2).split(':')
                colspec = colspec.split('.')

                info['_filters'][p] = {
                    'colspec': colspec,
                    'op': op,
                    'value': val
                }
            # Paging.
            elif match.group(1) == 'page':
                info['_page'][match.group(2)] = val
        return info

    def get_collection_query(self):
        '''Handle GET requests for the collection.

        Get a set of items from the collection, possibly matching search/filter
        parameters. Optionally sort the results, page them, return only certain
        fields, and include related resources.

        **Query Parameters**

            **include:** comma separated list of related resources to include
            in the include section.

            **fields[<collection>]:** comma separated list of fields
            (attributes or relationships) to include in data.

            **sort:** comma separated list of sort keys.

            **page[limit]:** number of results to return per page.

            **page[offset]:** starting index for current page.

            **filter[<attribute>:<op>]:** filter operation.

        Returns:
            dict: dict in the form:

            .. parsed-literal::

                {
                    "data": [ list of resource objects ],
                    "links": { links object },
                    "include": [ optional list of included resource objects ],
                    "meta": { implementation specific information }
                }

        Raises:
            HTTPBadRequest

        Examples:
            Get up to default page limit people resources:

            .. parsed-literal::

                http GET http://localhost:6543/people

            Get the second page of two people, reverse sorted by name and
            include the related posts as included documents:

            .. parsed-literal::

                http GET http://localhost:6543/people?page[limit]=2&page[offset]=2&sort=-name&include=posts
        '''
        db_session = self.session

        # Set up the query
        q = db_session.query(
            self.model
        ).options(
            load_only(*self.allowed_requested_query_columns.keys())
        )
        q = self.query_add_sorting(q)
        q = self.query_add_filtering(q)
        try:
            count = q.count()
        except sqlalchemy.exc.ProgrammingError as e:
            raise HTTPBadRequest(
                'An error occurred querying the database. Server logs may have details.'
            )
        qinfo = self.collection_query_info(self.request, self.key_column)
        limit = int(qinfo['page[limit]'])
        offset = int(qinfo['page[offset]']) * int(limit) if qinfo.get('page[offset]', None) else 0
        q = q.offset(offset)
        q = q.limit(limit)
        return q, {
            'total': count,
            'page': qinfo['page[offset]'],
            'pageSize': qinfo['page[limit]']
        }
