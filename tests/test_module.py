# (Url, authorization required, redirection)

urls = {
    '/': (
        '',
        'dashboard',
        'dashboard_control',
        'project'
        ),
    '/users/': (
        'overview',
        'manage_users',
        'login',
        'create_account',
        'tacacs_server'
        ),
    '/objects/': (
        'objects',
        'object_creation',
        'object_deletion',
        'object_filtering'
        ),
    '/views/': (
        'geographical_view',
        'logical_view',
        'google_earth_export'
        ),
    '/scripts/': (
        'overview',
        'script_creation',
        'ansible_script'
        ),
    '/tasks/': (
        'task_management',
        'calendar'
        ),
    '/logs/': (
        'overview',
        'syslog_server'
        )
    }

free_access = {'/', '/users/login', '/users/create_account'}

def test_authentication(base_client):
    for blueprint, pages in urls.items():
        for page in pages:
            page_url = blueprint + page
            print(page_url)
            expected_code = 200 if page_url in free_access else 403
            r = base_client.get(page_url, follow_redirects=True)
            assert r.status_code == expected_code

def test_urls(user_client):
    for blueprint, pages in urls.items():
        for page in pages:
            page_url = blueprint + page
            r = user_client.get(page_url, follow_redirects=True)
            assert r.status_code == 200