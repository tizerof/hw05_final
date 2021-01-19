from django.contrib import admin

from .models import Comment, Follow, Group, Post


class GroupAdmin(admin.ModelAdmin):
    """
    Класс отображения групп в админке сайта.
    """
    list_display = ("pk", "title", "slug", "description")
    search_fields = ("title",)
    empty_value_display = "-пусто-"
    prepopulated_fields = {"slug": ("title",)}
    list_per_page = 10


class PostAdmin(admin.ModelAdmin):
    """
    Класс отображения постов в админке сайта.
    """
    list_display = ("pk", "text", "pub_date", "group", "author")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"
    list_per_page = 10


class CommentAdmin(admin.ModelAdmin):
    """
    Класс отображения комментариев в админке сайта.
    """
    list_display = ("pk", "post", "text", "created", "author")
    search_fields = ("text",)
    list_filter = ("created",)
    empty_value_display = "-пусто-"
    list_per_page = 10


admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow)
