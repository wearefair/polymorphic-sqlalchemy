# Polymorphic extension for SQLAlchemy v0.2.6

# Install

`pip install polymorphic-sqlalchemy`

# Why?

Imagine if you have a table with some data.

```
┏━━━━━━━━━━━━━┓
┃Vehicle Table┃
┣━━━━━━━━━━━━━┫
┃ 1 BMW 3     ┃
┣━━━━━━━━━━━━━┫
┃ 2 Tesla S   ┃
┗━━━━━━━━━━━━━┛
```


And now you want to know what the source of each row was. You could start by simply making foreign keys to individual tables that could be the source of your data in the vehicle table. Let's say at this point the source of vehicle could be some organization or some dealer:


```
┏━━━━━━━━━━━━━┓
┃Vehicle Table┃    ┏━━━━━━━━━━━━━┓
┣━━━━━━━━━━━━━┫    ┃  Org Table  ┃
┃ 1 BMW 3     ┃----┗━━━━━━━━━━━━━┛
┣━━━━━━━━━━━━━┫    ┏━━━━━━━━━━━━━┓
┃ 2 Tesla S   ┃----┃Dealer Table ┃
┗━━━━━━━━━━━━━┛    ┗━━━━━━━━━━━━━┛
```


But once you have many different sources of data, this approach quickly becomes unmanageable.

Now imagine if you are using a microservice architecture. Sometimes people have microservices that share the database:

```


             ░            SHARED DATABASE           ░
             ░  ┏━━━━━━━━━━━━━┓                     ░
             ░  ┃Vehicle Table┃    ┏━━━━━━━━━━━━━┓  ░
             ░  ┣━━━━━━━━━━━━━┫    ┃  Org Table  ┃  ░
 Service 1   ░  ┃ 1 BMW 3     ┃----┗━━━━━━━━━━━━━┛  ░   Service 2
             ░  ┣━━━━━━━━━━━━━┫    ┏━━━━━━━━━━━━━┓  ░
             ░  ┃ 2 Tesla S   ┃----┃Dealer Table ┃  ░
             ░  ┗━━━━━━━━━━━━━┛    ┗━━━━━━━━━━━━━┛  ░
             ░                                      ░
```

But that is not recommended. You want your microservices to be loosely coupled. It is a bad idea to have shared resource. So we separate the vehicle model and org model to live on the same database for service 1 but some other microservice has the dealer table.


```
                   Service 1        ░                   ░    Service 2
┏━━━━━━━━━━━━━┓                     ░                   ░
┃Vehicle Table┃    ┏━━━━━━━━━━━━━┓  ░                   ░
┣━━━━━━━━━━━━━┫    ┃  Org Table  ┃  ░                   ░
┃ 1 BMW 3     ┃----┗━━━━━━━━━━━━━┛  ░                   ░
┣━━━━━━━━━━━━━┫                     ░                   ░  ┏━━━━━━━━━━━━━┓
┃ 2 Tesla S   ┃-------------------Client ┈ network ┈ ┈ API-┃Dealer Table ┃
┗━━━━━━━━━━━━━┛                     ░                   ░  ┗━━━━━━━━━━━━━┛
                                    ░                   ░
```


The Polymorphic extension is written to manage relationship such as above. So you can deal with the above situation as if the models were all in the same database in the same service.

# How to use Polymorphic Extension

[Take a look at the tutorial](tutorial.md)

# Reference

This package introduces the following fields and helpers:

- `PolyField` : Used to get and set polymorphic objects. It reads and writes to the `[prefix]_id` and `[prefix]_type` fields in the same object.

    Example:

    ```py
    source_id = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source = PolyField(prefix='source')
    ```

- `NetRelationship` : Used for network backed relationships. Acts similar to SQLAlchemy relationships. Use `NetRelationship` when you have network backed models that SQLAlchemy can not automatically make relationship to them. ONLY used for polymorphic network backed objects. It needs to be used along the `PolyField` and `[prefix]_id` and `[prefix]_type` fields. The convension is to use double underscore between the prefix and class name as the name for this field. For example if the prefix is `source` (simply because we have source_id and source_type fields, then the PolyField should be called `source` too and the NetRelationship field that is pointing to the Dealer Model should be called `[prefix]__[model lower case name]` which is `source__dealer` in this case:


    ```py
    source_id = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source = PolyField(prefix='source')
    source__dealer = NetRelationship(prefix='source', _class=Dealer)
    ```

- `NetModel` : Used for network backed models. Only for **NON-polymorphic** relationships.

    Another field type that this library provides is the NetModel

    Example:

    ```py
    from polymorphic_sqlalchemy import NetModel

    class NetworkModel:

        def __init__(self, dealer_id):
            self.dealer_id = dealer_id

        # Look at the Dealer definition in multiple relations example in the readme.
        dealer = NetModel(field='dealer_id', _class=Dealer)


    obj = NetworkModel(1)

    dealer1 = Dealer(1)
    assert obj.dealer == dealer1
    ```

- `BaseInitializer` : Used as base class for SQLAlchemy models. It needs to be used in your super classes BEFORE the `db.Model`. For example `class VehicleReferencePrice(BaseInitializer, db.Model)` is correct but `class VehicleReferencePrice(db.Model, BaseInitializer)` is wrong. All it does is that it helps you with instantiation of your SQLAlchemy models so fields are instantiated in the correct order. If you don't use this base class, you need to make sure the SQLAlchemy fields are instantiated BEFORE the non-SQLAlchemy fields. For example `source_id` and `source_type` need to be instantiated BEFORE `source` which is a PolyField.

- `create_polymorphic_base` : creates base class from your data class to be added to your ref classes. Data class is where the `[prefix]_id` and `[prefix]_type]` fields along your PolyField are defined. Ref class[es] are which models that the polymorphic relationship points to. The relationship is automatically created for you by using the output of `create_polymorphic_base` as a base class in your ref class[es].

# Examples

Note: Please take a look at the [tutorial](#tutorial.md) for a step by step guide into the Polymorphic extension.
Also you can find actual working models in the [model tests](tests/models.py).

## Single relation:

```py
from polymorphic_sqlalchemy import create_polymorphic_base, PolyField, BaseInitializer
from sqlalchemy import Column, Integer, String


class VehicleReferencePrice(BaseInitializer, db.Model):

    __tablename__ = "vehicle_reference_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source = PolyField(prefix='source')


HasVehicleReferencePrices = create_polymorphic_base(data_class=VehicleReferencePrice,
                                                        data_class_attr='source')


class FairEstimatedValue(BaseInitializer, db.Model, HasVehicleReferencePrices):
    __tablename__ = "fair_estimated_value"
    id = Column(Integer, primary_key=True, autoincrement=True)

class SomeRecord(BaseInitializer, db.Model, HasVehicleReferencePrices):
    __tablename__ = "manheim_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
```

## multiple relations

```py
from polymorphic_sqlalchemy import create_polymorphic_base, Relation, PolyField, NetRelationship
from sqlalchemy import Column, Integer, String


class HasVehicleAssetTransfer():
    pass


class Dealer(object):
    """
    A network backed model
    Dealer model for the dealers table (pseudo)
    """

    def __init__(self, id):
        self.id = id

    def __eq__(self, other):
        """
        So you can do dealer_obj == another_dealer_obj
        """
        return self.id == other.id

    @classmethod
    def find(cls, id):
        return cls(id)

    def __repr__(self):
        return '< Dealer id: {} >'.format(self.id)


class Org(db.Model, HasVehicleAssetTransfer):
    __tablename__ = "org"

    id = Column(Integer, primary_key=True, autoincrement=True)
    def __repr__(self):
        return '< Org id: {} >'.format(self.id)


class Records(BaseInitializer, db.Model):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(String(50), nullable=False)
    buyer_type = Column(String(50), nullable=False)
    seller_id = Column(String(50), nullable=False)
    seller_type = Column(String(50), nullable=False)
    buyer__dealer = NetRelationship(prefix='buyer', _class=Dealer)  # Network backed fields
    seller__dealer = NetRelationship(prefix='seller', _class=Dealer)   # Network backed fields
    buyer = PolyField(prefix='buyer')
    seller = PolyField(prefix='seller')


relations = (
    Relation(data_class=Records, data_class_attr='buyer', ref_class_attr='buyer_records'),
    Relation(data_class=Records, data_class_attr='seller', ref_class_attr='seller_records')
)

HasVehicleAssetTransfer = create_polymorphic_base(relations=relations)
```

Now you can:

```py
dealer1 = Dealer(1)
dealer2 = Dealer(2)

org1 = Org(id=1)
org2 = Org(id=2)

rec1 = Records(buyer=org1, seller=dealer2, id=1)
rec2 = Records(buyer=org1, seller=org2, id=2)
rec3 = Records(buyer=dealer1, seller=dealer2, id=3)
rec4 = Records(buyer=dealer1, seller=org1, id=4)

assert rec1.buyer_type == 'org'
assert rec1.buyer_id == 1
assert rec1.buyer is org1
assert org1.buyer_records == [rec1, rec2]
assert org1.seller_records == [rec4]
assert rec3.buyer is dealer1
```

## Using Polymorphic extension with Single table inheritence

```py
class SourceOfData(db.Model):
    __tablename__ = 'source_of_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filter_type = Column(String(16), nullable=False)

    ADS_FILTER_TYPE = 'ads'
    NEWS_FILTER_TYPE = 'news'

    __mapper_args__ = {
        'polymorphic_on': filter_type
    }


class AdsData(SourceOfData, HasVehicle):
    __mapper_args__ = {
        'polymorphic_identity': SourceOfData.ADS_FILTER_TYPE
    }


class NewsData(SourceOfData, HasVehicle):
    __mapper_args__ = {
        'polymorphic_identity': SourceOfData.NEWS_FILTER_TYPE
    }
```

Note that `HasVehicle` is subclassed by the `AdsData` and `NewsData` but NOT by their superclass, `SourceOfData`.


# Behind the scene

Going back to this model:

```py
class Dealer:
    """ Dealer model for the dealers table (pseudo) """

    def __init__(self, id):
        self.id = id

    @classmethod
    def find(cls, id):
        return cls(id)

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return '< Dealer id: {} >'.format(self.id)


class Vehicle(BaseInitializer, db.Model):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source = PolyField(prefix='source')
    source__dealer = NetRelationship(prefix='source', _class=Dealer)

HasVehicle = create_polymorphic_base(data_class=Vehicle, data_class_attr='source')


class LocalDealer(BaseInitializer, db.Model, HasVehicle):
    __tablename__ = "local_dealer"
    id = Column(Integer, primary_key=True, autoincrement=True)
```

The vehicle model has the following attributes defined above:

```
id
source_id
source_type
source
source__dealer
```

The Polymorphic extension automatically adds the following attributes to the Vehicle model:

```
source__local_dealer  # A SQLAlchemy relationship to the local dealer table
```

Then when you ask for the source attribute which is a Polyfield, it grabs the source_type's content (let's say 'local_dealer') and the prefix ('source') and uses a delimiter to combine them. The delimiter is double underscore so the combination becomes 'source__local_dealer'. As you know `source__local_dealer` is a SQLAlchemy relationship that the create_polymorphic_base has already built for us. The Polyfield then returns the value of `source__local_dealer`. So in this case it just returns the SQLAlchemy relationship. But what if the `source_type` is a network backed item like `dealer` then what it tries to return is the value of `source__dealer`. And we have manually set the `source_dealer` to be a NetRelationship field in the model. The NetRelationship then goes and runs the `find` on the Dealer model and grabs the object. Then it caches it in `_source__dealer` so the next time you ask for it, it does not need to hit an external API. The cache gets invalidated if the `source_id` or `source_type` fields get modified. Hence the cache is invalidated properly. But when it comes to SQLAlchemy relationships, as you can see in the [Known Limitations and Bugs](#known-limitations-and-bugs), the relationship is not automatically updated to point to the correct object.

# Coming from older generate_polymorphic_listener_function

You can simply import:

`from polymorphic_sqlalchemy import generate_polymorphic_listener_function`

and use it as before.


# Running tests

`pip install requirements-dev.txt`

`pytest tests/`


# Known Limitations and Bugs

1. It is up to your implementation of the actual network backed model to provide the backref of the relationship. For example in the above example, there is `org1.buyer_records` automatically made for you since `org1` is a SQLAlchemy object. However `dealer1.buyer_records` is not automatically made for you,
2. The values of the actual SQLAlchemy fields that get saved into the database are currently only set when you initially assign the object to the field. If you later modify the object from reference table, the value of the field in the data table does not update automatically. The opposite of this is true too:

    ```py
    dealer2 = Dealer(2)

    org1 = Org(id=1)
    org2 = Org(id=2)

    rec1 = Records(buyer=org1, seller=dealer2, id=1)
    rec2 = Records(buyer=org1, seller=org2, id=2)

    rec1.buyer_id = 2
    # NOTE: This is a bug. A solution might be to use SQLAlchemy events to update the object.
    # The problem is that setting the object will again update the fields which causes an infinite loop.
    assert rec1.buyer is org1

    # The opposite of it is true too and is a bug. If the reference object gets modified and it is already set in the data model,
    # the values do not update.
    org1.id = 20
    assert rec2.buyer is org1
    assert rec2.buyer_id != org1.id
    ```


# Future developments

There is no plan to implement the following yet but in future we can combine the `[prefix]_id`, `[prefix]_type`, PolyField and NetRelationship all into one PolyField. And via Metaclass that Polyfield can dynamically generate all these other fields.
