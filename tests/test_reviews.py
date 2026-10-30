import pytest
from conftest import csrf_token_from


def post_review(client, product_id, content, rating="5"):
    page = client.get(f"/product/{product_id}")
    token = csrf_token_from(page.get_data(as_text=True))
    client.post(
        f"/product/{product_id}",
        data={"csrf_token": token, "content": content, "rating": rating},
    )
    return client.get(f"/product/{product_id}").get_data(as_text=True)


def submit_review(client, product_id, content, rating="5"):
    """POST a review and return (POST response, product page HTML afterwards)."""
    page = client.get(f"/product/{product_id}")
    token = csrf_token_from(page.get_data(as_text=True))
    response = client.post(
        f"/product/{product_id}",
        data={"csrf_token": token, "content": content, "rating": rating},
    )
    return response, client.get(f"/product/{product_id}").get_data(as_text=True)


def test_non_numeric_rating_is_rejected_without_error(logged_in_client, product_id):
    response, html = submit_review(logged_in_client, product_id, "Marker-abc", rating="abc")

    assert response.status_code == 302
    assert "Marker-abc" not in html


@pytest.mark.parametrize("rating", ["0", "6", "99", "-5"])
def test_out_of_range_rating_is_rejected(logged_in_client, product_id, rating):
    response, html = submit_review(logged_in_client, product_id, "Marker-range", rating=rating)

    assert response.status_code == 302
    assert "Marker-range" not in html


@pytest.mark.parametrize("content", ["", "   \n\t ", "<b></b>", "<script></script>  "])
def test_empty_content_is_rejected(logged_in_client, product_id, content):
    response, html = submit_review(logged_in_client, product_id, content)

    assert response.status_code == 302
    assert "No reviews yet." in html


def test_review_over_2000_characters_is_rejected(logged_in_client, product_id):
    response, html = submit_review(logged_in_client, product_id, "x" * 2001)

    assert response.status_code == 302
    assert "No reviews yet." in html


def test_review_of_exactly_2000_characters_is_accepted(logged_in_client, product_id):
    _, html = submit_review(logged_in_client, product_id, "y" * 2000)

    assert "y" * 2000 in html


def test_script_tag_in_review_is_neutralised(logged_in_client, product_id):
    html = post_review(logged_in_client, product_id, "<script>alert(1)</script>Nice")

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script" not in html  # tags are removed, not displayed as escaped text
    assert "&amp;lt;script" not in html  # and never double-escaped
    assert "Nice" in html


def test_plain_review_is_still_shown(logged_in_client, product_id):
    html = post_review(logged_in_client, product_id, "Great product")

    assert "Great product" in html
