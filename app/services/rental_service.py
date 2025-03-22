from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from flask import json
from sqlalchemy.exc import IntegrityError
from app.models.base import db
from app.models.rental import RentalModel
from app.models.unit import UnitModel
from app.models.enums import UnitStatus
from app.models.user import UserModel


class RentalService:
    @staticmethod
    def create_rental(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new rental agreement"""
        try:
            # Validate unit availability
            unit = db.session.execute(
                db.select(UnitModel).filter_by(unit_id=data['unit_id'])
            ).scalar_one_or_none()

            if not unit:
                return {"error": "Unit not found"}

            if unit.status != UnitStatus.VACANT:
                return {"error": "Unit is not available for rent"}

            # Create rental agreement
            rental = RentalModel(
                unit_id=data['unit_id'],
                tenant_id=data['tenant_id'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                monthly_rate=unit.monthly_rate,
                status='active',
                created_at=datetime.now(tz=timezone.utc)
            )

            # TODO: Change this when payment methods is implemented
            # Update unit status
            unit.status = UnitStatus.OCCUPIED
            unit.tenant_id = data['tenant_id']

            db.session.add(rental)
            db.session.commit()

            return RentalService._serialize_rental(rental)

        except IntegrityError:
            db.session.rollback()
            return {"error": "Database integrity error"}
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to create rental: {str(e)}"}

    @staticmethod
    def get_rental_by_id(rental_id: int, current_user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get rental agreement by ID"""
        rental = db.session.execute(
            db.select(RentalModel).filter_by(id=rental_id)
        ).scalar_one_or_none()

        return RentalService._serialize_rental(rental, current_user_id) if rental else None

    @staticmethod
    def get_user_rentals(user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get all rentals for a user (both as tenant and owner)"""
        # Get rentals where user is tenant
        tenant_rentals = db.session.execute(
            db.select(RentalModel).filter_by(tenant_id=user_id)
        ).scalars().all()

        # Get rentals where user is unit owner
        owner_rentals = db.session.execute(
            db.select(RentalModel)
            .join(UnitModel)
            .filter(UnitModel.user_id == user_id)
        ).scalars().all()

        return {
            'as_tenant': [RentalService._serialize_rental(r, user_id) for r in tenant_rentals],
            'as_owner': [RentalService._serialize_rental(r, user_id) for r in owner_rentals]
        }

    @staticmethod
    def update_rental(rental_id: int, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Update rental agreement"""
        try:
            rental = db.session.execute(
                db.select(RentalModel).filter_by(id=rental_id)
            ).scalar_one_or_none()

            if not rental:
                return {"error": "Rental not found"}

            # Verify user is either tenant or unit owner
            if not (str(rental.tenant_id) == str(user_id) or str(rental.unit.user_id) == str(user_id)):
                return {"error": "Unauthorized to modify this rental"}

            # Handle status changes
            if 'status' in data:
                if data['status'] == 'terminated':
                    rental.end_date = datetime.now(tz=timezone.utc)
                    rental.unit.status = UnitStatus.VACANT
                    rental.unit.tenant_id = None

            allowed_fields = ['end_date', 'status']
            for field in allowed_fields:
                if field in data:
                    setattr(rental, field, data[field])

            rental.updated_at = datetime.now(tz=timezone.utc)
            db.session.commit()

            return RentalService._serialize_rental(rental)

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to update rental: {str(e)}"}

    @staticmethod
    def terminate_rental(rental_id: int, user_id: int) -> Dict[str, Any]:
        """Early termination of rental agreement"""
        try:
            rental = db.session.execute(
                db.select(RentalModel).filter_by(id=rental_id)
            ).scalar_one_or_none()

            if not rental:
                return {"error": "Rental not found"}

            # Verify user is either tenant or unit owner
            if not (str(rental.tenant_id) == str(user_id) or str(rental.unit.user_id) == str(user_id)):
                return {"error": "Unauthorized to terminate this rental"}

            if rental.status != 'active':
                return {"error": "Rental is not active"}

            # Update rental and unit
            rental.status = 'terminated'
            rental.end_date = datetime.now(tz=timezone.utc)
            rental.updated_at = datetime.now(tz=timezone.utc)

            rental.unit.status = UnitStatus.VACANT
            rental.unit.tenant_id = None

            db.session.commit()

            return {"message": "Rental terminated successfully"}

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to terminate rental: {str(e)}"}

    @staticmethod
    def _serialize_rental(rental: RentalModel, current_user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Convert rental model to dictionary
        Args:
            rental: The rental to serialize
            current_user_id: ID of the requesting user (None for public access)
        """
        # Check if user is authorized to see sensitive info
        shared_users = json.loads(rental.shared_user_emails or '[]')
        current_user = None
        if current_user_id:
            current_user = db.session.query(UserModel).get(current_user_id)

        is_authorized = (
            current_user_id and (
                str(current_user_id) == str(rental.tenant_id) or  # Is tenant
                str(current_user_id) == str(rental.unit.user_id) or  # Is owner
                (current_user and current_user.email in shared_users)  # Is shared user
            )
        )

        # Base serialization (public info)
        serialized = {
            'id': rental.id,
            'unit_id': rental.unit_id,
            'start_date': rental.start_date.isoformat(),
            'end_date': rental.end_date.isoformat(),
            'status': rental.status,
            'created_at': rental.created_at.isoformat(),
            'updated_at': rental.updated_at.isoformat() if rental.updated_at else None,
            'unit': {
                'id': rental.unit.unit_id,
                'name': rental.unit.unit_name,
                'location': f"{rental.unit.city}, {rental.unit.country}"
            }
        }

        # Add sensitive info only if authorized
        if is_authorized:
            serialized.update({
                'tenant_id': rental.tenant_id,
                'monthly_rate': float(rental.monthly_rate),
                'tenant': {
                    'id': rental.tenant.id,
                    'name': f"{rental.tenant.name} {rental.tenant.surname}",
                    'email': rental.tenant.email
                },
                'shared_users': shared_users
            })

        return serialized

    @staticmethod
    def get_rental_statistics() -> Dict[str, Any]:
        """Get statistics about rentals"""
        now = datetime.now(tz=timezone.utc)
        stats = {
            'total_active_rentals': db.session.query(RentalModel)
            .filter_by(status='active').count(),
            'total_terminated': db.session.query(RentalModel)
            .filter_by(status='terminated').count(),
            'expiring_soon': db.session.query(RentalModel)
            .filter(
                RentalModel.status == 'active',
                RentalModel.end_date <= now + timedelta(days=30)
            ).count(),
            'average_duration': db.session.query(
                db.func.avg(
                    db.func.julianday(RentalModel.end_date) -
                    db.func.julianday(RentalModel.start_date)
                )
            ).scalar() or 0
        }
        return stats

    @staticmethod
    def get_rental_statistics(user_id: int) -> Dict[str, Any]:
        """Get statistics about user's rentals"""
        try:
            # Get user's rentals as tenant
            tenant_rentals = db.session.query(
                RentalModel).filter_by(tenant_id=user_id)

            # Get user's rentals as owner
            owner_rentals = (db.session.query(RentalModel)
                             .join(UnitModel)
                             .filter(UnitModel.user_id == user_id))

            # Calculate average duration using SQLite's julianday function
            avg_duration = db.session.query(
                db.func.avg(
                    db.func.round(
                        (db.func.julianday(RentalModel.end_date) -
                         db.func.julianday(RentalModel.start_date))
                    )
                )
            ).filter(RentalModel.tenant_id == user_id).scalar()

            stats = {
                'as_tenant': {
                    'total_rentals': tenant_rentals.count(),
                    'active_rentals': tenant_rentals.filter_by(status='ACTIVE').count(),
                    'total_spent': float(
                        tenant_rentals.with_entities(
                            db.func.sum(RentalModel.total_cost)
                        ).scalar() or 0
                    ),
                    'average_duration': float(avg_duration or 0)
                },
                'as_owner': {
                    'total_rentals': owner_rentals.count(),
                    'active_rentals': owner_rentals.filter_by(status='ACTIVE').count(),
                    'total_revenue': float(
                        owner_rentals.with_entities(
                            db.func.sum(RentalModel.total_cost)
                        ).scalar() or 0
                    ),
                    'units_rented': owner_rentals.distinct(RentalModel.unit_id).count()
                }
            }

            return stats

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to get rental statistics: {str(e)}"}

    @staticmethod
    def share_rental(rental_id: int, email: str, user_id: int) -> Dict[str, Any]:
        """Share rental with another user"""
        try:
            rental = db.session.execute(
                db.select(RentalModel).filter_by(id=rental_id)
            ).scalar_one_or_none()

            if not rental:
                return {"error": "Rental not found"}

            # Verify ownership/permissions
            if str(rental.tenant_id) != str(user_id):
                return {"error": "Only the tenant can share this rental"}

            # Verify user exists
            shared_user = db.session.execute(
                db.select(UserModel).filter_by(email=email)
            ).scalar_one_or_none()

            if not shared_user:
                return {"error": "User not found"}

            if rental.add_shared_user(email):
                db.session.commit()
                return RentalService._serialize_rental(rental)
            else:
                return {"error": "User already has access"}

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to share rental: {str(e)}"}

    @staticmethod
    def unshare_rental(rental_id: int, email: str, user_id: int) -> Dict[str, Any]:
        """Remove shared access for a user"""
        try:
            rental = db.session.execute(
                db.select(RentalModel).filter_by(id=rental_id)
            ).scalar_one_or_none()

            if not rental:
                return {"error": "Rental not found"}

            if str(rental.tenant_id) != str(user_id):
                return {"error": "Only the tenant can manage sharing"}

            if rental.remove_shared_user(email):
                db.session.commit()
                return RentalService._serialize_rental(rental)
            else:
                return {"error": "User does not have access"}

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to remove shared access: {str(e)}"}

    @staticmethod
    def get_upcoming_expirations(user_id: int) -> List[Dict[str, Any]]:
        """
        Get rentals expiring in the next 30 days for a user
        Args:
            user_id: ID of the user (can be tenant or owner)
        Returns:
            List of rentals expiring soon
        """
        try:
            thirty_days_from_now = datetime.now(
                tz=timezone.utc) + timedelta(days=30)

            # Get rentals where user is tenant
            tenant_rentals = (
                db.session.query(RentalModel)
                .filter(
                    RentalModel.tenant_id == user_id,
                    RentalModel.status == 'active',
                    RentalModel.end_date <= thirty_days_from_now,
                    RentalModel.end_date >= datetime.now(tz=timezone.utc)
                )
                .all()
            )

            # Get rentals where user is owner
            owner_rentals = (
                db.session.query(RentalModel)
                .join(UnitModel)
                .filter(
                    UnitModel.user_id == user_id,
                    RentalModel.status == 'active',
                    RentalModel.end_date <= thirty_days_from_now,
                    RentalModel.end_date >= datetime.now(tz=timezone.utc)
                )
                .all()
            )

            return {
                'as_tenant': [
                    RentalService._serialize_rental(rental, user_id)
                    for rental in tenant_rentals
                ],
                'as_owner': [
                    RentalService._serialize_rental(rental, user_id)
                    for rental in owner_rentals
                ]
            }

        except Exception as e:
            return {"error": f"Failed to get upcoming expirations: {str(e)}"}

    @staticmethod
    def get_rental_history(unit_id: str, user_id: int) -> List[Dict[str, Any]]:
        """
        Get rental history for a specific unit
        Args:
            unit_id: ID of the unit
            user_id: ID of the requesting user (for authorization)
        Returns:
            List of past rentals for the unit
        """
        try:
            # First verify if user has access to this unit
            unit = db.session.query(UnitModel).filter_by(
                unit_id=unit_id).first()
            if not unit:
                return {"error": "Unit not found"}

            # Check if user is authorized (owner or current tenant)
            if str(unit.user_id) != str(user_id) and str(unit.tenant_id) != str(user_id):
                return {"error": "Unauthorized to view rental history"}

            # Get all rentals for this unit, ordered by date
            rentals = (
                db.session.query(RentalModel)
                .filter(RentalModel.unit_id == unit_id)
                .order_by(RentalModel.start_date.desc())
                .all()
            )

            return [RentalService._serialize_rental(rental, user_id) for rental in rentals]

        except Exception as e:
            return {"error": f"Failed to get rental history: {str(e)}"}
