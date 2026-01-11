# incomes/test_debug.py
from django.test import TestCase
from django.urls import reverse, resolve
from rest_framework.test import APIClient
from users.models import User
from .models import Income

class DebugIncomeViews(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create user with phone_number as required field
        self.user = User.objects.create_user(
            phone_number='+254712345678',
            password='testpass123',
            full_name='Test User',
            email='test@test.com',
            default_mpesa_number='+254712345678'
        )
        
        self.income = Income.objects.create(
            user=self.user,
            source_name='Test Income',
            amount=1000.00,
            frequency='MONTHLY'
        )
    
    def test_url_resolves(self):
        """Check if URL resolves correctly"""
        url = f'/api/incomes/{self.income.id}/'
        print(f"\nTesting URL: {url}")
        
        try:
            resolved = resolve(url)
            print(f"✓ Resolved view: {resolved.func.__name__}")
            print(f"✓ URL kwargs: {resolved.kwargs}")
        except Exception as e:
            print(f"✗ URL resolution failed: {e}")
    
    def test_authenticated_get(self):
        """Test GET with authentication"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/incomes/{self.income.id}/'
        
        print(f"\n--- Testing GET {url} ---")
        response = self.client.get(url)
        print(f"Status: {response.status_code}")
        if hasattr(response, 'data'):
            print(f"Response data: {response.data}")
        else:
            print(f"Response content: {response.content}")
        
        allow_header = response.get('Allow', None)
        if allow_header:
            print(f"Allowed methods: {allow_header}")
        else:
            print("No Allow header found")
        
    def test_authenticated_put(self):
        """Test PUT with authentication"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/incomes/{self.income.id}/'
        
        data = {
            'source_name': 'Updated Income',
            'amount': '1500.00',
            'frequency': 'MONTHLY',
            'description': 'Updated description',
            'is_active': True
        }
        
        print(f"\n--- Testing PUT {url} ---")
        print(f"Data: {data}")
        response = self.client.put(url, data, format='json')
        print(f"Status: {response.status_code}")
        if hasattr(response, 'data'):
            print(f"Response data: {response.data}")
        else:
            print(f"Response content: {response.content}")
    
    def test_authenticated_patch(self):
        """Test PATCH with authentication"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/incomes/{self.income.id}/'
        
        data = {
            'amount': '2000.00'
        }
        
        print(f"\n--- Testing PATCH {url} ---")
        print(f"Data: {data}")
        response = self.client.patch(url, data, format='json')
        print(f"Status: {response.status_code}")
        if hasattr(response, 'data'):
            print(f"Response data: {response.data}")
        else:
            print(f"Response content: {response.content}")
    
    def test_authenticated_delete(self):
        """Test DELETE with authentication"""
        self.client.force_authenticate(user=self.user)
        
        # Create a separate income for deletion
        income_to_delete = Income.objects.create(
            user=self.user,
            source_name='Delete Me',
            amount=500.00,
            frequency='ONE_OFF'
        )
        
        url = f'/api/incomes/{income_to_delete.id}/'
        
        print(f"\n--- Testing DELETE {url} ---")
        response = self.client.delete(url)
        print(f"Status: {response.status_code}")
        if hasattr(response, 'data'):
            print(f"Response data: {response.data}")
        
    def test_list_incomes(self):
        """Test listing incomes"""
        self.client.force_authenticate(user=self.user)
        url = '/api/incomes/'
        
        print(f"\n--- Testing GET {url} (list) ---")
        response = self.client.get(url)
        print(f"Status: {response.status_code}")
        if hasattr(response, 'data'):
            print(f"Response data: {response.data}")