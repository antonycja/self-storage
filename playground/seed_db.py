# seed_database.py
from app.models import db, UnitModel, UserModel, UnitStatus
from app import create_app
from random import choice, randint, uniform, random
from datetime import datetime
from json import dumps

def seed_users():
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
            "password": "$2b$12$3yCYvndv80Y1fA..nuvR2epdalKIAJetsX8Y6Wn.MCHzvX0V0aH02,",
            "created_at": datetime(2025, 2, 21, 17, 58, 28, 148969),
            "updated_at": datetime(2025, 2, 21, 17, 58, 28, 148974)
        }
    ]

    # Create user objects
    user_objects = []
    for user_data in users:
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
    if status in ['occupied', 'reserved']:
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
    db.session.query(UnitModel).delete()

    # Define possible values for categorical fields
    statuses = [status.value for status in UnitStatus]
    floor_levels = ['ground', 'first', 'second', 'basement']
    climate_options = ['yes', 'no']
    security_features_list = [
        'Basic (Lock and Key)',
        'Standard (Lock and Security Camera)',
        'Premium (24/7 Monitoring, Individual Alarm)',
        'Elite (Biometric Access, 24/7 Monitoring, Individual Alarm)'
    ]

    # Create 50 sample units
    units = []
    for i in range(50):
        # Calculate a realistic monthly rate based on size
        size = round(uniform(5.0, 50.0), 1)
        base_rate = size * 20  # Base rate of $20 per square meter

        # Add premium for climate control and security features
        climate_controlled = choice(climate_options)
        security_level = choice(security_features_list)

        # Adjust rate based on features
        rate_multiplier = 1.0
        if climate_controlled == 'yes':
            rate_multiplier += 0.2  # 20% premium for climate control
        if 'Premium' in security_level:
            rate_multiplier += 0.15  # 15% premium for premium security
        elif 'Elite' in security_level:
            rate_multiplier += 0.25  # 25% premium for elite security

        monthly_rate = round(base_rate * rate_multiplier, 2)

        # Determine status and assign tenants
        status = choice(statuses)
        tenant_id, is_shared, shared_with_emails = assign_tenants(status, size)

        # Create unit with random owner (including admin)
        unit = UnitModel(
            unit_id=i + 1,
            status=status,
            size_sqm=size,
            monthly_rate=round(base_rate * rate_multiplier, 2),
            climate_controlled=climate_controlled,
            floor_level=choice(floor_levels),
            security_features=dumps([security_level]),
            rental_duration_days=choice([30, 90, 180, 365]),
            user_id=randint(1, 5),  # Random owner (including admin)
            tenant_id=tenant_id,  # Main tenant (if unit is occupied/reserved)
            shared_user_emails=dumps(shared_with_emails)  # List of emails for additional tenants
        )
        units.append(unit)

    # Add all units to the database
    db.session.bulk_save_objects(units)
    db.session.commit()

    print(f"Successfully created {len(units)} sample storage units")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        try:
            # Seed users first to ensure they exist for the unit foreign keys
            seed_users()
            seed_units()
            print("Database seeding completed successfully!")
        except Exception as e:
            print(f"Error seeding database: {e}")
