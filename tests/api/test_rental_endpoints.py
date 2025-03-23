import pytest
from datetime import datetime, timedelta, timezone


class TestRentalEndpoints:
    def test_create_rental(self, app, client, auth_headers, test_unit):
        """Test creating a new rental."""
        with app.app_context():
            data = {
                'unit_id': test_unit.unit_id,
                'start_date': datetime.now(timezone.utc).date().isoformat(),
                'end_date': (datetime.now(timezone.utc) + timedelta(days=90)).date().isoformat(),
                'monthly_rate': 1500.00
            }

            response = client.post(
                '/api/rentals/',
                json=data,
                headers=auth_headers
            )
            assert response.status_code == 201
            assert response.json['unit_id'] == data['unit_id']
            assert response.json['tenant_id'] == 1

    def test_create_rental_invalid_data(self, client, auth_headers, app):
        with app.app_context():
            data = {
                'unit_id': 'INVALID-UNIT',
                'start_date': 'invalid-date',
                'monthly_rate': -1500.00
            }

            response = client.post(
                '/api/rentals/',
                json=data,
                headers=auth_headers
            )
            assert response.status_code == 400

    def test_create_rental_unauthorized(self, client, app):
        with app.app_context():
            data = {
                'unit_id': 'UNIT-001',
                'start_date': '2024-03-23',
                'end_date': '2024-06-23',
                'monthly_rate': 1500.00
            }

            response = client.post(
                '/api/rentals/',
                json=data  # No auth headers
            )
            assert response.status_code == 401

    def test_extend_rental(self, client, auth_headers, test_rental):
        data = {'extension_days': 30}
        response = client.post(
            f'/api/rentals/extend/{test_rental.id}',
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert 'end_date' in response.json

    def test_get_rental_history(self, client, auth_headers, test_unit, test_rental):
        response = client.get(
            f'/api/rentals/history/{test_unit.unit_id}',
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json, list)

    def test_get_upcoming_expirations(self, client, auth_headers):
        response = client.get(
            '/api/rentals/upcoming-expiration/',  # Added trailing slash
            headers=auth_headers
        )
        assert response.status_code == 200
        assert 'as_tenant' in response.json
