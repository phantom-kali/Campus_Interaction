from django import forms
from django.forms import modelformset_factory, BaseModelFormSet
from .models import Poll, Option
from datetime import datetime

class PollForm(forms.ModelForm):
    poll_type = forms.ChoiceField(
        choices=Poll.POLL_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='opinion'
    )

    def clean_expiration_time(self):
        # Retrieve the expiration_time data, discarding empty entries if present
        expiration_time_data = self.data.getlist('expiration_time')
        expiration_time_data = [item for item in expiration_time_data if item]  # Remove empty strings
        
        if expiration_time_data:
            try:
                # Take only the date and time up to minutes (YYYY-MM-DDTHH:MM)
                expiration_time = expiration_time_data[0][:16]  # Slice to "YYYY-MM-DDTHH:MM"
                return datetime.strptime(expiration_time, "%Y-%m-%dT%H:%M")
            except ValueError:
                self.add_error('expiration_time', "Invalid datetime format. Please use YYYY-MM-DDTHH:MM.")
        
        return None


    class Meta:
        model = Poll
        fields = [
            'title', 'description', 'poll_type', 'expiration_time', 
            'allow_expiration', 'background_color', 'show_share_button', 
            'is_public', 'banner_image', 'multi_option'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-title', 'placeholder': 'Enter poll title'}),
            'description': forms.Textarea(attrs={
                'class': 'form-description',
                'id': 'id_description',
                'placeholder': 'Enter poll description (optional)'
            }),
            'expiration_time': forms.DateTimeInput(attrs={
                'class': 'form-control form-period', 'type': 'datetime-local'
            }),
            'background_color': forms.TextInput(attrs={'class': 'form-image', 'type': 'color', 'id': 'background-color-picker'}),
            'banner_image': forms.FileInput(attrs={'class': 'form-control-file', 'id': 'banner_image'}),
            'allow_expiration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'multi_option': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_share_button': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OptionForm(forms.ModelForm):
    option_image = forms.ImageField(required=False, label='Upload Image', widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))

    class Meta:
        model = Option
        fields = ['option_text', 'is_correct', 'option_image']  # Include the new field

        widgets = {
            'option_text': forms.TextInput(attrs={'class': 'form-option-text', 'placeholder': 'Enter option text', 'autocomplete':'off'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Call the parent constructor
        if self.instance and self.instance.pk:
            self.fields['option_text'].required = False  # Make option_text optional for existing options

class OptionFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()

        filled_options_count = 0

        for form in self.forms:
            # Check if either option_text or option_image is filled
            if form.cleaned_data.get('option_text') or form.cleaned_data.get('option_image'):
                filled_options_count += 1

        # Ensure at least two options are filled
        if filled_options_count < 2:
            raise forms.ValidationError("You must fill at least two options with either text or an image.")

# Create the formset without extra forms for editing
OptionFormSet = modelformset_factory(Option, form=OptionForm, formset=OptionFormSet, extra=2)
class EditPollForm(PollForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Call the parent constructor

        # Make fields optional or change initial values if needed
        self.fields['title'].required = True  # Ensure title is required
        self.fields['description'].required = False  # Description is optional
        self.fields['expiration_time'].required = False  # Make expiration time optional if editing

        # If you want to set any initial values based on the instance, you can do that here
        if self.instance and self.instance.pk:
            # Example: Set the initial value of the poll type to the current type
            self.fields['poll_type'].initial = self.instance.poll_type
