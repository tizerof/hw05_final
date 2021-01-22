import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User
from ..views import POSTS_PER_PAGE

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostsPagesTests(TestCase):
    """Класс тестов страниц приложения posts"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Заголовок тестовой группы",
            description="Описание",
            slug="test_group")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        small_jpeg = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')
        upload_image = SimpleUploadedFile(
            name='small.jpeg',
            content=small_jpeg,
            content_type='image/jpeg',)
        self.post = Post.objects.create(
            text="Текст сообщения",
            author=self.user,
            group=self.group,
            image=upload_image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("index"): "index.html",
            self.group.get_absolute_url(): "group.html",
            reverse("new_post"): "post_new.html",
            reverse("profile", kwargs={"username": self.user.username}):
            "user/profile.html",
            self.post.get_absolute_url(): "user/post.html",
            reverse("post_edit", kwargs={
                "username": self.user.username,
                "post_id": self.post.id}): "post_new.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_and_group_page_show_correct_context(self):
        """Шаблон home и group сформирован с правильным контекстом."""
        pages_names = (
            reverse("index"),
            self.group.get_absolute_url(),
        )
        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                post = response.context.get("page")[0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.user)
                self.assertEqual(post.pub_date, self.post.pub_date)
                self.assertEqual(post.image, self.post.image)

    def test_new_post_correct_context(self):
        """Шаблон post_new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("new_post"))
        form_fields = {
            "group": forms.fields.ChoiceField,
            "text": forms.fields.CharField,
            "image": forms.fields.ImageField,
        }
        self.assertTrue(response.context.get("is_new"))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_not_in_other_groups(self):
        """Новый пост не попал в группу, для которой не был предназначен."""
        group_2 = Group.objects.create(
            title="Заголовок второй тестовой группы",
            slug="second_test_group")
        reverse_name = group_2.get_absolute_url()
        response = self.authorized_client.get(reverse_name)
        self.assertEqual(response.context.get("page").object_list.count(), 0)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        reverse_name = reverse("profile", kwargs={
            "username": self.user.username})
        response = self.authorized_client.get(reverse_name)
        post = response.context.get("page")[0]
        author = response.context.get("author")
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(author, self.post.author)
        self.assertEqual(post.image, self.post.image)

    def test_post_view_correct_context(self):
        """Шаблон post_view сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.post.get_absolute_url())
        post = response.context.get("post")
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.image, self.post.image)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        reverse_name = reverse("post_edit", kwargs={
            "username": self.user.username,
            "post_id": self.post.id})
        response = self.authorized_client.get(reverse_name)
        form_fields = {
            "group": forms.fields.ChoiceField,
            "text": forms.fields.CharField,
            "image": forms.fields.ImageField,
        }
        self.assertFalse(response.context.get("is_new"))
        self.assertEqual(response.context.get("post"), self.post)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)


class FollowViewsTests(TestCase):
    """Класс тестов подписок"""

    def setUp(self):
        self.author = User.objects.create(username="author")
        self.follower = User.objects.create(username="follower")
        self.not_follower = User.objects.create(
            username="not_follower")
        self.authorized_follower = Client()
        self.authorized_not_follower = Client()
        self.authorized_follower.force_login(self.follower)
        self.authorized_not_follower.force_login(self.not_follower)
        self.post = Post.objects.create(
            text="Текст сообщения",
            author=self.author)
        self.user_followed = Follow.objects.create(
            user=self.follower, author=self.author)

    def test_user_follow(self):
        """Авторизованный пользователь может подписываться на
        других пользователей."""
        reverse_name_follow = reverse("profile_follow", kwargs={
            "username": self.author.username})
        self.authorized_not_follower.get(reverse_name_follow)
        self.assertTrue(
            Follow.objects.filter(
                user=self.not_follower,
                author=self.author).exists(),
            "Подписка на пользователя не работает")

    def test_user_not_follow_himself(self):
        """Пользователь не может подписываться сам на себя."""
        reverse_name_follow = reverse("profile_follow", kwargs={
            "username": self.follower.username})
        self.authorized_follower.get(reverse_name_follow)
        self.assertFalse(Follow.objects.filter(
            user=self.follower, author=self.follower).exists())

    def test_user_unfollow(self):
        """Подписанный пользователь может удалять других пользователей
        из подписок."""
        reverse_name_unfollow = reverse("profile_unfollow", kwargs={
            "username": self.author.username})
        self.authorized_follower.get(reverse_name_unfollow)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.author).exists(),
            "Удаление подписки на пользователя не работает")

    def test_follow_index_correct_context(self):
        """Шаблон follow_index сформирован для подписанного пользователя 
        с правильным контекстом."""
        reverse_name = reverse("follow_index")
        response_follow = self.authorized_follower.get(reverse_name)
        self.assertIn(
            self.post, response_follow.context.get("page").object_list)

    def test_not_follow_index_correct_context(self):
        """Шаблон follow_index сформирован для неподписанного пользователя
        с правильным контекстом."""
        reverse_name = reverse("follow_index")
        response_not_follow = self.authorized_not_follower.get(reverse_name)
        self.assertNotIn(
            self.post, response_not_follow.context.get("page").object_list)


class PaginatorViewsTest(TestCase):
    """Класс тестов пагинатора"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Заголовок тестовой группы",
            description="Описание",
            slug="test_group")

    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.client = Client()
        post = Post(text="Текст сообщения", author=self.user, group=self.group)
        batch_size = POSTS_PER_PAGE + 3
        batch = [post for p in range(batch_size)]
        Post.objects.bulk_create(batch, batch_size)

    def test_pages_contains_ten_posts(self):
        """Корректное отображение страниц c постами."""
        pages_names = {
            reverse("index"): POSTS_PER_PAGE,
            reverse('index') + '?page=2': 3,
            self.group.get_absolute_url(): POSTS_PER_PAGE,
            self.group.get_absolute_url() + '?page=2': 3,
            reverse("profile", kwargs={"username": self.user.username}):
            POSTS_PER_PAGE,
            reverse("profile", kwargs={"username": self.user.username}) +
            '?page=2': 3,
        }
        for reverse_name, post_nums in pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context.get('page').object_list),
                    post_nums,)
