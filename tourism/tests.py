from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Destination


class DestinationPageTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(
            name="Test Coast",
            category="Beach",
            description="A test destination description.",
            location="Kanyakumari",
            latitude="8.080000",
            longitude="77.550000",
            visiting_hours="9 AM to 5 PM",
            best_time="Winter",
            entry_fee="Free",
            budget_level="Budget",
        )

    def test_home_and_explore_render_database_destinations(self):
        home_response = self.client.get(reverse("home"))
        explore_response = self.client.get(reverse("explore"))

        self.assertEqual(home_response.status_code, 200)
        self.assertContains(home_response, self.destination.name)
        self.assertEqual(explore_response.status_code, 200)
        self.assertContains(explore_response, self.destination.name)
        self.assertContains(explore_response, 'data-category="Beach"')
        self.assertContains(explore_response, "Budget budget")

    def test_destination_detail_shows_details_and_external_map(self):
        response = self.client.get(
            reverse("destination_detail", args=[self.destination.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.destination.description)
        self.assertContains(response, self.destination.visiting_hours)
        self.assertContains(response, "Open in Google Maps")
        self.assertContains(response, 'class="map-frame"')
        self.assertContains(response, "Hotels")

    def test_destination_without_coordinates_has_search_fallback(self):
        destination = Destination.objects.create(
            name="Unlocated Place",
            category="Nature",
            description="Coordinates are not available.",
            location="Kanyakumari",
            visiting_hours="Daytime",
            best_time="Winter",
            entry_fee="Free",
            budget_level="Budget",
        )

        response = self.client.get(
            reverse("destination_detail", args=[destination.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Map preview unavailable")
        self.assertNotContains(response, 'class="map-frame"')

    def test_login_and_registration_pages_render(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("register")).status_code, 200)

    def test_profile_requires_authentication_and_renders_for_owner(self):
        profile_url = reverse("profile")
        self.assertEqual(self.client.get(profile_url).status_code, 302)

        user = User.objects.create_user(username="traveler", password="safe-test-password")
        self.client.force_login(user)
        response = self.client.get(profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "traveler")

    def test_shared_layout_pages_render_for_their_expected_audience(self):
        self.assertEqual(self.client.get(reverse("about")).status_code, 200)
        self.assertEqual(self.client.get(reverse("safety")).status_code, 200)
        self.assertEqual(self.client.get(reverse("feedback")).status_code, 302)
        self.assertEqual(self.client.get(reverse("notifications")).status_code, 302)

        user = User.objects.create_user(username="page-user", password="safe-test-password")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("feedback")).status_code, 200)
        self.assertEqual(self.client.get(reverse("notifications")).status_code, 200)
        self.assertEqual(self.client.get(reverse("edit_profile")).status_code, 200)
