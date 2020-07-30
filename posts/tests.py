from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from io import BytesIO
from PIL import Image
from .models import Post, Group, Follow, Comment

User = get_user_model()

CACHE_DEFAULT = {
    'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }


class PostTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="james",
            email="bond_j@gmail.com"
        )
        self.client_auth = Client()
        self.client_auth.force_login(self.user)
        self.client_unauth = Client()
        self.group = Group.objects.create(
            title="тестовая группа",
            slug="test_group"
        )
        self.author = User.objects.create_user(
            username="dostoevsky",
            email="dostoevsky@gmail.com"
        )
        cache.clear()

    def url_check(self, url, group, user, text):
        response = self.client_auth.get(url)
        if 'paginator' in response.context:
            current_post = response.context['paginator'].object_list.first()
        else:
            current_post = response.context['post']
        self.assertEqual(current_post.text, text)
        self.assertEqual(current_post.group, group)
        self.assertEqual(current_post.author, user)

    def test_profile(self):
        """Проверка страницы профиля автора"""
        response = self.client_auth.get(
            reverse('profile', kwargs={'username': 'james'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["profile_user"], User)
        self.assertEqual(
            response.context["profile_user"].username, self.user.username
        )

    def test_new_post_authorized(self):
        """Авторизованный пользователь
           может создавать пост"""
        response = self.client_auth.post(
            reverse('new_post'),
            data={
                "text": "тест тест",
                "group": self.group.id
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, "тест тест")
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    @override_settings(CACHES=CACHE_DEFAULT)
    def test_post_on_pages(self):
        """Пост отображается на всех
           связанных страницах"""
        cache.clear()
        post = Post.objects.create(
            text="тест тест",
            author=self.user,
            group=self.group
        )
        for url in (
            reverse('index'),
            reverse('profile', kwargs={'username': 'james'}),
            reverse('group', kwargs={'slug': 'test_group'}),
            reverse(
                'post', kwargs={
                'username': 'james', 'post_id': post.id
                }
            )
        ):
            self.url_check(url, post.group, post.author, post.text)

    def test_new_post_unauthorized(self):
        """Неавторизованный пользователь не может
           создать пост"""
        response = self.client_unauth.post(
            reverse('new_post'),
            {
                "text": "пост неавторизованного пользователя"
            }
        )
        self.assertEqual(Post.objects.count(), 0)
        expected_url = reverse('login') + "?next=" + reverse('new_post')
        self.assertRedirects(response, expected_url)

    @override_settings(CACHES=CACHE_DEFAULT)
    def test_edit(self):
        """Пользователь может редактировать свой пост"""
        group2 = Group.objects.create(
            title="вторая группа",
            slug="sec_group"
        )
        first_post = Post.objects.create(
            text="Bond... James Bond",
            author=self.user,
            group=self.group
        )
        self.client_auth.post(
            reverse(
                'edit_post', kwargs={
                    'username': 'james', 'post_id': first_post.id
                }
            ),
            {
                "text": "another text",
                "group": group2.id
            }
        )
        post = Post.objects.first()
        for url in (
                reverse('index'),
                reverse('profile', kwargs={'username': 'james'}),
                reverse('group', kwargs={'slug': 'sec_group'}),
                reverse(
                    'post', kwargs={
                        'username': 'james', 'post_id': post.id
                    }
                )
        ):
            self.url_check(url, group2, self.user, post.text)
        response = self.client_auth.get(
            reverse('group', kwargs={'slug': 'test_group'})
        )
        self.assertNotContains(response, post)

    @override_settings(CACHES=CACHE_DEFAULT)
    def test_image(self):
        """Проверка загрузки графического файла"""
        file = BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        img = SimpleUploadedFile(
            file.name, file.read(), content_type='image/png'
        )
        post = Post.objects.create(
            text="проверка изображения",
            author=self.user,
            group=self.group,
            image=img
        )
        cache.clear()
        for url in (
                reverse('index'),
                reverse('profile', kwargs={'username': 'james'}),
                reverse('group', kwargs={'slug': 'test_group'}),
                reverse(
                    'post', kwargs={
                        'username': 'james', 'post_id': post.id
                    }
                )
        ):
            response = self.client_auth.get(url)
            self.assertContains(response, '<img class')

    def test_upload(self):
        """Проверка, что неграфический файл не загрузится."""
        txt = SimpleUploadedFile(
            name='test_text.txt',
            content=b'abc',
            content_type='text/plain'
        )
        response = self.client_auth.post(
            reverse('new_post'),
            {
                'text': 'проверка изображения',
                'group': self.group.id,
                'author': self.user,
                'image': txt
            }
        )
        self.assertNotContains(response, '<img class')

    def test_cache_index(self):
        """Проверка, что главная странийа кэшируется."""
        cache.clear()
        post = Post.objects.create(
            text="проверка кэша",
            author=self.user,
            group=self.group
        )
        response = self.client_auth.get(reverse('index'))
        self.assertContains(response, post.text)
        post2 = Post.objects.create(
            text="дубль два",
            author=self.user,
            group=self.group
        )
        response2 = self.client_auth.get(reverse('index'))
        self.assertNotContains(response2, post2.text)
        cache.clear()
        response2 = self.client_auth.get(reverse('index'))
        self.assertContains(response2, post2.text)

    def test_auth_follow(self):
        """Авторизованный пользователь может подписываться
           на других пользователей."""
        response = self.client_auth.get(
            reverse(
                'profile_follow', kwargs={
                    'username': 'dostoevsky'
                }
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.author.following.get(user=self.user).user,
            self.user
        )

    def test_auth_unfollow(self):
        """Авторизованный пользователь может
           удалять авторов из подписок."""
        response = self.client_auth.get(
            reverse(
                'profile_unfollow', kwargs={
                    'username': 'dostoevsky'
                }
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.author.following.count(), 0
        )

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
           кто на него подписан"""
        follow = Follow.objects.create(
            user=self.user,
            author=self.author
        )
        self.assertEqual(self.user.follower.first(), follow)
        new_post = Post.objects.create(
            text="проверка подписки",
            author=self.author
        )
        response = self.client_auth.get(
            reverse('follow_index')
        )
        self.assertContains(response, new_post.text)

    def test_non_follow_index(self):
        """Новая запись пользователя не появляется
           в ленте пользователя, который не подписан."""
        self.client_auth.logout()
        new_user = User.objects.create_user(
            username="homer",
            email="homer@gmail.com"
        )
        self.client_auth.force_login(new_user)
        new_post = Post.objects.create(
            text="проверка подписки",
            author=self.author
        )
        response = self.client_auth.get(
            reverse('follow_index')
        )
        self.assertNotContains(response, new_post.text)

    def test_auth_comments(self):
        """Авторизированный пользователь может комментировать посты."""
        post = Post.objects.create(
            text="проверка коммента",
            author=self.user
        )
        response = self.client_auth.post(
            reverse(
                'add_comment', kwargs={
                    'username': 'james', 'post_id': post.id
                }
            ),
            {
                "text": "коммент"
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        comment = Comment.objects.get(post=post)
        self.assertEqual(comment.text, "коммент")
        self.assertEqual(comment.post, post)
        self.assertEqual(comment.author, self.user)

    def test_unauth_comments(self):
        """Неавторизированный пользователь не может комментировать посты"""
        post = Post.objects.create(
            text="проверка коммента",
            author=self.user
        )
        response = self.client_unauth.post(
            reverse(
                'add_comment', kwargs={
                    'username': 'james', 'post_id': post.id
                }
            ),
            {
                "text": "comm_unath"
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 0)
        resp = self.client_auth.get(
            reverse('post', kwargs={'username': 'james', 'post_id': post.id})
        )
        self.assertNotContains(resp, "comm_unath")
