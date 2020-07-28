from django.test import TestCase, Client


class PagesTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_404(self):
        response = self.client.get('/my_posts/')
        self.assertEqual(response.status_code, 404)
