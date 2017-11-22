from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from .forms import DeviceUploadForm, DeviceCreationForm
from .functions import handle_uploaded_file

def index(request):
    context = {}
    template = loader.get_template('app/index.html')
    return HttpResponse(template.render(context, request))

def gentella_html(request):
    print('test')
    context = {}
    # The template to be loaded as per gentelella.
    # All resource paths for gentelella end in .html.

    # Pick out the html file name from the url. And load that template.
    load_template = request.path.split('/')[-1]
    template = loader.get_template('app/' + load_template)
    return HttpResponse(template.render(context, request))
    
def create_devices(request):
    print(request.method)
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        device_creation_form = DeviceCreationForm(request.POST)
        device_upload_form = DeviceUploadForm(request.POST, request.FILES)
        # check whether it's valid:
        print(device_creation_form.is_valid(), device_upload_form.is_valid())
        if device_creation_form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')
        elif device_upload_form.is_valid():
            handle_uploaded_file(request.FILES['file'])
            return HttpResponseRedirect('devices.html')

    # if a GET (or any other method) we'll create a blank form
    else:
        device_creation_form = DeviceCreationForm()
        device_upload_form = DeviceUploadForm()

    return render(
                  request, 
                  'app/create_devices.html', 
                  {
                  'device_creation_form': device_creation_form,
                  'device_upload_form': device_upload_form
                  })