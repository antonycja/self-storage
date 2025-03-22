# seed_database.py
from app.models.enums import UnitStatus
from app.models.securityFeature import SecurityFeatureModel, SecurityFeatureType
from app.models.unit import UnitModel
from app.models.base import db
from random import randint, choice, sample, random, uniform
from app import create_app
from random import choice, randint, uniform, random
from datetime import datetime, timedelta
import json
from werkzeug.security import generate_password_hash
from app.models.enums import UnitStatus  # Add this import


def seed_users():
    from app.models.base import db
    from app.models.user import UserModel

    # Clear existing users
    db.session.query(UserModel).delete()

    # User data from provided CSV
    users = [
        {
            "id": 1,
            "name": "Admin",
            "surname": "User",
            "email": "admin@user.com",
            "password": "$2b$12$MhC3HQ4ukAVhoLRr3DaWFOrZZoU1kAuk6I/8y7I0bMwr9peBaXd.O",
            "created_at": datetime(2025, 2, 21, 17, 52, 50, 315406),
            "updated_at": datetime(2025, 2, 21, 17, 52, 50, 315413)
        },
        {
            "id": 2,
            "name": "User",
            "surname": "1",
            "email": "user1@email.com",
            "password": "$2b$12$VYwo7GqAZYMvw/y9cut.i.HNuTsI87eX2RraRwSoyAi5qfvj6vbCS",
            "created_at": datetime(2025, 2, 21, 17, 54, 35, 676119),
            "updated_at": datetime(2025, 2, 21, 17, 54, 35, 676125)
        },
        {
            "id": 3,
            "name": "User",
            "surname": "2",
            "email": "user2@email.com",
            "password": "$2b$12$VndXoTFIkdZuazH5OSBSpe0BQ/yWT3hmFMo9.ihiPK8WNmjhCDXTy",
            "created_at": datetime(2025, 2, 21, 17, 55, 16, 868805),
            "updated_at": datetime(2025, 2, 21, 17, 55, 16, 868813)
        },
        {
            "id": 4,
            "name": "User",
            "surname": "3",
            "email": "user3@email.com",
            "password": "$2b$12$2d7hJVRUPfms5XgLYy7hXujqx05BsR1FR/AtcRfvZWqYbGBekvfUm",
            "created_at": datetime(2025, 2, 21, 17, 57, 51, 116218),
            "updated_at": datetime(2025, 2, 21, 17, 57, 51, 116225)
        },
        {
            "id": 5,
            "name": "User",
            "surname": "4",
            "email": "user4@email.com",
            "password": "$2b$12$3yCYvndv80Y1fA..nuvR2epdalKIAJetsX8Y6Wn.MCHzvX0V0aH02",
            "created_at": datetime(2025, 2, 21, 17, 58, 28, 148969),
            "updated_at": datetime(2025, 2, 21, 17, 58, 28, 148974)
        }
    ]

    # Create user objects
    user_objects = []
    for user_data in users:
        # Unpack dictionary into keyword arguments
        user = UserModel(**user_data)
        user_objects.append(user)

    # Add all users to the database
    db.session.bulk_save_objects(user_objects)
    db.session.commit()

    print(f"Successfully created {len(user_objects)} users")


def get_user_email(user_id):
    """Helper function to get user email by ID"""
    user_emails = {
        2: "user1@email.com",
        3: "user2@email.com",
        4: "user3@email.com",
        5: "user4@email.com"
    }
    return user_emails.get(user_id)


def assign_tenants(status, size_sqm):
    """Helper function to assign tenants based on unit status"""
    from random import random, randint, choice

    if status in [UnitStatus.OCCUPIED.value, UnitStatus.RESERVED.value]:
        # 30% chance of being a shared unit for units over 20 sqm
        is_shared = size_sqm > 20 and random() < 0.3

        # Assign main tenant
        tenant_id = randint(2, 5)  # Exclude admin user (ID 1)

        if is_shared:
            # Get 1-2 additional tenants (different from main tenant)
            shared_with_emails = []
            potential_tenants = list(range(2, 6))  # IDs 2-5
            potential_tenants.remove(tenant_id)  # Remove main tenant from pool

            num_additional = randint(1, 2)
            additional_tenant_ids = []
            for _ in range(num_additional):
                if potential_tenants:
                    additional_id = choice(potential_tenants)
                    potential_tenants.remove(additional_id)
                    additional_tenant_ids.append(additional_id)

            # Convert additional tenant IDs to emails
            shared_with_emails = [get_user_email(
                tid) for tid in additional_tenant_ids]
            return tenant_id, True, shared_with_emails
        else:
            return tenant_id, False, []

    return None, False, []


def seed_units():
    # Clear existing data
    db.session.query(SecurityFeatureModel).delete()
    db.session.query(UnitModel).delete()
    db.session.commit()

    for i in range(50):
        # Define possible values for categorical fields
        statuses = [status for status in UnitStatus]
        floor_levels = ['Ground Floor', '1st Floor', '2nd Floor', 'Basement']

        # Sample locations
        locations = [
            {
                'country': 'South Africa',
                'city': 'Cape Town',
                'areas': ['Sea Point', 'Green Point', 'Camps Bay', 'Observatory']
            },
            {
                'country': 'South Africa',
                'city': 'Johannesburg',
                'areas': ['Sandton', 'Rosebank', 'Randburg', 'Braamfontein']
            }
        ]

        # Generate location data
        location = choice(locations)
        area = choice(location['areas'])

        # Calculate base rate
        size = round(uniform(5.0, 50.0), 1)
        base_rate = size * 20  # Base rate of R20 per square meter

        # Climate control
        climate_controlled = bool(random() < 0.3)  # 30% chance
        rate_multiplier = 1.2 if climate_controlled else 1.0

        # Determine status and assign tenants
        status = choice(statuses)
        tenant_id, is_shared, shared_with_emails = assign_tenants(
            status.value, size)

        if status == UnitStatus.OCCUPIED and tenant_id is None:
            status = UnitStatus.VACANT

        # Create unit first and add to session
        unit = UnitModel(
            unit_id=f"UNIT-{i+1:03d}",
            unit_name=f"{area} Storage Unit {i+1}",
            country=location['country'],
            city=location['city'],
            address_link=f"https://maps.google.com/?q={'+'.join(area.split())},{'+'.join(location['city'].split())}",
            status=status,
            size_sqm=size,
            monthly_rate=base_rate,
            climate_controlled=climate_controlled,
            floor_level=choice(floor_levels),
            rental_duration_days=choice([30, 90, 180, 365]),
            user_id=randint(1, 5),
            tenant_id=tenant_id,
            shared_user_emails=shared_with_emails
        )

        db.session.add(unit)
        db.session.flush()  # This ensures the unit has an ID

        # Generate security features
        num_features = randint(1, 4)
        selected_features = [SecurityFeatureType.BASIC]  # Always include basic

        # Add additional random features
        available_features = [
            f for f in SecurityFeatureType if f != SecurityFeatureType.BASIC]
        if num_features > 1:
            additional_features = sample(available_features, min(
                num_features - 1, len(available_features)))
            selected_features.extend(additional_features)

        # Create and add security features
        for feature in selected_features:
            security_feature = SecurityFeatureModel(
                unit_id=unit.unit_id,
                feature_type=feature,
                notes=f"Installed in 2024" if feature == SecurityFeatureType.CCTV else None
            )
            db.session.add(security_feature)

            # Update rate multiplier
            if feature in [SecurityFeatureType.BIOMETRIC, SecurityFeatureType.GUARDS]:
                rate_multiplier += 0.15
            elif feature in [SecurityFeatureType.CCTV, SecurityFeatureType.ACCESS]:
                rate_multiplier += 0.10
            elif feature in [SecurityFeatureType.ALARM, SecurityFeatureType.MOTION]:
                rate_multiplier += 0.05

        # Update final rate
        unit.monthly_rate = round(base_rate * rate_multiplier, 2)

    try:
        db.session.commit()
        print(f"Successfully created 50 units with security features")
    except Exception as e:
        print(f"Error creating units and features: {e}")
        db.session.rollback()

# Add this function to verify the seeding


def verify_security_features():
    """Verify security features were properly created"""
    features = db.session.query(SecurityFeatureModel).count()
    units = db.session.query(UnitModel).count()
    print(f"Created {features} security features for {units} units")

    # Sample check
    sample_unit = db.session.query(UnitModel).first()
    if sample_unit:
        print(f"\nSample unit {sample_unit.unit_id} features:")
        for feature in sample_unit.security_features:
            print(f"- {feature.feature_name}")


def seed_rentals():
    """Generate sample rental agreements based on occupied units"""
    from app.models.base import db
    from app.models.rental import RentalModel
    from app.models.unit import UnitModel
    from app.models.enums import UnitStatus

    # Clear existing rentals
    db.session.query(RentalModel).delete()

    # Get all occupied units using the enum value
    occupied_units = db.session.query(UnitModel).filter(
        UnitModel.status == UnitStatus.OCCUPIED
    ).all()

    print(f"Found {len(occupied_units)} occupied units")  # Debug print

    rentals = []
    for unit in occupied_units:
        # Debug print to check unit and tenant details
        print(f"Processing unit {unit.unit_id} with tenant {unit.tenant_id}")

        if unit.tenant_id is None:
            print(f"Warning: Unit {unit.unit_id} has no tenant assigned")
            continue

        # Create a rental agreement for each occupied unit
        now = datetime.now()
        start_date = now - timedelta(days=randint(1, 60))
        end_date = start_date + timedelta(days=unit.rental_duration_days)

        rental = RentalModel(
            unit_id=unit.unit_id,
            tenant_id=unit.tenant_id,  # This should not be None
            start_date=start_date,
            end_date=end_date,
            monthly_rate=unit.monthly_rate,
            status='active' if end_date > now else 'expired',
            created_at=start_date,
            updated_at=now
        )
        rentals.append(rental)

    # Add all rentals to the database
    if rentals:
        try:
            db.session.bulk_save_objects(rentals)
            db.session.commit()
            print(f"Successfully created {len(rentals)} rental agreements")
        except Exception as e:
            print(f"Error creating rentals: {e}")
            db.session.rollback()
    else:
        print("No valid occupied units found to create rentals for")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        try:
            # Seed users first to ensure they exist for the unit foreign keys
            seed_users()
            seed_units()
            seed_rentals()  # Add rental agreements for occupied units
            verify_security_features()  # Verify the seeding
            print("Database seeding completed successfully!")
        except Exception as e:
            print(f"Error seeding database: {e}")
