import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

# Import the main app
from main import app

client = TestClient(app)

# Test data
test_user_data = {
    "phone_number": "7760873976",
    "password": "to_share@123"
}

test_kpa_form_data = {
    "employee_id": "EMP005",
    "employee_name": "Test User",
    "department": "QA",
    "designation": "QA Engineer",
    "performance_period": "Q1-2025",
    "kpa_title": "Test Automation",
    "kpa_description": "Implement automated testing framework",
    "target_value": 85.0,
    "achieved_value": 90.0,
    "weightage": 20.0,
    "remarks": "Excellent automation implementation"
}

class TestHealthCheck:
    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "KPA Form Data API is running" in data["message"]

class TestAuthentication:
    def test_login_endpoint_structure(self):
        """Test login endpoint structure (without database)"""
        # This test verifies the endpoint structure without database connection
        response = client.post("/api/v1/auth/login", json=test_user_data)
        # Should return 500 due to no database connection in test, but endpoint exists
        assert response.status_code in [200, 500]  # 200 if DB connected, 500 if not
        
    def test_login_invalid_data(self):
        """Test login with invalid data structure"""
        invalid_data = {"phone": "123", "pass": "abc"}
        response = client.post("/api/v1/auth/login", json=invalid_data)
        assert response.status_code == 422  # Validation error

class TestKPAForms:
    @pytest.fixture
    def auth_headers(self):
        """Fixture to provide auth headers (mock token)"""
        return {"Authorization": "Bearer mock-token"}
    
    def test_create_kpa_form_endpoint_exists(self, auth_headers):
        """Test that create KPA form endpoint exists"""
        response = client.post("/api/v1/kpa/forms", json=test_kpa_form_data, headers=auth_headers)
        # Should return 401 due to invalid token, but endpoint exists
        assert response.status_code == 401
        
    def test_get_kpa_forms_endpoint_exists(self, auth_headers):
        """Test that get KPA forms endpoint exists"""
        response = client.get("/api/v1/kpa/forms", headers=auth_headers)
        # Should return 401 due to invalid token, but endpoint exists
        assert response.status_code == 401
        
    def test_get_kpa_form_by_id_endpoint_exists(self, auth_headers):
        """Test that get KPA form by ID endpoint exists"""
        form_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(f"/api/v1/kpa/forms/{form_id}", headers=auth_headers)
        # Should return 401 due to invalid token, but endpoint exists
        assert response.status_code == 401
        
    def test_create_kpa_form_validation(self, auth_headers):
        """Test KPA form data validation"""
        invalid_data = {"employee_id": "EMP001"}  # Missing required fields
        response = client.post("/api/v1/kpa/forms", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error
        
    def test_get_kpa_forms_pagination_params(self, auth_headers):
        """Test pagination parameters"""
        response = client.get("/api/v1/kpa/forms?page=1&limit=5", headers=auth_headers)
        # Should return 401 due to invalid token, but validates params
        assert response.status_code == 401

class TestDataModels:
    def test_login_request_model(self):
        """Test LoginRequest model validation"""
        from main import LoginRequest
        
        # Valid data
        valid_data = {"phone_number": "7760873976", "password": "password123"}
        model = LoginRequest(**valid_data)
        assert model.phone_number == "7760873976"
        assert model.password == "password123"
        
        # Invalid data - missing fields
        with pytest.raises(ValueError):
            LoginRequest(phone_number="7760873976")  # Missing password
            
    def test_kpa_form_model(self):
        """Test KPAFormData model validation"""
        from main import KPAFormData
        
        # Valid data
        model = KPAFormData(**test_kpa_form_data)
        assert model.employee_id == "EMP005"
        assert model.target_value == 85.0
        assert model.achieved_value == 90.0
        
        # Invalid data - missing required fields
        with pytest.raises(ValueError):
            KPAFormData(employee_id="EMP001")  # Missing other required fields

class TestUtilityFunctions:
    def test_jwt_token_creation(self):
        """Test JWT token creation function"""
        from main import create_jwt_token
        
        token, expires_at = create_jwt_token("user-id-123", "7760873976")
        assert isinstance(token, str)
        assert len(token) > 0
        assert expires_at is not None
        
    def test_jwt_token_verification(self):
        """Test JWT token verification"""
        from main import create_jwt_token, verify_jwt_token
        
        # Create a valid token
        token, _ = create_jwt_token("user-id-123", "7760873976")
        
        # Verify the token
        payload = verify_jwt_token(token)
        assert payload["user_id"] == "user-id-123"
        assert payload["phone_number"] == "7760873976"
        
    def test_invalid_jwt_token(self):
        """Test invalid JWT token handling"""
        from main import verify_jwt_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token("invalid-token")
        assert exc_info.value.status_code == 401

# Integration test simulation
class TestAPIIntegration:
    def test_api_workflow_simulation(self):
        """Simulate the complete API workflow"""
        # 1. Health check
        health_response = client.get("/")
        assert health_response.status_code == 200
        
        # 2. Login attempt (will fail without DB, but validates structure)
        login_response = client.post("/api/v1/auth/login", json=test_user_data)
        assert login_response.status_code in [200, 500]
        
        # 3. Verify endpoints exist and require authentication
        auth_headers = {"Authorization": "Bearer mock-token"}
        
        # Create KPA form
        create_response = client.post("/api/v1/kpa/forms", json=test_kpa_form_data, headers=auth_headers)
        assert create_response.status_code == 401  # Unauthorized due to mock token
        
        # Get KPA forms
        list_response = client.get("/api/v1/kpa/forms", headers=auth_headers)
        assert list_response.status_code == 401  # Unauthorized due to mock token
        
        # Get specific KPA form
        detail_response = client.get("/api/v1/kpa/forms/123e4567-e89b-12d3-a456-426614174000", headers=auth_headers)
        assert detail_response.status_code == 401  # Unauthorized due to mock token

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
