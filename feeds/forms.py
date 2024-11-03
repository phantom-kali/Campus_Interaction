from django import forms
from .models import Post, Comment, Report
from django.core.validators import FileExtensionValidator
from django.conf import settings

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image', 'video', 'status']
        widgets = {
            'content': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': "What's on your mind?",
                    'maxlength': 500
                }
            ),
            'image': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'video/mp4,video/mov,video/avi'
            }),
            'status': forms.Select(attrs={'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        video = cleaned_data.get('video')
        content = cleaned_data.get('content')

        if image and video:
            raise forms.ValidationError(
                "You cannot upload both image and video"
            )

        if not any([content, image, video]):
            raise forms.ValidationError(
                "Post must contain either text, image, or video"
            )

        return cleaned_data


class CommentForm(forms.ModelForm):
    parent_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Write a comment...',
                    'maxlength': 500
                }
            )
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content.strip():
            raise forms.ValidationError("Comment cannot be empty")
        return content


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'description']
        widgets = {
            'report_type': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Please provide additional details...'
                }
            )
        }

    def clean_description(self):
        report_type = self.cleaned_data.get('report_type')
        description = self.cleaned_data.get('description')
        
        if report_type == 'other' and not description:
            raise forms.ValidationError(
                "Please provide details for 'Other' report type"
            )
        return description