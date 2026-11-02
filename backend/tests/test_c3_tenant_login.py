import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import decode_access_token

client = TestClient(app)


def test_tenant_aware_login_same_email_different_passwords():
    """
    C3: Two restaurants have users with the identical email address but different passwords.
    Verify that each can authenticate only within its own restaurant context.
    """
    # 1. Login to Kariz Café using Kariz password -> SUCCESS
    res_kariz = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "kariz-cafe",
        "email": "duplicate@cafegroup.ir",
        "password": "kariz_pass_123"
    })
    assert res_kariz.status_code == 200
    data_kariz = res_kariz.json()
    assert "access_token" in data_kariz
    payload_kariz = decode_access_token(data_kariz["access_token"])
    kariz_tenant_id = payload_kariz["restaurant_id"]

    # 2. Login to Sepanj Café using Sepanj password -> SUCCESS
    res_sepanj = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "sepanj-cafe",
        "email": "duplicate@cafegroup.ir",
        "password": "sepanj_pass_456"
    })
    assert res_sepanj.status_code == 200
    data_sepanj = res_sepanj.json()
    assert "access_token" in data_sepanj
    payload_sepanj = decode_access_token(data_sepanj["access_token"])
    sepanj_tenant_id = payload_sepanj["restaurant_id"]

    # Verify distinct tenants
    assert kariz_tenant_id != sepanj_tenant_id

    # 3. Cross-attempt: Kariz password on Sepanj tenant -> MUST FAIL (401)
    res_cross1 = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "sepanj-cafe",
        "email": "duplicate@cafegroup.ir",
        "password": "kariz_pass_123"
    })
    assert res_cross1.status_code == 401

    # 4. Cross-attempt: Sepanj password on Kariz tenant -> MUST FAIL (401)
    res_cross2 = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "kariz-cafe",
        "email": "duplicate@cafegroup.ir",
        "password": "sepanj_pass_456"
    })
    assert res_cross2.status_code == 401


def test_login_invalid_restaurant_slug():
    """C3: Login with non-existent restaurant slug fails with 401 without leaking tenant existence."""
    res = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "nonexistent-cafe-group",
        "email": "manager@kariz.ir",
        "password": "password123"
    })
    assert res.status_code == 401
    assert "Invalid restaurant identifier" in res.json()["detail"]


def test_login_wrong_password():
    """C3: Valid tenant and email with incorrect password fails with 401."""
    res = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "kariz-cafe",
        "email": "manager@kariz.ir",
        "password": "completely_wrong_pass"
    })
    assert res.status_code == 401


def test_login_inactive_user_rejected():
    """C3: Inactive users cannot authenticate and receive 401."""
    res = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "kariz-cafe",
        "email": "inactive@kariz.ir",
        "password": "password123"
    })
    assert res.status_code == 401
    assert "inactive" in res.json()["detail"].lower()



def test_subsequent_request_preserves_tenant_boundary():
    """C3: Token generated for Kariz cannot access Sepanj resources."""
    res_kariz = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "kariz-cafe",
        "email": "manager@kariz.ir",
        "password": "password123"
    })
    token = res_kariz.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch branches of Sepanj through Sepanj manager to get a foreign branch ID
    res_sepanj = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "sepanj-cafe",
        "email": "manager@sepanj.ir",
        "password": "password123"
    })
    sepanj_headers = {"Authorization": f"Bearer {res_sepanj.json()['access_token']}"}
    sepanj_branches = client.get("/api/v1/restaurants/branches", headers=sepanj_headers).json()
    sepanj_branch_id = sepanj_branches[0]["id"]

    # Kariz manager attempts to access Sepanj branch tables -> 404 ResourceNotFound
    cross_res = client.get(f"/api/v1/restaurants/branches/{sepanj_branch_id}/tables", headers=headers)
    assert cross_res.status_code == 404
