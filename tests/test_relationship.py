from models import (db, Dealer, LocalDealer, Company, Org, Records, VehicleReferencePrice,
                    FairEstimatedValue, SomeRecord, Vehicle, AdsData, NewsData)


class TestBaseInitializer:

    def test_poly_base(self):
        db.create_all()

        dealer1 = Dealer(1)
        dealer10 = Dealer(10)
        company1 = Company(id=1, dealer=dealer1)

        assert company1.dealer == dealer1
        assert company1.dealer_id == 1

        company1.dealer_id = 10

        assert company1.dealer == dealer10

        assert repr(company1) == '<Company id: 1>'


class TestPolymorphicGenerator:

    def test_polymorphic_generator_relationships(self):
        db.create_all()

        dealer1 = Dealer(1)
        dealer2 = Dealer(2)

        org1 = Org(id=1)
        org2 = Org(id=2)
        company1 = Company(id=1, dealer=dealer1)

        rec1 = Records(buyer=org1, seller=dealer2, id=1)
        rec2 = Records(buyer=org1, seller=org2, id=2)
        rec3 = Records(buyer=dealer1, seller=dealer2, id=3)
        rec4 = Records(buyer=dealer1, seller=org1, id=4)
        rec5 = Records(buyer=org1, seller=company1, id=5)

        assert rec1.buyer_type == 'org'
        assert rec1.buyer_id == 1
        assert rec1.buyer is org1
        assert org1.buyer_records == [rec1, rec2, rec5]
        assert org1.seller_records == [rec4]
        assert rec5.seller is company1

        # The cache for Network backed model is properly invalidated
        assert rec3.buyer is dealer1
        rec3.buyer_id = 2
        assert rec3.buyer is not dealer2  # It is a new object so the identity check fails
        assert rec3.buyer == dealer2

        rec1.buyer_id = 2
        # NOTE: This is a bug. A solution might be to use SQLAlchemy events to update the object.
        # The problem is that setting the object will again update the fields which causes an infinite loop.
        assert rec1.buyer is org1

        # The opposite of it is true too and is a bug.
        # If the reference object gets modified and it is already set in the data model,
        # the values do not update.
        org1.id = 20
        assert rec2.buyer is org1
        assert rec2.buyer_id != org1.id

        db.session.add(org1)
        db.session.add(rec1)
        db.session.add(rec2)
        db.session.add(rec3)
        db.session.add(rec4)
        db.session.add(rec5)
        db.session.flush()  # Making sure that DB does not complain.
        db.session.rollback()

    def test_polymorphic_generator_one_relationship(self):
        db.create_all()

        fev1 = FairEstimatedValue()
        some1 = SomeRecord()
        db.session.add(fev1)
        db.session.add(some1)
        # We flush to get the ID of fev1 and some1
        db.session.flush()

        vat1 = VehicleReferencePrice(source=fev1)
        vat2 = VehicleReferencePrice(source=some1)
        vat3 = VehicleReferencePrice(source=fev1)
        vat4 = VehicleReferencePrice(source=fev1)

        assert vat1.source == fev1
        assert vat1.source_id == 1
        assert vat2.source_type == 'some_record'
        assert fev1.vehicle_reference_prices == [vat1, vat3, vat4]
        db.session.flush()
        db.session.rollback()

    def test_polymorphic_generator_one_relationship_readme_example(self):
        db.create_all()

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

        assert vehicle1.source == org1
        assert vehicle1.source_id == 1
        assert vehicle2.source_type == 'local_dealer'
        assert org1.vehicles == [vehicle1, vehicle3, vehicle4]
        assert vehicle5.source == dealer2
        assert vehicle5.source_type == 'dealer'

        db.session.flush()
        db.session.rollback()


class TestInheritence:

    def test_single_table_inheritence(self):
        db.create_all()

        ads1 = AdsData()
        news1 = NewsData()
        db.session.add(ads1)
        db.session.add(news1)
        db.session.flush()
        vehicle1 = Vehicle(source=ads1)
        vehicle2 = Vehicle(source=ads1)
        vehicle3 = Vehicle(source=news1)

        assert vehicle1.source == ads1
        assert vehicle1.source_id == 1
        assert vehicle1.source_type == "ads_data"
        assert ads1.vehicles == [vehicle1, vehicle2]
        assert news1.vehicles == [vehicle3]
        db.session.flush()
        db.session.rollback()
