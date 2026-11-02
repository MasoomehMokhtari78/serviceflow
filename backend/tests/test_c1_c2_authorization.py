import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token(email: str, password: str = "password123", slug: str = "kariz-cafe") -> dict:
    res = client.post("/api/v1/auth/login", json={
        "restaurant_slug": slug,
        "email": email,
        "password": password
    })
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ====================================================
# C1: Branch Authorization on Order Retrieval
# ====================================================

def test_c1_waiter_retrieving_order_from_own_branch():
    """Waiter retrieves an order belonging to their own branch -> 200 OK."""
    headers = get_token("waiter.enghelab@kariz.ir")

    # Get orders (automatically scoped to Enghelab branch)
    res = client.get("/api/v1/orders?active_only=false", headers=headers)
    assert res.status_code == 200
    orders = res.json()
    assert len(orders) > 0

    own_order_id = orders[0]["id"]
    get_res = client.get(f"/api/v1/orders/{own_order_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == own_order_id


def test_c1_waiter_retrieving_order_from_another_branch_same_restaurant():
    """Waiter attempts to retrieve an order from another branch of same restaurant -> fails closed (403/404)."""
    enghelab_headers = get_token("waiter.enghelab@kariz.ir")
    sanaee_headers = get_token("waiter.sanaee@kariz.ir")

    # Get Sanaee branch order
    sanaee_orders = client.get("/api/v1/orders?active_only=false", headers=sanaee_headers).json()
    assert len(sanaee_orders) > 0
    sanaee_order_id = sanaee_orders[0]["id"]

    # Enghelab waiter attempts to read Sanaee branch order
    res = client.get(f"/api/v1/orders/{sanaee_order_id}", headers=enghelab_headers)
    assert res.status_code in [403, 404]


def test_c1_waiter_retrieving_order_from_another_restaurant():
    """Waiter attempts to retrieve an order from another restaurant tenant -> 404 Not Found."""
    enghelab_headers = get_token("waiter.enghelab@kariz.ir")
    sepanj_headers = get_token("waiter@sepanj.ir", slug="sepanj-cafe")

    # Get Kariz's order
    kariz_orders = client.get("/api/v1/orders?active_only=false", headers=enghelab_headers).json()
    assert len(kariz_orders) > 0
    kariz_order_id = kariz_orders[0]["id"]

    # Sepanj waiter attempts to access Kariz order -> MUST return 404
    res_sepanj = client.get(f"/api/v1/orders/{kariz_order_id}", headers=sepanj_headers)
    assert res_sepanj.status_code == 404

    # Kariz waiter attempts to access a completely foreign order ID -> MUST return 404
    res_foreign = client.get("/api/v1/orders/00000000-0000-0000-0000-000000000001", headers=enghelab_headers)
    assert res_foreign.status_code == 404



def test_c1_manager_accessing_authorized_branch():
    """Manager accessing orders across any authorized branch within their restaurant -> 200 OK."""
    headers = get_token("manager@kariz.ir")
    res = client.get("/api/v1/orders?active_only=false", headers=headers)
    assert res.status_code == 200
    orders = res.json()
    assert len(orders) > 0

    order_id = orders[0]["id"]
    get_res = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert get_res.status_code == 200


def test_c1_manager_attempting_to_access_unauthorized_foreign_branch():
    """Manager attempting to access a branch from another restaurant -> 404 Not Found."""
    kariz_manager_headers = get_token("manager@kariz.ir")
    sepanj_manager_headers = get_token("manager@sepanj.ir", slug="sepanj-cafe")

    # Get Sepanj branch
    sepanj_branches = client.get("/api/v1/restaurants/branches", headers=sepanj_manager_headers).json()
    sepanj_branch_id = sepanj_branches[0]["id"]

    # Kariz manager attempts to query orders scoped to Sepanj branch
    res = client.get(f"/api/v1/orders?branch_id={sepanj_branch_id}", headers=kariz_manager_headers)
    assert res.status_code == 404


def test_c1_unassigned_waiter_fails_closed():
    """Waiter without branch assignment must fail closed on order retrieval -> 403 Forbidden."""
    headers = get_token("unassigned.waiter@kariz.ir")
    res = client.get("/api/v1/orders", headers=headers)
    assert res.status_code == 403
    assert "no branch assignment" in res.json()["detail"].lower()


# ====================================================
# C2: Branch and Station Authorization on Item Mutations
# ====================================================

def test_c2_kitchen_staff_updating_assigned_station_item():
    """Kitchen staff updates an item in their assigned branch and station -> 200 OK."""
    waiter_headers = get_token("waiter.enghelab@kariz.ir")
    chef_headers = get_token("chef.enghelab@kariz.ir")

    # Waiter creates order with Roast Beef (routed to Kitchen station)
    branches = client.get("/api/v1/restaurants/branches", headers=waiter_headers).json()
    b_id = branches[0]["id"]
    tables = client.get(f"/api/v1/restaurants/branches/{b_id}/tables", headers=waiter_headers).json()
    items = client.get("/api/v1/menu/items", headers=waiter_headers).json()
    roast_beef = next(i for i in items if "رست بیف" in i["name_fa"])

    order = client.post("/api/v1/orders", json={
        "branch_id": b_id,
        "table_id": tables[0]["id"],
        "items": [{"menu_item_id": roast_beef["id"], "quantity": 1}]
    }, headers=waiter_headers).json()
    item_id = order["items"][0]["id"]

    # Chef updates to PREPARING -> 200 OK
    res = client.patch(f"/api/v1/order-items/{item_id}/status", json={
        "target_status": "preparing",
        "expected_item_version": 1
    }, headers=chef_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "preparing"


def test_c2_kitchen_staff_attempting_to_update_another_station_item():
    """Kitchen staff attempts to update an item at another station in the same branch -> 403 Forbidden."""
    waiter_headers = get_token("waiter.enghelab@kariz.ir")
    chef_headers = get_token("chef.enghelab@kariz.ir")

    # Waiter creates order with Espresso (routed to Barista station)
    branches = client.get("/api/v1/restaurants/branches", headers=waiter_headers).json()
    b_id = branches[0]["id"]
    tables = client.get(f"/api/v1/restaurants/branches/{b_id}/tables", headers=waiter_headers).json()
    items = client.get("/api/v1/menu/items", headers=waiter_headers).json()
    espresso = next(i for i in items if "اسپرسو دابل" in i["name_fa"])

    order = client.post("/api/v1/orders", json={
        "branch_id": b_id,
        "table_id": tables[1]["id"],
        "items": [{"menu_item_id": espresso["id"], "quantity": 1}]
    }, headers=waiter_headers).json()
    item_id = order["items"][0]["id"]

    # Kitchen chef (assigned to Kitchen station) attempts to update Barista item -> 403 Forbidden
    res = client.patch(f"/api/v1/order-items/{item_id}/status", json={
        "target_status": "preparing",
        "expected_item_version": 1
    }, headers=chef_headers)
    assert res.status_code == 403
    assert "not authorized to update items for this kitchen station" in res.json()["detail"].lower()


def test_c2_kitchen_staff_attempting_to_update_item_in_another_branch():
    """Kitchen staff attempts to update an item in another branch -> 404 (does not leak resource)."""
    waiter_sanaee = get_token("waiter.sanaee@kariz.ir")
    chef_enghelab = get_token("chef.enghelab@kariz.ir")

    # Create order in Sanaee branch with kitchen dish
    branches = client.get("/api/v1/restaurants/branches", headers=waiter_sanaee).json()
    sanaee_branch = next(b for b in branches if "سنایی" in b["name"])
    tables = client.get(f"/api/v1/restaurants/branches/{sanaee_branch['id']}/tables", headers=waiter_sanaee).json()
    items = client.get("/api/v1/menu/items", headers=waiter_sanaee).json()
    roast_beef = next(i for i in items if "رست بیف" in i["name_fa"])

    order = client.post("/api/v1/orders", json={
        "branch_id": sanaee_branch["id"],
        "table_id": tables[0]["id"],
        "items": [{"menu_item_id": roast_beef["id"], "quantity": 1}]
    }, headers=waiter_sanaee).json()
    sanaee_item_id = order["items"][0]["id"]

    # Enghelab chef attempts to update Sanaee item -> 404 ResourceNotFound
    res = client.patch(f"/api/v1/order-items/{sanaee_item_id}/status", json={
        "target_status": "preparing",
        "expected_item_version": 1
    }, headers=chef_enghelab)
    assert res.status_code == 404


def test_c2_waiter_forbidden_from_item_mutations():
    """Waiters are strictly forbidden from kitchen item status mutations -> 403 Forbidden."""
    waiter_headers = get_token("waiter.enghelab@kariz.ir")

    # Create order
    branches = client.get("/api/v1/restaurants/branches", headers=waiter_headers).json()
    tables = client.get(f"/api/v1/restaurants/branches/{branches[0]['id']}/tables", headers=waiter_headers).json()
    items = client.get("/api/v1/menu/items", headers=waiter_headers).json()

    order = client.post("/api/v1/orders", json={
        "branch_id": branches[0]["id"],
        "table_id": tables[0]["id"],
        "items": [{"menu_item_id": items[0]["id"], "quantity": 1}]
    }, headers=waiter_headers).json()
    item_id = order["items"][0]["id"]

    # Waiter attempts to mutate item status -> 403 Forbidden
    res = client.patch(f"/api/v1/order-items/{item_id}/status", json={
        "target_status": "preparing",
        "expected_item_version": 1
    }, headers=waiter_headers)
    assert res.status_code == 403


def test_c2_manager_accessing_authorized_item():
    """Managers have authority across all stations in their authorized branches -> 200 OK."""
    waiter_headers = get_token("waiter.enghelab@kariz.ir")
    manager_headers = get_token("manager@kariz.ir")

    branches = client.get("/api/v1/restaurants/branches", headers=waiter_headers).json()
    tables = client.get(f"/api/v1/restaurants/branches/{branches[0]['id']}/tables", headers=waiter_headers).json()
    items = client.get("/api/v1/menu/items", headers=waiter_headers).json()

    order = client.post("/api/v1/orders", json={
        "branch_id": branches[0]["id"],
        "table_id": tables[0]["id"],
        "items": [{"menu_item_id": items[0]["id"], "quantity": 1}]
    }, headers=waiter_headers).json()
    item_id = order["items"][0]["id"]

    # Manager updates item -> 200 OK
    res = client.patch(f"/api/v1/order-items/{item_id}/status", json={
        "target_status": "preparing",
        "expected_item_version": 1
    }, headers=manager_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "preparing"


def test_c2_unassigned_kitchen_staff_fails_closed():
    """Kitchen staff without station assignment fails closed on item mutation -> 403 Forbidden."""
    waiter_headers = get_token("waiter.enghelab@kariz.ir")
    unassigned_headers = get_token("unassigned.kitchen@kariz.ir")

    branches = client.get("/api/v1/restaurants/branches", headers=waiter_headers).json()
    tables = client.get(f"/api/v1/restaurants/branches/{branches[0]['id']}/tables", headers=waiter_headers).json()
    items = client.get("/api/v1/menu/items", headers=waiter_headers).json()

    order = client.post("/api/v1/orders", json={
        "branch_id": branches[0]["id"],
        "table_id": tables[0]["id"],
        "items": [{"menu_item_id": items[0]["id"], "quantity": 1}]
    }, headers=waiter_headers).json()
    item_id = order["items"][0]["id"]

    res = client.patch(f"/api/v1/order-items/{item_id}/status", json={
        "target_status": "preparing",
        "expected_item_version": 1
    }, headers=unassigned_headers)
    assert res.status_code == 403
    assert "no station assignment" in res.json()["detail"].lower()
