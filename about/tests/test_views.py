from django.test import Client, TestCase
from django.urls import reverse


class StaticURLTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_about_urls_exists(self):
        """Проверка доступности страниц приложения about. """
        url_names = (
            reverse("about:author"),
            reverse("about:tech"),
        )
        for reverse_name in url_names:
            response = self.client.get(reverse_name)
            self.assertEqual(response.status_code, 200)

    def test_about_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон. """
        templates_url_names = {
            "about/author.html": reverse("about:author"),
            "about/tech.html": reverse("about:tech"),
        }
        for template, reverse_name in templates_url_names.items():
            with self.subTest():
                response = self.client .get(reverse_name)
                self.assertTemplateUsed(response, template)
