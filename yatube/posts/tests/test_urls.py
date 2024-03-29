from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост достаточной длины',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.non_author = User.objects.create_user(username='test-non-author')
        self.non_author_client = Client()
        self.non_author_client.force_login(self.non_author)

    def test_urls_exists_at_desired_location_guest(self):
        """Страницы '/', '/group/test-slug/', '/profile/test-author/',
        '/posts/1/' доступны любому пользователю."""
        url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}): (
                'posts/profile.html'),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}): (
                'posts/post_detail.html')
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_location_authorized(self):
        """Страница '/create/' доступна авторизованному пользователю,
        страница '/posts/1/edit' доступна автору поста."""
        url_names = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}): (
                'posts/create_post.html'),
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_return_404(self):
        """Страница /unexisting_page/ не существует."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_redirect_anonymous(self):
        """Страницы '/create/', '/posts/1/edit/','/posts/1/comment/'перенаправляют
        анонимного пользователя на страницу логина."""
        url_names = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}): (
                'posts/create_post.html'),
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}): (
                'posts/post_detail.html'),
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                redirect_url = reverse('users:login') + '?next=' + address
                self.assertRedirects(response, redirect_url)

    def test_post_edit_url_redirect_non_author_authorized(self):
        """Страница /posts/1/edit/ перенаправляет авторизованного пользователя,
        не являющегося автором поста на страницу /posts/1/"""
        response = self.non_author_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}), follow=True)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.pk}))

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        url_names_templates = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/test-author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
