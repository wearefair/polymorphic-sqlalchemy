import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from polymorphic_sqlalchemy import (create_polymorphic_base, Relation,
                                    PolyField, NetRelationship, NetModel, BaseInitializer)
from sqlalchemy import Column, Integer, String

test_app = Flask(__name__)
test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
db = SQLAlchemy(test_app)


logger = logging.getLogger(__name__)


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


class Records(BaseInitializer, db.Model):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_id = Column(String(50), nullable=False)
    buyer_type = Column(String(50), nullable=False)
    seller_id = Column(String(50), nullable=False)
    seller_type = Column(String(50), nullable=False)
    buyer__dealer = NetRelationship(prefix='buyer', _class=Dealer)
    seller__dealer = NetRelationship(prefix='seller', _class=Dealer)
    buyer = PolyField(prefix='buyer')
    seller = PolyField(prefix='seller')


relations = (
    Relation(data_class=Records, data_class_attr='buyer', ref_class_attr='buyer_records'),
    Relation(data_class=Records, data_class_attr='seller', ref_class_attr='seller_records')
)

HasRecord = create_polymorphic_base(relations=relations)


class Org(db.Model, HasRecord, HasVehicle):
    __tablename__ = "org"

    id = Column(Integer, primary_key=True, autoincrement=True)

    def __repr__(self):
        return '< Org id: {} >'.format(self.id)


class Company(BaseInitializer, db.Model, HasRecord):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dealer_id = Column(Integer, nullable=False)
    dealer = NetModel(field='dealer_id', _class=Dealer)


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
    __tablename__ = "some_records"
    id = Column(Integer, primary_key=True, autoincrement=True)


# ------------- Single Table InheritAnce -------------

class SourceOfData(db.Model):
    __tablename__ = 'juices'

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
