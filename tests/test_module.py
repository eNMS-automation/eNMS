def test_urls(client):
    r = client.get('/')
    assert r.status_code == 302
    
    r = client.get('/', follow_redirects=True)
    assert r.status_code == 200

# def test_login(username, password):
#     r = app.post('/login', data=dict(
#         username=username,
#         password=password
#     ), follow_redirects=True)
#     print(r)
#     assert True