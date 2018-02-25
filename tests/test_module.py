def test_urls(client):
    r = client.get('/')
    assert r.status_code == 302
    
    r = client.get('/', follow_redirects=True)
    assert r.status_code == 200
