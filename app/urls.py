from django.conf.urls import url
from app import views

urlpatterns = [

    url(r'^create_devices\.html', views.get_name),
    # Matches any html file - to be used for gentella
    # Avoid using your .html in your resources.
    # Or create a separate django app.
    url(r'^.*\.html', views.gentella_html, name='ngNMS'),

    # The home page
    url(r'^$', views.index, name='index'),
]