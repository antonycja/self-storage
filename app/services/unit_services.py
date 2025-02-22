import json
from typing import Optional, Dict, Any
from app.models import db, UnitModel, UnitStatus
from app.services.user_services import UserService
from sqlalchemy.exc import SQLAlchemyError


class UnitService():
    @staticmethod
    def get_unit_data(unit: UnitModel, current_user=None):
        """
        Returns secured unit details while ensuring sensitive data is protected.
        """
        unit_data = {
            "unit_id": unit.unit_id,
            "status": unit.status.value,
            "size_sqm": unit.size_sqm,
            "monthly_rate": unit.monthly_rate,
            "climate_controlled": unit.climate_controlled,
            "floor_level": unit.floor_level,
            "rental_duration_days": unit.rental_duration_days,
            "security_features": json.loads(unit.security_features),
            # Indicate if shared, but hide emails
            "is_shared": bool(unit.shared_user_emails),
        }

        # Only return `shared_user_emails` if user owns or shares the unit
        if current_user and current_user.is_authenticated:
            if (current_user.id == unit.user_id or current_user.email in unit.shared_user_emails):
                unit_data["shared_user_emails"] = json.loads(
                    unit.shared_user_emails)

            # Hide `tenant_id`, but optionally return `tenant_email`
            if current_user and current_user.id == unit.user_id:
                tenant_email = None
                if unit.tenant_id:
                    tenant = UserService.get_user_by_id(unit.tenant_id)
                    tenant_email = tenant.email if tenant else None
                unit_data["tenant_email"] = tenant_email

        return unit_data

    @staticmethod
    def get_all_units():
        try:
            # Query all units
            units = db.session.execute(db.select(UnitModel)).scalars().all()

            if not units:
                return {"error": {"Not Found": "Sorry, we couldn't find any units."}}

            # Return the unit data
            return [UnitService.get_unit_data(unit) for unit in units]

        except SQLAlchemyError as e:
            # print(f"Database error: {e}")
            return {"error": {"Database Error": "There was an issue retrieving the units from the database."}}
        except Exception as e:
            # print(f"Unexpected error: {e}")
            return {"error": {"Unexpected Error": "An unexpected error occurred while retrieving the units."}}

    @staticmethod
    def get_available_units():
        try:
            # Query available units
            units = db.session.execute(
                db.select(UnitModel).filter_by(status=UnitStatus.AVAILABLE.value)).scalars().all()

            if not units:
                return {"error": {"Not Found": "Sorry, we couldn't find any available units."}}

            # Return the unit data
            return [UnitService.get_unit_data(unit) for unit in units]

        except SQLAlchemyError as e:
            # print(f"Database error: {e}")
            return {"error": {"Database Error": "There was an issue retrieving available units from the database."}}
        except Exception as e:
            # print(f"Unexpected error: {e}")
            return {"error": {"Unexpected Error": "An unexpected error occurred while retrieving available units."}}

    @staticmethod
    def get_unit_by_owner(owner_id: int, current_user=None):
        try:
            # Query units by owner_id
            units = db.session.execute(
                db.select(UnitModel).filter_by(user_id=owner_id)).scalars().all()

            if not units:
                return {"error": {"Not Found": "Sorry, we couldn't find any units for the specified owner."}}
            print(units[0].owner.name)
            # Secure the response (considering current_user)
            return [UnitService.get_unit_data(unit, current_user) for unit in units]

        except SQLAlchemyError as e:
            # print(f"Database error: {e}")
            return {"error": {"Database Error": "There was an issue retrieving the units by owner from the database."}}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {"error": {"Unexpected Error": "An unexpected error occurred while retrieving units by owner."}}
