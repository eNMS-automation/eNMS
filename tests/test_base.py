from logging import CRITICAL, disable
disable(CRITICAL)

urls = {
    '': (
        '/',
        '/dashboard'
    ),
    '/admin': (
        '/user_management',
        '/login',
        '/administration',
        '/migrations'
    ),
    '/objects': (
        '/device_management',
        '/link_management',
        '/pool_management',
        '/import_export'
    ),
    '/views': (
        '/geographical_view',
        '/logical_view'
    ),
    '/automation': (
        '/service_management',
        '/workflow_management',
        '/workflow_builder'
    ),
    '/scheduling': (
        '/task_management',
        '/calendar'
    ),
    '/logs': (
        '/log_management',
        '/log_automation'
    )
}

free_access = {'/', '/admin/login', '/admin/create_account'}


def check_pages(*pages):
    def decorator(function):
        def wrapper(user_client):
            function(user_client)
            for page in pages:
                r = user_client.get(page, follow_redirects=True)
                assert r.status_code == 200
        return wrapper
    return decorator


def check_blueprints(*blueprints):
    def decorator(function):
        def wrapper(user_client):
            function(user_client)
            for blueprint in blueprints:
                for page in urls[blueprint]:
                    r = user_client.get(blueprint + page, follow_redirects=True)
                    assert r.status_code == 200
        return wrapper
    return decorator


# test the login system: login, user creation, logout
# test that all pages respond with HTTP 403 if not logged in, 200 otherwise


def test_authentication(base_client):
    for blueprint, pages in urls.items():
        for page in pages:
            page_url = blueprint + page
            expected_code = 200 if page_url in free_access else 403
            r = base_client.get(page_url, follow_redirects=True)
            assert r.status_code == expected_code


def test_urls(user_client):
    for blueprint, pages in urls.items():
        for page in pages:
            page_url = blueprint + page
            r = user_client.get(page_url, follow_redirects=True)
            assert r.status_code == 200
    # logout and test that we cannot access anything anymore
    r = user_client.get('/admin/logout', follow_redirects=True)
    test_authentication(user_client)
