from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import TripPlan
from tourism.models import Destination


class PlannerTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(
            name="Test Heritage Place",
            category="Heritage",
            description="A destination used for planner tests.",
            location="Kanyakumari",
            visiting_hours="9 AM to 5 PM",
            best_time="Winter",
            entry_fee="Free",
            budget_level="Budget",
        )
        self.user = User.objects.create_user(
            username="planner-user",
            password="safe-test-password",
        )
        self.client.force_login(self.user)

    def test_planner_form_and_valid_submission(self):
        planner_url = reverse("planner")
        self.assertEqual(self.client.get(planner_url).status_code, 200)

        response = self.client.post(
            planner_url,
            {
                "days": "2",
                "category": "All",
                "trip_type": "Family",
                "budget": "Moderate",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your starting itinerary")
        self.assertEqual(response.context["selected_days"], 2)
        self.assertEqual(response.context["itinerary"][0]["destinations"][0], self.destination)
        self.assertEqual(TripPlan.objects.filter(user=self.user).count(), 1)

    def test_invalid_planner_submission_shows_error_without_saving(self):
        response = self.client.post(
            reverse("planner"),
            {
                "days": "not-a-number",
                "category": "All",
                "trip_type": "Family",
                "budget": "Budget",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose a trip length between 1 and 5 days.")
        self.assertEqual(TripPlan.objects.filter(user=self.user).count(), 0)

    def test_invalid_planner_choices_show_error_without_saving(self):
        response = self.client.post(
            reverse("planner"),
            {
                "days": "1",
                "category": "Unknown",
                "trip_type": "Family",
                "budget": "Budget",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose one of the listed interests.")
        self.assertEqual(TripPlan.objects.filter(user=self.user).count(), 0)
