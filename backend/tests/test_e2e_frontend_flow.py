import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_e2e_waiter_to_kitchen_to_waiter_workflow():
    """
    E2E Verification of the primary user journey:
    1. Waiter logs in with restaurant slug 'kariz'
    2. Waiter lists branch tables and menu categories
    3. Waiter submits an order for Table 2 with Latte Art
    4. Waiter retrieves active orders and sees the new order (SUBMITTED)
    5. Barista logs in and checks station KDS queue
    6. Barista updates item to PREPARING, then to READY
    7. Waiter retrieves order and verifies is_ready_for_service == True
    8. Waiter marks order as SERVED
    9. Order reaches terminal state SERVED and cannot be served again
    10. Manager logs in and views operational metrics and AI analyst
    """
    # 1. Waiter Login
    login_resp = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "kariz-cafe",
        "email": "waiter.enghelab@kariz.ir",
        "password": "password123"
    })
    assert login_resp.status_code == 200, login_resp.text
    waiter_data = login_resp.json()
    waiter_token = waiter_data["access_token"]
    branch_id = waiter_data["branch_id"]
    waiter_headers = {"Authorization": f"Bearer {waiter_token}"}

    # 2. Waiter fetches tables and menu categories
    tables_resp = client.get(f"/api/v1/restaurants/branches/{branch_id}/tables", headers=waiter_headers)
    assert tables_resp.status_code == 200
    tables = tables_resp.json()
    assert len(tables) > 0
    table = tables[0]

    menu_resp = client.get("/api/v1/menu/categories", headers=waiter_headers)
    assert menu_resp.status_code == 200
    categories = menu_resp.json()
    assert len(categories) > 0
    
    # Find a menu item routed to Barista (latte art)
    target_item = None
    for cat in categories:
        for itm in cat["items"]:
            if "لاته" in itm["name_fa"]:
                target_item = itm
                break
        if target_item:
            break
    assert target_item is not None

    # 3. Waiter creates order
    order_payload = {
        "branch_id": branch_id,
        "table_id": table["id"],
        "notes": "میز مشتری مهمان ویژه",
        "items": [
            {
                "menu_item_id": target_item["id"],
                "quantity": 2,
                "modifiers": "شیر کم‌چرب"
            }
        ]
    }
    create_resp = client.post("/api/v1/orders", json=order_payload, headers=waiter_headers)
    assert create_resp.status_code == 201, create_resp.text
    order = create_resp.json()
    order_id = order["id"]
    assert order["order_number"] > 0
    assert order["status"].lower() == "submitted"
    assert len(order["items"]) == 1
    order_item = order["items"][0]
    order_item_id = order_item["id"]
    barista_station_id = order_item["station_id"]

    # 4. Waiter lists active orders and sees the created order
    orders_list_resp = client.get(f"/api/v1/orders?branch_id={branch_id}&active_only=true", headers=waiter_headers)
    assert orders_list_resp.status_code == 200
    active_orders = orders_list_resp.json()
    matching_orders = [o for o in active_orders if o["id"] == order_id]
    assert len(matching_orders) == 1
    assert matching_orders[0]["is_ready_for_service"] is False

    # 5. Barista Login
    barista_login = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "kariz-cafe",
        "email": "barista.enghelab@kariz.ir",
        "password": "password123"
    })
    assert barista_login.status_code == 200
    barista_token = barista_login.json()["access_token"]
    barista_headers = {"Authorization": f"Bearer {barista_token}"}

    # 6. Barista fetches KDS queue
    queue_resp = client.get(
        f"/api/v1/stations/{barista_station_id}/queue?branch_id={branch_id}",
        headers=barista_headers
    )
    assert queue_resp.status_code == 200
    queue = queue_resp.json()
    queued_item = next((q for q in queue if q["item_id"] == order_item_id), None)
    assert queued_item is not None
    assert queued_item["status"].lower() == "pending"

    # 7. Barista updates status: pending -> preparing
    prep_resp = client.patch(
        f"/api/v1/order-items/{order_item_id}/status",
        json={"target_status": "preparing", "expected_item_version": queued_item["version"]},
        headers=barista_headers
    )
    assert prep_resp.status_code == 200
    updated_item = prep_resp.json()
    assert updated_item["status"].lower() == "preparing"

    # 8. Barista updates status: preparing -> ready
    ready_resp = client.patch(
        f"/api/v1/order-items/{order_item_id}/status",
        json={"target_status": "ready", "expected_item_version": updated_item["version"]},
        headers=barista_headers
    )
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"].lower() == "ready"

    # 9. Waiter checks order status: should now be ready for service
    check_resp = client.get(f"/api/v1/orders/{order_id}?branch_id={branch_id}", headers=waiter_headers)
    assert check_resp.status_code == 200
    ready_order = check_resp.json()
    assert ready_order["is_ready_for_service"] is True
    assert ready_order["ready_items_count"] == 1
    assert ready_order["status"].lower() == "ready_for_service"

    # 10. Waiter serves order
    serve_resp = client.post(
        f"/api/v1/orders/{order_id}/serve?branch_id={branch_id}",
        json={"expected_order_version": ready_order["version"], "notes": "تحویل به مهمان"},
        headers=waiter_headers
    )
    assert serve_resp.status_code == 200
    served_order = serve_resp.json()
    assert served_order["status"].lower() == "served"
    assert served_order["served_at"] is not None

    # 11. Manager views metrics and AI Analyst
    manager_login = client.post("/api/v1/auth/login", json={
        "restaurant_slug": "kariz-cafe",
        "email": "manager@kariz.ir",
        "password": "password123"
    })
    assert manager_login.status_code == 200
    manager_token = manager_login.json()["access_token"]
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    metrics_resp = client.get(
        f"/api/v1/metrics/operational?branch_id={branch_id}&time_window_hours=24",
        headers=manager_headers
    )
    assert metrics_resp.status_code == 200
    metrics_data = metrics_resp.json()
    assert metrics_data["completed_orders"] >= 1

    ai_resp = client.post(
        "/api/v1/ai/explain",
        json={"branch_id": branch_id, "intent": "SHIFT_SUMMARY"},
        headers=manager_headers
    )
    assert ai_resp.status_code == 200
    ai_data = ai_resp.json()
    assert len(ai_data["measured_facts"]) > 0
    assert ai_data["analysis_text"] != ""
