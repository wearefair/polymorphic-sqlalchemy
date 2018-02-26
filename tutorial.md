# [Polymorphic extension](readme.md) Tutorial

Note: Actual example codes can be found in [model tests](tests/models.py).

In order to use the Polymorphic extension for SQLAlchemy you need to:

1. Define the Data Table and the Reference Table(s)
2. Define the PolyField
3. NetRelationship for network backed models
4. Relation: When you have more than one polymorphic relationship to the same table

## 1. Define the Data Table and the Reference Table(s)

The data table is where you would have traditionally put your foreign keys.
The reference table(s) are the tables that that the data table would have foreign keyed to. The reference table can be in another database or abstracted through an API end point and it exists somewhere else on the network.


```
  DATA TABLE
┏━━━━━━━━━━━━━┓       REF TABLE
┃Vehicle Table┃    ┏━━━━━━━━━━━━━┓
┣━━━━━━━━━━━━━┫    ┃  Org Table  ┃
┃ 1 BMW 3     ┃----┗━━━━━━━━━━━━━┛
┣━━━━━━━━━━━━━┫    ┏━━━━━━━━━━━━━┓
┃ 2 Tesla S   ┃----┃Dealer Table ┃
┗━━━━━━━━━━━━━┛    ┗━━━━━━━━━━━━━┛
                      REF TABLE
```

In the above case if your models were defined like this:

```py
from sqlalchemy import Column, Integer, String

class Vehicle(db.Model):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, autoincrement=True)

class Org(db.Model):
    __tablename__ = "org"
    id = Column(Integer, primary_key=True, autoincrement=True)

class Dealer(db.Model):
    __tablename__ = "dealer"
    id = Column(Integer, primary_key=True, autoincrement=True)
```

Then we define what is the data table via `create_polymorphic_base`.
The reference tables will subclass the resule of `create_polymorphic_base` :

```py
from polymorphic_sqlalchemy import create_polymorphic_base
from sqlalchemy import Column, Integer, String


class Vehicle(db.Model):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, autoincrement=True)


HasVehicle = create_polymorphic_base(data_class=Vehicle, ...)


class Org(BaseInitializer, db.Model, HasVehicle):
    __tablename__ = "org"
    id = Column(Integer, primary_key=True, autoincrement=True)

class Dealer(BaseInitializer, db.Model, HasVehicle):
    __tablename__ = "dealer"
    id = Column(Integer, primary_key=True, autoincrement=True)
```

You might wonder what is that BaseInitializer doing. It is there to make sure the SQLAlchemy fields are initialized before the Polymorphic fields (such as PolyField are initialized.)

## 2. Define the PolyField

Think of PolyField as a foreign key field that can point to different tables.
The PolyField itself is *not* stored in the database. However the PolyField stores the reference to other tables' data through two fields: the type field and the id field. The type field points to the name of the reference table and the id field is the id of the row in that reference table.

Basically it reads and writes to the `[prefix]_id` and `[prefix]_type` fields.
A PolyField that is named `source` needs 2 other fields: `source_id` and `source_type` :


```py
from polymorphic_sqlalchemy import create_polymorphic_base, PolyField, BaseInitializer
from sqlalchemy import Column, Integer, String

class Vehicle(BaseInitializer, db.Model):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source = PolyField(prefix='source')

HasVehicle = create_polymorphic_base(data_class=Vehicle, data_class_attr='source')

class Org(BaseInitializer, db.Model, HasVehicle):
    __tablename__ = "org"
    id = Column(Integer, primary_key=True, autoincrement=True)

class LocalDealer(BaseInitializer, db.Model, HasVehicle):
    __tablename__ = "dealer"
    id = Column(Integer, primary_key=True, autoincrement=True)
```

At this point you can use this relationship!

```py
org1 = Org()
dealer1 = LocalDealer()
db.session.add(org1)
db.session.add(dealer1)
# We flush to get the ID of org1 and dealer1
db.session.flush()

vehicle1 = Vehicle(source=org1)
vehicle2 = Vehicle(source=dealer1)
vehicle3 = Vehicle(source=org1)
vehicle4 = Vehicle(source=org1)

>>> vehicle1.source == org1
True
>>> vehicle1.source_id == 1
True
>>> vehicle2.source_type == 'local_dealer'
True
>>> org1.vehicles == [vehicle1, vehicle3, vehicle4]
True
```

## 3. NetRelationship for network backed models

The NetRelationship is used to define a network backed (or technically a non-SQLAlchemy) relationship. An example of it would be if the dealers table exists in another microservice and we have created a python model that provides the abstraction.

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

A simple example of it is if the dealer table was served by a separate service and we need to hit its API to get the object:

```py
class Dealer:
    """ Dealer model for the dealers table (pseudo) """

    def __init__(self, id, name=None):
        self.id = id
        self.name = name

    @classmethod
    def find(cls, id):
        name = get_dealer_name_from_external_service(id)
        return cls(id ,name)

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return '< Dealer id: {} >'.format(self.id)
```

The Polymorphic extension expects a factory class method called `find` that it uses to get the info from the external service to generate the class instance. Up to this point we have only had the Source field which is a PolyField to use SQLAlchemy relationships. In order to have source also consider the network backed Dealer model, we need to use NetRelationship:

```py
class Vehicle(BaseInitializer, db.Model):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source = PolyField(prefix='source')
    source__dealer = NetRelationship(prefix='source', _class=Dealer)
```

Note that the polymorphic extension is very sensitive to the names that you choose for the fields. The name of the network backed field has to be the name of the PolyField + `__` + the lowercase of the network backed model. In this case `source__dealer`.

```py
org1 = Org()
dealer1 = LocalDealer()  # SQLAlchemy model
dealer2 = Dealer.find(id=3)  # Network backed model
# We flush to get the ID of org1 and dealer1
db.session.flush()

vehicle1 = Vehicle(source=org1)
vehicle2 = Vehicle(source=dealer1)
vehicle3 = Vehicle(source=org1)
vehicle4 = Vehicle(source=org1)
vehicle5 = Vehicle(source=dealer2)

assert vehicle1.source == org1
assert vehicle1.source_id == 1
assert vehicle2.source_type == 'local_dealer'
assert org1.vehicles == [vehicle1, vehicle3, vehicle4]
assert vehicle5.source == dealer2
assert vehicle5.source_type == 'dealer'
```


## 4. Relation: When you have more than one polymorphic relationship to the same table

If you ever have more than one Polymorphic relationship to the same table, you will need to use `Relation` to inform the Polymorphic extension about the intricacies of your relationship.

Relation is a named tuple that takes optionally the following arguments:

`data_class, data_class_attr, ref_class_attr`

You might wonder why you even need this. Let's go back to the example. We know the source of each vehicle. But what if we want to know who bought the vehicle and who sold it. The buyer and the seller both could be organiaations or dealers or something else. In that case defining the following Polyfields is **not** enough:

```py
class Vehicle(BaseInitializer, db.Model):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source = PolyField(prefix='source')
    source__dealer = NetRelationship(prefix='source', _class=Dealer)
    buyer = PolyField(prefix='buyer')
    seller = PolyField(prefix='seller')
```

What we need is to explicitly define the relationships in the `create_polymorphic_base`.

```py
relations = (
    Relation(data_class=Records, data_class_attr='buyer', ref_class_attr='buyer_records'),
    Relation(data_class=Records, data_class_attr='seller', ref_class_attr='seller_records')
)

HasVehicle = create_polymorphic_base(relations=relations)
```

And if you want the buyer or seller to be able to be network backed objects too, you add the NetRelationship fields:

```py
class Vehicle(BaseInitializer, db.Model):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), nullable=False)
    source_type = Column(String(50), nullable=False)
    source = PolyField(prefix='source')
    source__dealer = NetRelationship(prefix='source', _class=Dealer)
    buyer = PolyField(prefix='buyer')
    buyer__dealer = NetRelationship(prefix='source', _class=Dealer)
    seller = PolyField(prefix='seller')
    seller__dealer = NetRelationship(prefix='source', _class=Dealer)
```

Now you can:

```py
org1 = Org()
dealer1 = LocalDealer()  # SQLAlchemy model
dealer2 = Dealer.find(id=3)  # Network backed model
db.session.add(org1)
db.session.add(dealer1)
# We flush to get the ID of org1 and dealer1
db.session.flush()

vehicle1 = Vehicle(source=org1)
vehicle2 = Vehicle(source=dealer1)
vehicle3 = Vehicle(source=org1)
vehicle4 = Vehicle(source=org1)
vehicle5 = Vehicle(source=dealer2)

>>> vehicle1.source == org1
True
>>> vehicle1.source_id == 1
True
>>> vehicle2.source_type == 'local_dealer'
True
>>> org1.vehicles == [vehicle1, vehicle3, vehicle4]
True
>>> vehicle5.source == dealer2
True
>>> vehicle5.source_type == 'dealer'
True
```
