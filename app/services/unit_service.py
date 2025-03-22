from typing import List, Dict, Any, Optional

from flask import json
from app.models.base import db
from app.models.rental import RentalModel
from app.models.unit import UnitModel
from app.models.enums import UnitStatus
from app.models.securityFeature import SecurityFeatureModel, SecurityFeatureType
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.models.user import UserModel
from app.schemas.unit import UnitCreateSchema, UnitUpdateSchema, UnitResponseSchema
from urllib.parse import urlparse
import re


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
        """Get all available units (public view)"""
        units = db.session.execute(
            db.select(UnitModel).filter_by(status=UnitStatus.VACANT)
        ).scalars().all()
        # No user_id for public view
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
            'owned_units': [UnitService._serialize_unit(unit, user_id) for unit in owned_units],
            'rented_units': [UnitService._serialize_unit(unit, user_id) for unit in rented_units]
        }

    @staticmethod
    def create_unit(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new storage unit with security features"""
        try:
            # Validate data first
            is_valid, error_message = UnitService._validate_unit_data(data)
            if not is_valid:
                return {"error": error_message}

            # Generate unit ID
            unit_count = db.session.query(UnitModel).count()
            unit_id = f"UNIT-{unit_count + 1:03d}"

            # Create unit with all fields from schema
            new_unit = UnitModel(
                unit_id=unit_id,
                unit_name=data['unit_name'],
                country=data['country'],
                city=data['city'],
                address_link=data['address_link'],
                status=data['status'],
                size_sqm=data['size_sqm'],
                monthly_rate=data['monthly_rate'],
                currency=data.get('currency', 'ZAR'),
                climate_controlled=data.get('climate_controlled', False),
                floor_level=data['floor_level'],
                rental_duration_days=data['rental_duration_days'],
                user_id=data['user_id'],
                tenant_id=data.get('tenant_id'),
                shared_user_emails=data.get('shared_user_emails', [])
            )

            # Add security features if provided
            if 'security_features' in data:
                features = []
                for feature_type in data['security_features']:
                    feature = SecurityFeatureModel(
                        unit_id=unit_id,
                        feature_type=SecurityFeatureType[feature_type],
                        notes=f"Added during unit creation"
                    )
                    features.append(feature)
                new_unit.security_features = features

            # Calculate rate with security premium
            base_rate = float(new_unit.monthly_rate)
            premium = new_unit.calculate_security_premium()
            new_unit.monthly_rate = round(base_rate * (1 + premium), 2)

            db.session.add(new_unit)
            db.session.commit()

            return UnitService._serialize_unit(new_unit)

        except IntegrityError as e:
            db.session.rollback()
            return {"error": f"Database integrity error: {str(e)}"}
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to create unit: {str(e)}"}

    @staticmethod
    def update_unit(unit_id: str, data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Update an existing storage unit with ownership check"""
        try:
            unit = db.session.execute(
                db.select(UnitModel).filter_by(unit_id=unit_id)
            ).scalar_one_or_none()

            if not unit:
                return {"error": "Unit not found"}

            # Check ownership
            if unit.user_id != user_id:
                return {"error": "Unauthorized - not the owner"}

            # Update allowed fields from schema
            allowed_fields = [
                'unit_name', 'status', 'monthly_rate', 'currency',
                'climate_controlled', 'floor_level', 'rental_duration_days',
                'tenant_id', 'shared_user_emails'
            ]

            for field in allowed_fields:
                if field in data:
                    setattr(unit, field, data[field])

            # Handle security features update
            if 'security_features' in data:
                # Clear existing features
                unit.security_features = []

                # Add new features
                for feature_type in data['security_features']:
                    feature = SecurityFeatureModel(
                        unit_id=unit_id,
                        feature_type=SecurityFeatureType[feature_type],
                        notes=f"Updated on {datetime.utcnow().isoformat()}"
                    )
                    unit.security_features.append(feature)

                # Recalculate rate with new security premium
                base_rate = float(unit.monthly_rate)
                premium = unit.calculate_security_premium()
                unit.monthly_rate = round(base_rate * (1 + premium), 2)

            unit.updated_at = datetime.utcnow()
            db.session.commit()

            return UnitService._serialize_unit(unit)

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to update unit: {str(e)}"}

    @staticmethod
    def delete_unit(unit_id: str, user_id: int) -> Dict[str, Any]:
        """Delete a storage unit"""
        try:
            unit = db.session.execute(
                db.select(UnitModel).filter_by(unit_id=unit_id)
            ).scalar_one_or_none()

            if not unit:
                return {"error": "Unit not found"}

            # Check ownership
            if unit.user_id != user_id:
                return {"error": "Unauthorized - not the owner"}

            # Check if unit can be deleted
            if unit.status != UnitStatus.VACANT:
                return {"error": "Cannot delete occupied or reserved unit"}

            db.session.delete(unit)
            db.session.commit()

            return {"message": "Unit deleted successfully"}
        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to delete unit: {str(e)}"}

    @staticmethod
    def get_unit_by_id(unit_id: str, current_user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get a single unit by ID"""
        unit = db.session.execute(
            db.select(UnitModel).filter_by(unit_id=unit_id)
        ).scalar_one_or_none()

        if not unit:
            return None

        return UnitService._serialize_unit(unit, current_user_id)

    @staticmethod
    def search_units(
        city: str = None,
        min_size: float = None,
        max_size: float = None,
        min_price: float = None,
        max_price: float = None,
        features: List[str] = None,
        floor_level: str = None,
        status: str = None,
    ) -> List[Dict[str, Any]]:
        """Search units with filters"""
        query = db.select(UnitModel)

        if city:
            query = query.filter(UnitModel.city.like(f"%{city}%"))
        if min_size:
            query = query.filter(UnitModel.size_sqm >= min_size)
        if max_size:
            query = query.filter(UnitModel.size_sqm <= max_size)
        if min_price:
            query = query.filter(UnitModel.monthly_rate >= min_price)
        if max_price:
            query = query.filter(UnitModel.monthly_rate <= max_price)
        if floor_level:
            query = query.filter(
                UnitModel.floor_level.like(f"%{floor_level}%"))
        if status:
            query = query.filter(UnitModel.status.like(f"%{status}%"))
        if features:
            for feature in features:
                query = query.join(SecurityFeatureModel).filter(
                    SecurityFeatureModel.feature_type == SecurityFeatureType[feature]
                )

        units = db.session.execute(query).scalars().all()
        return [UnitService._serialize_unit(unit) for unit in units]

    @staticmethod
    def get_unit_statistics() -> Dict[str, Any]:
        """Get statistics about units"""
        stats = {
            'total_units': db.session.query(UnitModel).count(),
            'vacant_units': db.session.query(UnitModel)
            .filter_by(status=UnitStatus.VACANT).count(),
            'occupied_units': db.session.query(UnitModel)
            .filter_by(status=UnitStatus.OCCUPIED).count(),
            'average_rate': float(
                db.session.query(db.func.avg(UnitModel.monthly_rate))
                .scalar() or 0
            ),
            'total_area': float(
                db.session.query(db.func.sum(UnitModel.size_sqm))
                .scalar() or 0
            ),
            'cities': [
                city[0] for city in db.session.query(UnitModel.city)
                .distinct()
                .order_by(UnitModel.city)
                .all()
            ]
        }

        # Add more detailed statistics
        stats.update({
            'average_size': float(
                db.session.query(db.func.avg(UnitModel.size_sqm))
                .scalar() or 0
            ),
            'occupancy_rate': round(
                (stats['occupied_units'] / stats['total_units'] * 100)
                if stats['total_units'] > 0 else 0,
                2
            ),
            'total_revenue': float(
                db.session.query(db.func.sum(UnitModel.monthly_rate))
                .filter_by(status=UnitStatus.OCCUPIED)
                .scalar() or 0
            )
        })

        return stats

    @staticmethod
    def _serialize_unit(unit: UnitModel, current_user_id: Optional[int] = None) -> Dict[str, Any]:
        """Convert unit model to dictionary with privacy controls"""
        # Base serialization
        serialized = {
            'unit_id': unit.unit_id,
            'unit_name': unit.unit_name,
            'country': unit.country,
            'city': unit.city,
            'address_link': unit.address_link,
            'status': unit.status.value,
            'size_sqm': unit.size_sqm,
            'monthly_rate': float(unit.monthly_rate),
            'currency': unit.currency,
            'climate_controlled': unit.climate_controlled,
            'floor_level': unit.floor_level,
            'rental_duration_days': unit.rental_duration_days,
            'created_at': unit.created_at.isoformat() if unit.created_at else None,
            'updated_at': unit.updated_at.isoformat() if unit.updated_at else None,
            'security_features': [
                {
                    'type': feature.feature_type.value,
                    'notes': feature.notes
                } for feature in unit.security_features
            ]
        }

        # Add owner info
        if unit.owner:
            serialized['owner'] = {
                'id': unit.owner.id,
                'name': unit.owner.name,
                'email': unit.owner.email
            }

        # Get active rental for this unit and its shared users
        active_rental = db.session.query(RentalModel).filter(
            RentalModel.unit_id == unit.unit_id,
            RentalModel.status == 'active'
        ).first()

        # Check if current user is authorized (owner, tenant, or shared user)
        is_authorized = False
        if current_user_id:
            is_authorized = (
                str(current_user_id) == str(unit.user_id) or  # Is owner
                str(current_user_id) == str(unit.tenant_id)    # Is tenant
            )

            # Check if user is in shared_user_emails
            if active_rental and not is_authorized:
                shared_users = json.loads(
                    active_rental.shared_user_emails or '[]')
                user = db.session.query(UserModel).get(current_user_id)
                is_authorized = user and user.email in shared_users

        if is_authorized:
            if unit.tenant:
                serialized['tenant'] = {
                    'id': unit.tenant.id,
                    'name': unit.tenant.name,
                    'email': unit.tenant.email
                }
                serialized['tenant_id'] = unit.tenant_id

                if active_rental:
                    serialized['shared_user_emails'] = json.loads(
                        active_rental.shared_user_emails or '[]'
                    )
        else:
            # For public view, just show if unit is occupied
            serialized['is_occupied'] = bool(unit.tenant_id)

        return serialized

    @staticmethod
    def _validate_unit_data(data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate unit data before creation/update"""
        # Required fields check
        required_fields = ['unit_name', 'city', 'country', 'address_link',
                           'size_sqm', 'monthly_rate', 'floor_level',
                           'rental_duration_days', 'status']

        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"

        # Check for existing unit with same location and name first
        existing_unit = db.session.execute(
            db.select(UnitModel)
            .filter(
                db.func.lower(
                    UnitModel.unit_name) == data['unit_name'].lower(),
                db.func.lower(UnitModel.city) == data['city'].lower()
            )
        ).scalar_one_or_none()

        if existing_unit:
            return False, f"Unit with name '{data['unit_name']}' already exists in {data['city']}"

        # Case-insensitive status validation
        try:
            valid_statuses = [status.name.lower() for status in UnitStatus]
            if data['status'].lower() not in valid_statuses:
                return False, f"Invalid status. Must be one of: {', '.join(status.name for status in UnitStatus)}"
            # Convert to uppercase for storage
            data['status'] = data['status'].upper()
        except AttributeError:
            return False, "Status must be a string"

        # Numeric validations
        if data.get('size_sqm', 0) <= 0:
            return False, "Size must be greater than 0"
        if data.get('monthly_rate', 0) <= 0:
            return False, "Monthly rate must be greater than 0"
        if data.get('rental_duration_days', 0) < 30:
            return False, "Minimum rental duration is 30 days"

        # Address link validation
        if 'address_link' in data:
            url = data['address_link']
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    return False, "Invalid URL format"
                if not (parsed.netloc == 'maps.google.com' or
                        parsed.netloc == 'www.google.com/maps'):
                    return False, "Address link must be a Google Maps URL"
                if not parsed.query or 'q=' not in parsed.query:
                    return False, "Invalid Google Maps link format"
                if re.search(r'[<>"\']', url):
                    return False, "Address link contains invalid characters"
            except Exception:
                return False, "Invalid address link format"

        # Security features validation
        if 'security_features' in data:
            try:
                for feature in data['security_features']:
                    SecurityFeatureType[feature]
            except KeyError:
                return False, f"Invalid security feature: {feature}"

        return True, ""

    @staticmethod
    def add_security_features(unit_id: str, features: List[str], user_id: int) -> Dict[str, Any]:
        """
        Add security features to a unit
        Args:
            unit_id: ID of the unit to update
            features: List of security feature types to add
            user_id: ID of the user making the request
        Returns:
            Dict with updated unit data or error message
        """
        try:
            # Get unit and verify ownership
            unit = db.session.execute(
                db.select(UnitModel).filter_by(unit_id=unit_id)
            ).scalar_one_or_none()

            if not unit:
                return {"error": "Unit not found"}

            if unit.user_id != user_id:
                return {"error": "Unauthorized - not the owner"}

            # Get existing features
            existing_features = {
                feature.feature_type.name for feature in unit.security_features}

            # Validate and check for duplicates
            new_features = []
            for feature in features:
                try:
                    feature_upper = feature.upper()
                    # Validate feature type
                    SecurityFeatureType[feature_upper]

                    # Check if feature already exists
                    if feature_upper in existing_features:
                        return {"error": f"Security feature '{feature}' already exists for this unit"}

                    new_features.append(feature_upper)
                except KeyError:
                    return {"error": f"Invalid security feature: {feature}"}

            # Add new features
            for feature_type in new_features:
                feature = SecurityFeatureModel(
                    unit_id=unit_id,
                    feature_type=SecurityFeatureType[feature_type],
                    notes=f"Added on {datetime.utcnow().isoformat()}"
                )
                unit.security_features.append(feature)

            # Recalculate monthly rate with new security premium
            base_rate = float(unit.monthly_rate) / \
                (1 + unit.calculate_security_premium())
            new_premium = unit.calculate_security_premium()
            unit.monthly_rate = round(base_rate * (1 + new_premium), 2)

            unit.updated_at = datetime.utcnow()
            db.session.commit()

            return UnitService._serialize_unit(unit)

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to add security features: {str(e)}"}

    @staticmethod
    def remove_security_features(unit_id: str, features: List[str], user_id: int) -> Dict[str, Any]:
        """
        Remove security features from a unit
        Args:
            unit_id: ID of the unit to update
            features: List of security feature types to remove
            user_id: ID of the user making the request
        Returns:
            Dict with updated unit data or error message
        """
        try:
            # Get unit and verify ownership
            unit = db.session.execute(
                db.select(UnitModel).filter_by(unit_id=unit_id)
            ).scalar_one_or_none()

            if not unit:
                return {"error": "Unit not found"}

            if int(unit.user_id) != user_id:
                return {"error": "Unauthorized - not the owner"}

            # Get existing features
            existing_features = {
                feature.feature_type.name: feature
                for feature in unit.security_features
            }

            # Validate features to remove
            features_to_remove = []
            for feature in features:
                try:
                    feature_upper = feature.upper()
                    # Validate feature type
                    SecurityFeatureType[feature_upper]

                    # Check if feature exists
                    if feature_upper not in existing_features:
                        return {"error": f"Security feature '{feature}' does not exist on this unit"}

                    if feature_upper == 'BASIC':
                        return {"error": "Cannot remove BASIC security feature"}

                    features_to_remove.append(existing_features[feature_upper])
                except KeyError:
                    return {"error": f"Invalid security feature: {feature}"}

            # Remove features
            for feature in features_to_remove:
                db.session.delete(feature)
                unit.security_features.remove(feature)

            # Recalculate monthly rate with new security premium
            base_rate = float(unit.monthly_rate) / \
                (1 + unit.calculate_security_premium())
            new_premium = unit.calculate_security_premium()
            unit.monthly_rate = round(base_rate * (1 + new_premium), 2)

            unit.updated_at = datetime.utcnow()
            db.session.commit()

            return UnitService._serialize_unit(unit)

        except Exception as e:
            db.session.rollback()
            return {"error": f"Failed to remove security features: {str(e)}"}
