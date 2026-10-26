import importlib
import os
import re
import sys
import uuid

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def shop_app(tmp_path_factory):
    """Import app.py once, against a throwaway database in a temp directory."""
    work_dir = tmp_path_factory.mktemp("shop")
    patch = pytest.MonkeyPatch()
    patch.syspath_prepend(ROOT)
    patch.setenv("SECRET_KEY", "test-only-key-not-a-real-secret")
    patch.setenv("FLASK_ENV", "development")  # Secure cookie flag off for http test client
    patch.chdir(work_dir)  # Database() uses a relative 'database.db'
    sys.modules.pop("app", None)
    module = importlib.import_module("app")
    module.app.config["TESTING"] = True
    yield module
    patch.undo()
    sys.modules.pop("app", None)


def make_user(shop_app, name, role):
    shop_app.db.add_user(name, "pw-for-tests", f"{name}@example.com", role)
    return shop_app.db.get_user_by_email(f"{name}@example.com")["id"]


@pytest.fixture
def product_id(shop_app):
    seller_id = make_user(shop_app, f"seller{uuid.uuid4().hex[:8]}", "seller")
    return shop_app.db.add_product_with_seller("Widget", 9.99, "A widget", seller_id, 5)


@pytest.fixture
def logged_in_client(shop_app):
    user_id = make_user(shop_app, f"reviewer{uuid.uuid4().hex[:8]}", "user")
    client = shop_app.app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["role"] = "user"
    return client


def csrf_token_from(html):
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
