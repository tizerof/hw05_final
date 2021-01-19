from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create(username="testuser")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title="Заголовок тестовой группы",
            description="Описание группы",
            slug="test_group"
        )
        self.post = Post.objects.create(
            text="Текст сообщения",
            author=self.user,
            group=self.group
        )

    def test_posts_urls_exists(self):
        """Проверка доступности страниц приложения posts. """
        url_names = {
            "anonymous": (
                reverse("index"),
                self.group.get_absolute_url(),
                reverse("profile", kwargs={"username": self.user.username}),
                self.post.get_absolute_url(),
            ),
            "authorized": (
                reverse("new_post"),
            ),
        }
        # Проверка доступности страниц для авторизированных пользователей
        for url in url_names["anonymous"]:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)
        # Проверка доступности страниц для авторизированных пользователей
        for url in url_names["authorized"]:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)
        # Проверка перенаправления неавторизованных пользователей
        for url in url_names["authorized"]:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_edit_post_not_author(self):
        """Страница редактирования поста доступна только автору. """
        user_second = User.objects.create(username="testuser_second")
        authorized_client_second = Client()
        authorized_client_second.force_login(user_second)
        reverse_name = reverse("post_edit", kwargs={
            "username": self.user.username,
            "post_id": self.post.id})
        response_1 = self.authorized_client.get(reverse_name)
        self.assertEqual(response_1.status_code, 200)
        response_2 = self.guest_client.get(reverse_name)
        self.assertEqual(response_2.status_code, 302)
        response_3 = authorized_client_second.get(reverse_name)
        self.assertEqual(response_3.status_code, 302)
        # Проверка редиректа пользователя без прав доступа
        self.assertRedirects(response_3, self.post.get_absolute_url())

    def test_posts_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон. """
        templates_url_names = {
            reverse("index"): "index.html",
            self.group.get_absolute_url(): "group.html",
            reverse("new_post"): "post_new.html",
            reverse("profile",
                    kwargs={"username": self.user.username}):
                        "user/profile.html",
            self.post.get_absolute_url(): "user/post.html",
            reverse("post_edit",
                    kwargs={"username": self.user.username,
                            "post_id": self.post.id}): "post_new.html",
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_not_found_correct_response(self):
        """Сервер возвращает код 404, если страница не найдена"""
        response = self.guest_client.get("/test_page_404/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "misc/404.html")
