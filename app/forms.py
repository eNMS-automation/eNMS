from django import forms

class BootstrapForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

class DeviceUploadForm(BootstrapForm):
    file = forms.FileField(label='Select a file')
    
class DeviceCreationForm(BootstrapForm):
    
    VENDOR_CHOICES = (
    ('cisco', 'Cisco'),
    ('juniper', 'Juniper')
    )
    
    hostname = forms.CharField(label='Hostname', max_length=100)
    ip_address = forms.CharField(label='IP address', max_length=100)
    vendor = forms.ChoiceField(choices=VENDOR_CHOICES)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['hostname'].widget.attrs.update({'placeholder': 'Enter a name'})
    
    def yield_values(self):
        for value in ('hostname', 'ip_address', 'vendor'):
            yield value