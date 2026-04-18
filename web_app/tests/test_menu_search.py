from django.test import TestCase, Client
from django.urls import reverse
from web_app.models import Type, Menu


class MenuSearchHTMLTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        menu_type = Type.objects.create(type_name='炸雞')
        cls.menu = Menu.objects.create(
            type=menu_type,
            name='香脆炸雞腿',
            price=90,
            status=True,
        )

    def setUp(self):
        self.client = Client()

    def test_home_contains_search_input(self):
        """首頁應包含 id="menu-search" 的搜尋框"""
        response = self.client.get(reverse('web_app:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="menu-search"')

    def test_home_item_card_has_data_name(self):
        """首頁品項卡片應包含 data-name 屬性"""
        response = self.client.get(reverse('web_app:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-name="{self.menu.name}"')
