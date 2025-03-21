from typing import List, Dict, Any
from app.models.base import db
from app.models.unit import UnitModel
from app.models.enums import UnitStatus


class UnitService:
    @staticmethod
    def get_all_units(floor_level: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get all units with optional filters"""
        query = db.select(UnitModel)

        if floor_level:
            query = query.filter(UnitModel.floor_level == floor_level)
        if status:
            query = query.filter(UnitModel.status == status)

        units = db.session.execute(query).scalars().all()
        return [UnitService._serialize_unit(unit) for unit in units]

    @staticmethod
    def get_available_units() -> List[Dict[str, Any]]:
        """Get all vacant units"""
        units = db.session.execute(
            db.select(UnitModel).filter_by(status=UnitStatus.VACANT)
        ).scalars().all()
        return [UnitService._serialize_unit(unit) for unit in units]

    @staticmethod
    def get_user_units(user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get units owned and rented by a user"""
        owned_units = db.session.execute(
            db.select(UnitModel).filter_by(user_id=user_id)
        ).scalars().all()

        rented_units = db.session.execute(
            db.select(UnitModel).filter_by(tenant_id=user_id)
        ).scalars().all()

        return {
            'owned_units': [UnitService._serialize_unit(unit) for unit in owned_units],
            'rented_units': [UnitService._serialize_unit(unit) for unit in rented_units]
        }

    @staticmethod
    def _serialize_unit(unit: UnitModel) -> Dict[str, Any]:
        """Convert unit model to dictionary"""
        return {
            'id': unit.unit_id,
            'status': unit.status.value,
            'size_sqm': unit.size_sqm,
            'monthly_rate': float(unit.monthly_rate),
            'floor_level': unit.floor_level,
            'climate_controlled': unit.climate_controlled
        }
