import uuid

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.jobs.models import User

from .models import Company, Job

# Create your tests here.


class JobViewSetsTestCase(TestCase):
    def setUp(self):
        # Create sample data for testing
        self.company_data = {
            "name": "Testing name",
            "location": "Testing Location",
            "about": "Testing about",
            "founded_year": 2011,
            "team_members": 110,
            "social_profiles": "https://testing.com/testing",
            "company_id": uuid.uuid4(),
        }
        self.company = Company.objects.create(**self.company_data)

        # job_data struct
        self.job_data = {
            "job_role": "Data Scientist",
            "company": self.company,
            "description": "Join our innovative team as a Data Scientist.",
            "location": "New York, NY",
            "post_date": "2024-02-15",
            "posted": True,
            "experience": 3,
            "job_type": "part time",
            "salary": 75000.00,
            "qualifications": "Master's degree in Data Science or related field",
            "vacency_position": 2,
            "industry": "Data Science",
            "category": "Analytics",
            "is_active": True,
            "job_responsibilities": "Analyze and interpret complex data sets.",
            "skills_required": "Python, R, Machine Learning",
            "education_or_certifications": "Master's degree in Data Science or related field.",
            "employer_id": uuid.uuid4(),
        }

        self.job = Job.objects.create(**self.job_data)

        # job url
        self.job_url = "/jobs/"

        # Create an instance of the APIClient and set the Authorization header
        self.client = APIClient()
        # dummy token
        self.access_token = ""
        self.client.credentials(HTTP_ACCESSTOKEN=self.access_token)
