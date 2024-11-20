from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from django.core.exceptions import ValidationError
import datetime

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use.")
        return email

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise ValidationError("A user with that username already exists.")
        return username

class ProfileUpdateForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }
        )
    )
    
    class Meta:
        model = Profile
        fields = [
            'student_id',
            'course',
            'year_of_study',
            'bio',
            'profile_pic',
            'campus',
            'gender',
            'date_of_birth'
        ]
        
    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if student_id:
            # Check if student ID is unique, excluding the current instance
            if Profile.objects.exclude(pk=self.instance.pk).filter(student_id=student_id).exists():
                raise ValidationError("This student ID is already registered.")
        return student_id
    
    def clean_year_of_study(self):
        year = self.cleaned_data.get('year_of_study')
        if year is not None:
            if year < 1:
                raise ValidationError("Year of study cannot be less than 1.")
            if year > 7:  # Assuming maximum 7 years for most programs
                raise ValidationError("Please enter a valid year of study (1-7).")
        return year
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            # Check if the date is not in the future
            if dob > datetime.date.today():
                raise ValidationError("Date of birth cannot be in the future.")
            
            # Check if the user is at least 16 years old
            today = datetime.date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                raise ValidationError("You must be at least 16 years old.")
            
            # Check if the date is not too far in the past (e.g., 100 years)
            if age > 100:
                raise ValidationError("Please enter a valid date of birth.")
                
        return dob
    
    def clean_profile_pic(self):
        profile_pic = self.cleaned_data.get('profile_pic')
        if profile_pic:
            # Check file size (limit to 5MB)
            if profile_pic.size > 5 * 1024 * 1024:
                raise ValidationError("Image file size must be less than 5MB.")
            
            # Check file extension
            allowed_extensions = ['jpg', 'jpeg', 'png']
            file_ext = profile_pic.name.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                raise ValidationError(
                    f"Only {', '.join(allowed_extensions)} files are allowed."
                )
                
        return profile_pic
    
    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if bio:
            # Remove extra whitespace
            bio = ' '.join(bio.split())
            
            # Check minimum length (optional)
            if len(bio) < 4:
                raise ValidationError("Bio must be at least 4 characters long.")
                
            if len(bio) > 500:
                raise ValidationError("Bio must not exceed 500 characters.")
                
        return bio

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        for field in self.fields:
            self.fields[field].required = False
            
        # Add placeholders and classes
        self.fields['bio'].widget.attrs.update({
            'placeholder': 'Tell us about yourself...',
            'rows': 1
        })
        self.fields['student_id'].widget.attrs.update({
            'placeholder': 'Enter your student ID'
        })
        self.fields['course'].widget.attrs.update({
            'placeholder': 'Enter your course name'
        })
        
        # Update choice fields labels
        self.fields['gender'].choices = [('', 'Select Gender')] + list(Profile.GENDER_CHOICES)