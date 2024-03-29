from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms


from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follow_author = User.objects.create_user(username='follow-author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group,
        )
        cls.POST_CREATE_URL = reverse('posts:post_create')
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': f'{cls.post.pk}'})

    def setUp(self):
        cache.clear()
        self.urls_templates_data = [
            (PostsPagesTests.POST_CREATE_URL, 'posts/create_post.html'),
            (PostsPagesTests.POST_EDIT_URL, 'posts/create_post.html')
        ]

    def test_pages_uses_correct_template(self):
        """Во view-функциях используются соответствующие шаблоны."""
        pages_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}): (
                'posts/create_post.html'
            ),
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def form_fields_is_valid(self, url):
        response = PostsPagesTests.authorized_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        self.form_fields_is_valid(PostsPagesTests.POST_CREATE_URL)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        self.form_fields_is_valid(PostsPagesTests.POST_EDIT_URL)
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        self.assertTrue(response.context.get('is_edit'))
        self.assertEqual(response.context.get('post_id'), 1)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(
            response.context['post'].text, self.post.text
        )
        self.assertEqual(
            response.context['post'].author, self.post.author
        )
        self.assertEqual(
            response.context['post'].group, self.post.group
        )
        self.assertEqual(
            response.context['post_number'],
            Post.objects.filter(author=self.user).count()
        )
        self.assertEqual(
            response.context['post'].image,
            self.post.image
        )

    def test_new_post_with_group_in_correct_pages(self):
        """Новый пост с группой отображается на правильных страницах"""
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        new_post = Post.objects.create(
            author=self.user,
            text='Тестовый пост с новой группой',
            group=new_group,
        )
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertIn(new_post, response.context['page_obj'])
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': new_group.slug})
        )
        self.assertIn(new_post, response.context['page_obj'])
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertNotIn(new_post, response.context['page_obj'])
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertIn(new_post, response.context['page_obj'])

    def test_index_show_correct_context(self):
        """Шаблон страницы index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        first_object = response.context['page_obj'][0]
        text = first_object.text
        self.assertEqual(text, self.post.text)
        self.assertEqual(
            self.post.image,
            response.context['page_obj'][Post.objects.count() - 1].image,
        )

    def test_group_list_show_correct_context(self):
        """Шаблон страницы group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        text = first_object.text
        self.assertEqual(text, self.post.text)
        self.assertEqual(
            response.context['group'], self.group
        )
        self.assertEqual(
            self.post.image,
            response.context['page_obj'][Post.objects.count() - 1].image,
        )

    def test_profile_show_correct_context(self):
        """Шаблон страницы profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        first_object = response.context['page_obj'][0]
        text = first_object.text
        self.assertEqual(text, self.post.text)
        self.assertEqual(
            response.context['author'], self.user
        )
        self.assertEqual(
            response.context['post_number'],
            Post.objects.filter(author=self.user).count()
        )
        self.assertEqual(
            self.post.image,
            response.context['page_obj'][Post.objects.count() - 1].image,
        )

    def test_post_detail_show_new_comment(self):
        """Шаблон post_detail отображает новый комментарий."""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый текст комментария'
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertIn(comment, response.context['comments'])

    def test_index_cache(self):
        """Шаблон страницы index хранит записи в кеше"""
        post_cache = Post.objects.create(
            author=self.user,
            text='Тестовый пост для проверки кеша',
        )
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        post_cache.delete()
        new_response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(response.content, new_response.content)

    def test_follow_author(self):
        """Авторизованный пользователь может
        подписываться на других пользователей."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.follow_author.username}
        ))
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.follow_author
        ).exists())

    def test_unfollow_author(self):
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.follow_author.username}
        ))
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.follow_author
        ).exists())

    def test_new_post_in_correct_follow_pages(self):
        """Новая запись автора появляется в ленте подписчиков."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.follow_author.username}
        ))
        new_post = Post.objects.create(
            author=self.follow_author,
            text='Тестовый пост',
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(new_post, response.context['page_obj'])

    def test_new_post_in_correct_follow_pages(self):
        """Новая запись автора не появляется в ленте тех, кто не подписан."""
        new_post = Post.objects.create(
            author=self.follow_author,
            text='Тестовый пост',
        )
        other_user = User.objects.create_user(username='other_user')
        other_authorized_client = Client()
        other_authorized_client.force_login(other_user)
        response = other_authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(new_post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        TEST_POST_COUNT = 14
        posts = (
            Post(
                author=cls.user,
                text=f'Тестовый пост №{i}',
                group=cls.group) for i in range(TEST_POST_COUNT))
        Post.objects.bulk_create(posts)

    def setUp(cls):
        cache.clear()

    def test_pages_with_pagination_contain_ten_and_four_records(self):
        """Шаблоны страниц index, group_list, profile сформированы
        с правильным количеством записей."""
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), settings.POSTS_NUMBER
                )
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    Post.objects.count() - settings.POSTS_NUMBER
                )
