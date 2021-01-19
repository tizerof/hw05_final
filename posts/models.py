from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


class Group(models.Model):
    """Модель групп для публикаций."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("group", kwargs={"slug": self.slug})


class Post(models.Model):
    """Модель публикации."""
    text = models.TextField("Текст поста", help_text="Тут введите текст поста")
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="posts",)
    group = models.ForeignKey(
        Group,
        verbose_name="Группа",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="group_posts",
        help_text="Группа публикации поста",)
    image = models.ImageField(
        upload_to='posts/',
        verbose_name="Изображение",
        blank=True,
        null=True,
        help_text="Изображение поста",)

    def get_absolute_url(self):
        return reverse("post", kwargs={
            "username": self.author,
            "post_id": self.pk})

    class Meta:
        ordering = ("-pub_date",)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name="Пост",
        on_delete=models.CASCADE,
        related_name="post_comments",)
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="comments",)
    text = models.TextField(
        "Текст комментария",
        help_text="Тут введите текст поста")
    created = models.DateTimeField("Дата комментария", auto_now_add=True)

    class Meta:
        ordering = ("created",)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Подписчик",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="follower",)
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="following",)

    def __str__(self):
        return f"@{self.user.username} is follower @{self.author.username}"
