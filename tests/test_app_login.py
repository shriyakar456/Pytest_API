import pytest
import requests
import json
import time
from app_login import reset_db

@pytest.fixture(autouse=True)
def clean_state():
    reset_db()

BASE_URL = "http://127.0.0.1:5000"

# Load users from any JSON file
def load_users(path):
    with open(path) as f:
        return json.load(f)

# ✅ Positive login test
@pytest.mark.parametrize("user", load_users("users.json"))
def test_login_positive(user):
    requests.post(f"{BASE_URL}/add_user", json=user)
    time.sleep(0.05)
    response = requests.post(f"{BASE_URL}/login", json=user)
    time.sleep(0.05)
    assert response.status_code == user["expected"], f"{user['username']} login failed"

# ❌ Negative login test
@pytest.mark.parametrize("user", load_users("users_fail.json"))
def test_login_negative(user):
    response = requests.post(f"{BASE_URL}/login", json=user)
    time.sleep(0.05)
    assert response.status_code == user["expected"], f"{user['username']} unexpectedly passed"

# ✅ Positive get_user test
@pytest.mark.parametrize("user", load_users("users.json"))
def test_get_user_positive(user):
    requests.post(f"{BASE_URL}/add_user", json=user)
    time.sleep(0.05)
    response = requests.get(f"{BASE_URL}/get_user", params={"username": user["username"]})
    time.sleep(0.05)
    assert response.status_code == 200, f"{user['username']} not found"
    assert response.json().get("username") == user["username"]

# ❌ Negative get_user test
@pytest.mark.parametrize("user", load_users("users_fail.json"))
def test_get_user_negative(user):
    response = requests.get(f"{BASE_URL}/get_user", params={"username": user["username"]})
    time.sleep(0.05)
    assert response.status_code == 404, f"{user['username']} should not exist"

# ✅ Positive delete_user test
@pytest.mark.parametrize("user", load_users("users.json"))
def test_delete_user_positive(user):
    # Step 1: Try adding user
    response = requests.post(f"{BASE_URL}/add_user", json=user)
    if response.status_code not in [200, 201, 400]:
        pytest.fail(f"Setup failed for user {user['username']}")

    time.sleep(0.05)  # allow DB write

    # Step 2: Delete user
    response = requests.delete(f"{BASE_URL}/delete_user", json={"username": user["username"]})
    assert response.status_code == 200, f"Failed to delete {user['username']}"

    time.sleep(0.05)  # allow DB write

    # Step 3: Confirm deletion
    confirm = requests.get(f"{BASE_URL}/get_user", params={"username": user["username"]})
    assert confirm.status_code == 404, f"{user['username']} still exists after deletion"


# ❌ Negative delete_user test
@pytest.mark.parametrize("user", load_users("users_fail.json"))
def test_delete_user_negative(user):
    response = requests.delete(f"{BASE_URL}/delete_user", json={"username": user["username"]})
    time.sleep(0.05)
    assert response.status_code == 404, f"{user['username']} should not be deletable"
