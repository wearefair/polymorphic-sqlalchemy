from .misc import namedtuple_with_defaults
from sqlalchemy import event, and_
from sqlalchemy.orm import relationship, foreign, remote, backref
from sqlalchemy.ext.associationproxy import association_proxy
import inflection
import logging
logger = logging.getLogger(__name__)

DELIMITER = '__'

Relation = namedtuple_with_defaults(
    'Relation', 'data_class ref_class data_class_attr ref_class_attr data_class_proxy_attr ' +\
                'ref_class_name data_class_alchemy_attr ref_class_attr_name')


def create_polymorphic_base(data_class=None, data_class_attr=None,
                                ref_class_attr=None, data_class_proxy_attr=None, relations=None):
    """
    Shortcut for generate_polymorphic_listener
    """
    if data_class:
        relation = Relation(data_class=data_class, data_class_attr=data_class_attr,
                            ref_class_attr=ref_class_attr, data_class_proxy_attr=data_class_proxy_attr)
        relations = (relation,)
    elif relations:
        pass
    else:
        raise ValueError('data_class and data_class_attr or relations must be set')

    data_class_name = 'Has{}'.format(relations[0].data_class.__name__)
    has_data_class = type(data_class_name, (), {})
    setup_listener = generate_polymorphic_listener(relations=relations)
    event.listen(has_data_class, 'mapper_configured', setup_listener, propagate=True)

    return has_data_class


def generate_polymorphic_listener_function(belongs_to_class, belongs_to_association,
    has_many_name = None, association_proxy_name = None):
    """
    Old way of using polymorphic relations
    """

    relation = Relation(data_class=belongs_to_class, data_class_attr=belongs_to_association,
                        ref_class_attr=has_many_name, data_class_proxy_attr=association_proxy_name)
    relations = (relation,)
    return generate_polymorphic_listener(relations=relations, new_format=False)

def generate_polymorphic_listener(relations=None, new_format=True):

    def setup_polymorphic_listener(mapper, ref_class):

        """
        Setup the polymorphic listener on append events of the data_class objects on the ref_class objects.
        Set DEBUG=True in order to get a verbose log of what happens.
        """

        for relation in relations:
            rel_dict = relation._asdict()
            rel_dict['data_class_alchemy_attr'], rel_dict['ref_class_name'] = get_data_class_alchemy_attr(
                ref_class=ref_class, data_class_attr=relation.data_class_attr, new_format=new_format)
            rel_dict['ref_class'] = ref_class
            rel_dict['ref_class_attr_name'] = get_ref_class_attr_name(relation)
            rel = Relation(**rel_dict)

            _create_orm_relation(rel)
            if rel.data_class_proxy_attr is not None:
                _add_proxy(rel)

            @event.listens_for(getattr(ref_class, rel.ref_class_attr_name), 'append')
            def append_object(ref_obj, data_obj, initiator):
                if new_format:
                    prefix, _type = initiator.key.split(DELIMITER)
                    setattr(data_obj, "{}_type".format(prefix), _type)
                    setattr(data_obj, "{}_id".format(prefix), ref_obj.id)
                else:
                    setattr(data_obj, "{}_type".format(rel.data_class_attr), rel.ref_class_name)

    return setup_polymorphic_listener


def get_ref_class_attr_name(rel):
    if rel.ref_class_attr is None:
        ref_class_attr_name = "{}s".format(get_underscored_class_name(rel.data_class))
    else:
        ref_class_attr_name = rel.ref_class_attr
    return ref_class_attr_name


def get_prefixed_name(x, y):
    return '{}{}{}'.format(x, DELIMITER, y)


def get_underscored_class_name(class_):
    return inflection.underscore(class_.__name__)


def get_data_class_alchemy_attr(ref_class, data_class_attr, new_format):
    """
        >>> print('data_class_alchemy_attr = ref_class + underscore(ref_class.__name__)')
        >>> print('data_class_alchemy_attr = {}'.format(data_class_alchemy_attr))
    """
    ref_class_name = get_underscored_class_name(ref_class)
    data_class_alchemy_attr = get_prefixed_name(data_class_attr, ref_class_name) if new_format else ref_class_name
    return data_class_alchemy_attr, ref_class_name


def _add_proxy(rel):
    """
    association_proxy is made between ref_class_attr_name and data_class_proxy_attr
        >>> print(between {} and {}'.format(rel.ref_class_attr_name, rel.data_class_proxy_attr))

    and then an "s" is added and it is set on ref_class')
        >>> print({}.{}s = association_proxy_rel'.format(rel.ref_class, rel.data_class_proxy_attr, ))

    """
    association_proxy_rel = association_proxy(rel.ref_class_attr_name, rel.data_class_proxy_attr)
    setattr(rel.ref_class, "{}s".format(rel.data_class_proxy_attr), association_proxy_rel)


def _create_orm_relation(rel):
    """
    ref_class_attr_name is based on the name of data_class if not provided. It adds an "s"
    ref_class.ref_class_attr_name = rel

    >>> print('{}.{} = rel'.format(rel.ref_class.__name__, rel.ref_class_attr_name))
    """
    orm_relation = relationship(rel.data_class,
                        primaryjoin=and_(
                                        rel.ref_class.id == foreign(remote(getattr(rel.data_class, "{}_id".format(rel.data_class_attr)))),
                                        getattr(rel.data_class, "{}_type".format(rel.data_class_attr)) == rel.ref_class_name
                                    ),
                        backref=backref(
                                rel.data_class_alchemy_attr,
                                primaryjoin=remote(rel.ref_class.id) == foreign(getattr(rel.data_class, "{}_id".format(rel.data_class_attr)))
                                )
                        )

    setattr(rel.ref_class, rel.ref_class_attr_name, orm_relation)


class NetRelationship:
    '''Descriptor for network backed object that is used in a polymorphic relationship.'''

    def __init__(self, prefix, _class):
        """
        Example:

        prefix = 'buyer'
        _class = Dealer

        buyer__dealer = NetRelationship(prefix='buyer', _class=Dealer)
        """
        self.prefix = prefix
        self.prefix_type = '{}_type'.format(prefix)  # buyer_type
        self.prefix_id = '{}_id'.format(prefix)  # buyer_id
        self._class = _class
        self._class_name = get_underscored_class_name(_class)
        self.prefixed = '_{}'.format(get_prefixed_name(prefix, self._class_name))  # Example: _buyer_dealer

    def _get_and_set_obj(self, instance, prefix_id_content):
        obj = self._class.find(prefix_id_content)
        setattr(instance, self.prefixed, obj)
        return obj

    def _get_obj_from_id(self, instance, prefix_id_content):
        if prefix_id_content is None:
            msg = '{} expected to be not null'.format(prefix_id_content)
            raise ValueError(msg)

        if hasattr(instance, self.prefixed):
            obj = getattr(instance, self.prefixed)
            if obj.id != prefix_id_content:
                obj = self._get_and_set_obj(instance, prefix_id_content)
        else:
             obj = self._get_and_set_obj(instance, prefix_id_content)

        return obj

    def __get__(self, instance, owner):
        prefix_type_content, prefix_id_content = self._get_type_field_contents(instance)
        if prefix_type_content != self._class_name:
            msg = '{} expected to be {}, not {}.'.format(prefix_type_content, self._class_name, prefix_type_content)
            raise ValueError(msg)

        return self._get_obj_from_id(instance, prefix_id_content)

    def _get_type_field_contents(self, instance):
        prefix_type_content = getattr(instance, self.prefix_type)  # buyer_type content which should be dealer
        prefix_id_content = getattr(instance, self.prefix_id)  # buyer_id content
        return prefix_type_content, prefix_id_content

    def __set__(self, instance, value):
        value_class_name = get_underscored_class_name(value.__class__)
        if value_class_name == self._class_name:
            # The class could be NetModel too
            if self.__class__ is NetRelationship:
                setattr(instance, self.prefix_type, self._class_name)
            setattr(instance, self.prefix_id, value.id)
            setattr(instance, self.prefixed, value)
        else:
            logger.error('{} and {} do not match for setting {}'.format(value_class_name, self._class_name, self.prefixed))



class NetModel(NetRelationship):
    '''Descriptor for network backed object that is defined by an id.'''

    def __init__(self, field, _class):
        """
        Example:

        field = 'buyer_id'
        _class = Organization
        """
        self.prefix_id = field
        self._class = _class
        self._class_name = get_underscored_class_name(_class)
        self.prefixed = '_{}'.format(field)

    def __get__(self, instance, owner):
        prefix_id_content = getattr(instance, self.prefix_id)
        return self._get_obj_from_id(instance, prefix_id_content)


class PolyField:

    def __init__(self, prefix):
        """
        Example:

        prefix = 'buyer'

        buyer = PolyField('buyer')
        """
        self.prefix = prefix
        self.prefix_type = '{}_type'.format(prefix)  # buyer_type

    def __get__(self, instance, owner):
        prefix_type_content = getattr(instance, self.prefix_type)
        if prefix_type_content is not None:
            attr = get_prefixed_name(self.prefix, prefix_type_content)
            return getattr(instance, attr)

    def __set__(self, instance, value):
        _class_name = get_underscored_class_name(value.__class__)
        attr = get_prefixed_name(self.prefix, _class_name)
        setattr(instance, attr, value)


class BaseInitializer:
    """
    Poly base is NOT essential to use for polymorphic models but it can make the initialization easier.
    It needs to be one of the superclasses of your model BEFORE db.Model
    """

    def __init__(self, *args, **kwargs):

        alchemy_fields = {}
        other_fields = {}
        all_alchemy_columns = self.__class__.__table__.columns

        for name, value in kwargs.items():
            if name in all_alchemy_columns:
                alchemy_fields[name] = value
            else:
                other_fields[name] = value

        super().__init__(*args, **alchemy_fields)

        for name, field in other_fields.items():
            setattr(self, name, field)

    def __repr__(self):
        id_ = getattr(self, 'id', False)
        id_ = ' id: {}'.format(id_) * bool(id_)
        name = getattr(self, 'name', False)
        name = ' name: {}'.format(name) * bool(name)
        return '<{}{}{}>'.format(self.__class__.__name__, id_, name)

