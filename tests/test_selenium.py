from tests.test_base import urls


def selenium_test(selenium_client):
    for blueprint, pages in urls.items():
        for page in pages:
            selenium_client.get('http://127.0.0.1:5000' + blueprint + page)
            for entry in selenium_client.get_log('browser'):
                assert entry['level'] != 'SEVERE'
