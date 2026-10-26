from conftest import csrf_token_from


def post_review(client, product_id, content, rating="5"):
    page = client.get(f"/product/{product_id}")
    token = csrf_token_from(page.get_data(as_text=True))
    client.post(
        f"/product/{product_id}",
        data={"csrf_token": token, "content": content, "rating": rating},
    )
    return client.get(f"/product/{product_id}").get_data(as_text=True)


def test_script_tag_in_review_is_neutralised(logged_in_client, product_id):
    html = post_review(logged_in_client, product_id, "<script>alert(1)</script>Nice")

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script" not in html  # tags are removed, not displayed as escaped text
    assert "&amp;lt;script" not in html  # and never double-escaped
    assert "Nice" in html


def test_plain_review_is_still_shown(logged_in_client, product_id):
    html = post_review(logged_in_client, product_id, "Great product")

    assert "Great product" in html
