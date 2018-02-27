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


class Org(db.Model, HasVehicle):
    __tablename__ = "org"
    id = Column(Integer, primary_key=True, autoincrement=True)

class Dealer(db.Model, HasVehicle):
    __tablename__ = "dealer"
    id = Column(Integer, primary_key=True, autoincrement=True)
```


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

class Org(db.Model, HasVehicle):
    __tablename__ = "org"
    id = Column(Integer, primary_key=True, autoincrement=True)

class LocalDealer(db.Model, HasVehicle):
    __tablename__ = "dealer"
    id = Column(Integer, primary_key=True, autoincrement=True)
```


You might wonder what is that BaseInitializer doing. It is there to make sure the SQLAlchemy fields are initialized before the Polymorphic fields (such as PolyField are initialized.)

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

>>> vehicle1.source
<org id: 1>
>>> vehicle1.source_id
1
>>> vehicle2.source_type
local_dealer
>>> org1.vehicles
[<vehicle id:1>, <vehicle id:3>, <vehicle id:4>]
```

## 3. NetRelationship for network backed models

Once you start getting into the microservices architecture, you will soon find that deciding the boundaries of services data becomes a difficult problem.

Let's say you have a Service 1 and that deals with vehicle and organizations and service 2 that deals with dealers. The first choice that you might make is to share the database between the 2 services.


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


But that makes your services heavily coupled and the single database very quickly becomes your bottleneck. What is recommended is to have a separate database per service and only keep the IDs from the other services in your own database as if you were having foreign key relationships to those tables. Then design API endpoints to fetch the appropriate data from the other services. We call these network backed models.

The NetRelationship is used to define these network backed (or technically a non-SQLAlchemy) relationships.

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

A simple example network backed dealers model:

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

>>> vehicle1.source
<org id:1>
>>> vehicle1.source_id
1
>>> vehicle2.source_type
local_dealer
>>> org1.vehicles
[<vehicle id:1>, <vehicle id:3>, <vehicle id:4>]
>>> vehicle5.source
<dealer id:2>
>>> vehicle5.source_type
dealer
```


## 4. Relation: When you have more than one polymorphic relationship to the same table

If you ever have more than one Polymorphic relationship to the same table, you will need to use `Relation` to inform the Polymorphic extension about the intricacies of your relationship.

Relation is a named tuple that takes optionally the following arguments:

`data_class, data_class_attr, ref_class_attr`

You might wonder why you even need this. Let's go back to the example. Previously we had a source field for each vehicle. The source could be an organization or a dealer. But what if we want to know who bought the vehicle and who sold it? The buyer and the seller both could be organiations or dealers.

```py
class Records(BaseInitializer, db.Model):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(String(50), nullable=False)
    buyer_type = Column(String(50), nullable=False)
    buyer = PolyField(prefix='buyer')
    buyer__dealer = NetRelationship(prefix='buyer', _class=Dealer)
    seller_id = Column(String(50), nullable=False)
    seller_type = Column(String(50), nullable=False)
    seller = PolyField(prefix='seller')
    seller__dealer = NetRelationship(prefix='seller', _class=Dealer)
```

What we need is to explicitly define the relationships in the `create_polymorphic_base`.

```py
relations = (
    Relation(data_class=Records, data_class_attr='buyer', ref_class_attr='buyer_records'),
    Relation(data_class=Records, data_class_attr='seller', ref_class_attr='seller_records')
)

HasRecord = create_polymorphic_base(relations=relations)


class Org(db.Model, HasRecord):
    __tablename__ = "org"
    id = Column(Integer, primary_key=True, autoincrement=True)
```

Now you can:

```py
dealer1 = Dealer(1)
dealer2 = Dealer(2)

org1 = Org(id=1)
org2 = Org(id=2)

# we specify the IDs here so we don't need to flush to db yet to get the ID
rec1 = Records(buyer=org1, seller=dealer2, id=1)
rec2 = Records(buyer=org1, seller=org2, id=2)
rec3 = Records(buyer=dealer1, seller=dealer2, id=3)
rec4 = Records(buyer=dealer1, seller=org1, id=4)

>>> rec1.buyer_type
org
>>> rec1.buyer_id
1
>>> rec1.buyer is org1
True
>>> org1.buyer_records
[rec1, rec2, rec5]
>>> org1.seller_records
[rec4]

# The cache for Network backed model is properly invalidated
>>> rec3.buyer is dealer1
True
>>> rec3.buyer_id = 2
>>> rec3.buyer == dealer2
True
# The identity check fails because the cache was invalidated and we used the `find` function to grab a new copy of dealer2
>>> rec3.buyer is dealer2
False


# The cache for SQLAlchemy objects is not properly invalidated
>>> rec1.buyer_id = 2
# NOTE: This is a bug. A solution might be to use SQLAlchemy events to update the object.
# The problem is that setting the object will again update the fields which causes an infinite loop.
>>> rec1.buyer is org1  # but it should be org2 since we updated the buyer_id
True

# The opposite of it is true too and is a bug.
# If the reference object gets modified and it is already set in the data model,
# the values do not update.
org1.id = 20
>>> rec2.buyer is org1
True
>>> rec2.buyer_id == org1.id
False
```
