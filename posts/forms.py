from django import forms
from django.contrib.auth import get_user_model
from .models import Post, Comment

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']

    def validate_form(self):
        data = self.cleaned_data['text']
        if data is None:
            raise forms.ValidationError('Пост не может быть пустым')
        return data


class CommentForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Comment
        fields = ['text']

    def validate_form(self):
        data = self.cleaned_data['text']
        if data is None:
            raise forms.ValidationError('Комментарий не может быть пустым')
        return data
