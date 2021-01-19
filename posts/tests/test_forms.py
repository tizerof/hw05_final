import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_group = Group.objects.create(
            title="Заголовок тестовой группы",
            description="Описание",
            slug="test_group"
        )
        cls.small_jpeg = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.uploaded = SimpleUploadedFile(
            name='small.jpeg',
            content=self.small_jpeg,
            content_type='image/jpeg')

    def test_create_post_form(self):
        """Валидная форма создает запись Posts."""
        forms_data = (
            {
                "group": self.test_group.id,
                "text": "Текст 1",
                "image": self.uploaded,
            },
            {
                "text": "Текст 2",
            },
        )
        for form_data in forms_data:
            posts_count = Post.objects.count()
            response = self.authorized_client.post(
                reverse("new_post"),
                data=form_data,
                follow=True)
            self.assertRedirects(response, reverse("index"))
            self.assertEqual(Post.objects.count(), posts_count + 1)
            self.assertContains(
                response, form_data["text"],
                msg_prefix="Новый пост отсутствует на главной странице")
            cache.clear()

    def test_invalid_form_doest_create_post(self):
        """Невалидная форма не создает запись Posts."""
        form_data = {"group": self.test_group.id, "text": " "}
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse("new_post"),
            data=form_data,
            follow=True
        )
        self.assertFormError(response, "form", "text", "Обязательное поле.")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_form(self):
        """Валидная форма изменяет запись Posts."""
        post = Post.objects.create(
            text="Текст сообщения",
            author=self.user,)
        form_data = {
            "group": self.test_group.id,
            "text": "Измененный текст",
            "image": self.uploaded,
        }
        reverse_url = reverse("post_edit", kwargs={
            "username": self.user.username,
            "post_id": post.id})
        response = self.authorized_client.post(
            reverse_url,
            data=form_data,)
        post.refresh_from_db()
        self.assertEqual(post.group, self.test_group)
        self.assertEqual(post.text, form_data['text'])
        self.assertRedirects(response, post.get_absolute_url())


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create(username="testuser")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text="Текст поста",
            author=self.user)

    def test_add_comment(self):
        """Только авторизированный пользователь может комментировать посты."""
        comment_count = Comment.objects.count()
        reverse_url = reverse("add_comment", kwargs={
            "username": self.user.username,
            "post_id": self.post.id})
        form_data = {"text": "Текст комментария"}
        self.authorized_client.post(reverse_url, data=form_data)
        self.assertTrue(
            Comment.objects.filter(
                post=self.post,
                author=self.user,
                text=form_data["text"]).exists(),
            "Форма комментариев не работает")
        self.guest_client.post(reverse_url, data=form_data)
        self.assertEqual(
            Post.objects.count(), comment_count + 1,
            ("Неавторизованный пользователь может добавить комментарий"))
