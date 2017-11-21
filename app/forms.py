from django import forms

class BootstrapForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a file')
    
class NameForm(BootstrapForm):
    
    hostname = forms.CharField(label='Hostname', max_length=100)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hostname'].widget.attrs.update({'placeholder': 'Enter a name'})
    