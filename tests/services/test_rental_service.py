import pytest
from datetime import datetime, timedelta, timezone
from app.services.rental_service import RentalService
from app.models.rental import RentalModel


class TestRentalService:
    def test_create_rental(self, app, test_user, test_unit):
        data = {
            'unit_id': test_unit.unit_id,
            'tenant_id': test_user.id,
            'start_date': datetime.now(timezone.utc),
            'end_date': datetime.now(timezone.utc) + timedelta(days=90),
            'monthly_rate': 1500.00
        }

        result = RentalService.create_rental(data)
        assert 'error' not in result
        assert result['unit_id'] == data['unit_id']
        assert result['status'] == 'active'

    def test_get_rental_by_id(self, app, test_rental, test_user):
        result = RentalService.get_rental_by_id(test_rental.id, test_user.id)
        assert result is not None
        assert result['id'] == test_rental.id
        assert result['unit_id'] == test_rental.unit_id

    def test_update_rental(self, app, test_rental, test_user):
        update_data = {'status': 'terminated'}
        result = RentalService.update_rental(
            test_rental.id, update_data, test_user.id)
        assert 'error' not in result
        assert result['status'] == 'terminated'

    def test_get_upcoming_expirations(self, app, test_rental, test_user):
        result = RentalService.get_upcoming_expirations(test_user.id)
        assert 'as_tenant' in result
        assert 'as_owner' in result

    def test_rental_statistics(self, app, test_rental, test_user):
        stats = RentalService.get_rental_statistics(test_user.id)
        assert 'as_tenant' in stats
        assert 'as_owner' in stats
        assert stats['as_tenant']['total_rentals'] > 0
