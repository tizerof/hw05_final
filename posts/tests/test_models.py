import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from ..models import Comment, Follow, Group, Post, User

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        text_example = "Тестовый текст поста, в нем 39 символов"
        cls.group = Group.objects.create(
            title="Заголовок тестовой группы",
            description="Описание группы",)
        user = User.objects.create(username="testuser")
        small_jpeg = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')
        upload_img = SimpleUploadedFile(
            name='small.jpeg',
            content=small_jpeg,
            content_type='image/jpeg',)
        cls.post = Post.objects.create(
            text=text_example,
            author=user,
            group=cls.group,
            image=upload_img)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_verbose_names(self):
        """verbose_name в полях совпадает с ожидаемым. """
        field_verboses = {
            "text": "Текст поста",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Группа",
            "image": "Изображение"
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name, expected)

    def test_help_texts(self):
        """help_text в полях совпадает с ожидаемым. """
        field_help_texts = {
            "group": "Группа публикации поста",
            "text": "Тут введите текст поста",
            "image": "Изображение поста"
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text, expected)

    def test_object_name_is_text_field(self):
        """В поле __str__  объекта Post равно первым 15 символам поля text """
        expected_object_name = self.post.text[:15]
        self.assertEqual(expected_object_name, str(self.post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Заголовок тестовой группы",
            description="Описание",
            slug="test_group")

    def test_object_name_is_title_field(self):
        """В поле __str__  объекта Group записано значение поля title"""
        expected_object_name = self.group.title
        self.assertEqual(expected_object_name, str(self.group))


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="testuser")
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.user,)
        text_example = "Тестовый текст комментария, в нем 45 символов"

    def test_object_name_is_title_field(self):
        """В поле __str__  объекта Comment равно первым 15 символам поля text"""
        text_example = "Тестовый текст комментария, в нем 45 символов"
        comment = Comment.objects.create(
            post=self.post,
            text=text_example,
            author=self.user,)
        expected_object_name = comment.text[:15]
        self.assertEqual(expected_object_name, str(comment))


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create(username="follower")
        cls.author = User.objects.create(username="author")

    def test_object_name_is_title_field(self):
        """В поле __str__  объекта Follow отображается 
        никнеймы автора и подписчика. """
        follow = Follow.objects.create(user=self.follower, author=self.author)
        expected_object_name = (f"@{self.follower.username}"
                                f" is follower @{self.author.username}")
        self.assertEqual(expected_object_name, str(follow))
