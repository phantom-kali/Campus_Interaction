#events/forms.py
from django import forms
from .models import Event, Comment, EventRegistration,Reply


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'start_date', 'end_date', 
                 'location', 'image', 'max_participants', 'is_public', 'content', 
                 'attachments']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter event title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe the event, including the university details',
                'rows': 3,
            }),
            'event_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'event-type-select',
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter event location (optional for text-based events)',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter content for text-based event',
                'rows': 5,
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'help_text': 'Optional: Upload an image for the event.'
            }),
            'attachments': forms.FileInput(attrs={
                'class': 'form-control',
                'help_text': 'Optional: Upload attachments for text-based events.'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Max participants',
                'min': 1,
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        event_type = cleaned_data.get('event_type')
        location = cleaned_data.get('location')
        content = cleaned_data.get('content')

        if event_type == 'physical' and not location:
            raise forms.ValidationError("Location is required for physical events.")
        
        if event_type == 'text' and not content:
            raise forms.ValidationError("Content is required for text-based events.")

        return cleaned_data
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment...',
                'required': True
            })
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or content.isspace():
            raise forms.ValidationError("Comment content cannot be empty.")
        return content.strip()

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']


class EventRegistrationForm(forms.ModelForm):
    name = forms.CharField(
        max_length=255,
        required=True,
        error_messages={'required': 'Please enter your name'}
    )
    email = forms.EmailField(
        required=True,
        error_messages={'required': 'Please enter your email'}
    )

    class Meta:
        model = EventRegistration
        fields = ['name', 'email']

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['name'].initial = self.user.get_full_name() or self.user.username
            self.fields['email'].initial = self.user.email
    
   

    def clean(self):
        name = self.cleaned_data.get('name')
        if not name or name.strip() == '':
            raise forms.ValidationError("Name is required.")
        return name.strip()
    def clean(self):
        if self.event and self.event.max_participants:
            current_registrations = EventRegistration.objects.filter(event=self.event).count()
            if current_registrations >= self.event.max_participants:
                raise forms.ValidationError("Event has reached the maximum number of participants.")
        return super().clean()