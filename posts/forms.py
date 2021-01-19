from django.forms import ModelForm, Textarea

from .models import Comment, Post


class PostForm(ModelForm):
    """Форма создания нового поста."""
    class Meta:
        model = Post
        fields = ("group", "text", "image",)


class CommentForm(ModelForm):
    """Форма создания нового комментария."""
    class Meta:
        model = Comment
        widgets = {'text': Textarea(attrs={
            'cols': 30,
            'rows': 3,
            'placeholder': 'Введите комментарий'})}
        fields = ("text",)
