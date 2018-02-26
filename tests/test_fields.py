from polymorphic_sqlalchemy import NetRelationship, PolyField, NetModel
from models import Dealer


class NetworkModel1:

    def __init__(self):
        self.seller_type = None
        self.seller_id = None
        self.buyer_type = None
        self.buyer_id = None

    seller__dealer = NetRelationship(prefix='seller', _class=Dealer)
    buyer__dealer = NetRelationship(prefix='buyer', _class=Dealer)


class TestNetRelationship:

    def test_net_field(self):
        dealer1 = Dealer(1)
        dealer2 = Dealer(2)

        obj = NetworkModel1()
        obj.seller__dealer = dealer1
        obj.buyer__dealer = dealer2

        assert obj.seller_type == 'dealer'
        assert obj.buyer_type == 'dealer'
        assert obj.seller_id == 1
        assert obj.buyer_id == 2
        assert obj.seller__dealer is dealer1
        assert obj.buyer__dealer is dealer2

        del obj._seller__dealer
        assert obj.seller__dealer.id == 1



class PolyModel:

    def __init__(self, buyer__dealer=None, buyer_type=None):
        self.buyer_type = buyer_type
        self.buyer__dealer = buyer__dealer

    buyer = PolyField(prefix='buyer')


class TestPolyField:

    def test_poly_field_set_and_get(self):
        dealer1 = Dealer(1)

        obj = PolyModel()
        obj.buyer = dealer1

        assert obj.buyer__dealer is dealer1

    def test_poly_field_get(self):
        dealer1 = Dealer(1)
        dealer2 = Dealer(2)

        obj = PolyModel(buyer__dealer=dealer1, buyer_type='dealer')

        assert obj.buyer is dealer1

        obj.buyer = dealer2
        assert obj.buyer__dealer is dealer2


class NetworkModel2:

    def __init__(self, dealer_id):
        self.dealer_id = dealer_id

    dealer = NetModel(field='dealer_id', _class=Dealer)


class TestNetModel:

    def test_net_object(self):
        obj = NetworkModel2(1)

        dealer1 = Dealer(1)
        result = obj.dealer
        assert result == dealer1
