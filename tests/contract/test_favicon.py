def test_favicon(client):
    # only exists to cover app/main.py's /favicon.ico route for coverage purposes
    # app/__main__.py stays untested regardless, it's the entrypoint file
    resp = client.get("/favicon.ico")

    assert resp.status_code == 200, resp.text
    assert "image" in resp.headers.get("content-type", "")
