from django.shortcuts import render
from tourism.models import Destination
from .models import TripPlan


def planner_home(request):

    all_destinations = Destination.objects.all()

    if request.method == "POST":
        raw_days = request.POST.get("days", "1")
        category = request.POST.get("category", "All")
        trip_type = request.POST.get("trip_type", "Family")
        budget = request.POST.get("budget", "Budget")
        selected_days = raw_days

        valid_categories = {"All", "Heritage", "Beach", "Nature", "Religious", "Adventure"}
        valid_trip_types = {"Family", "Couple", "Solo", "Friends"}
        valid_budgets = {"Budget", "Moderate", "Luxury"}

        try:
            days = int(raw_days)
        except (TypeError, ValueError):
            days = None

        planner_error = None
        if days not in range(1, 6):
            planner_error = "Choose a trip length between 1 and 5 days."
        elif category not in valid_categories:
            planner_error = "Choose one of the listed interests."
        elif trip_type not in valid_trip_types:
            planner_error = "Choose one of the listed travel groups."
        elif budget not in valid_budgets:
            planner_error = "Choose one of the listed budget preferences."

        if planner_error:
            return render(
                request,
                "planner.html",
                {
                    "destinations": all_destinations,
                    "selected_days": selected_days,
                    "selected_category": category,
                    "selected_trip_type": trip_type,
                    "selected_budget": budget,
                    "planner_error": planner_error,
                }
            )

        # Save trip for logged-in user
        if request.user.is_authenticated:
            TripPlan.objects.create(
                user=request.user,
                days=days,
                category=category,
                trip_type=trip_type,
                budget=budget
            )

        destinations = all_destinations

        # Category filter
        if category != "All":
            destinations = destinations.filter(
                category=category
            )

        # Budget filter
        if budget == "Budget":

            destinations = destinations.filter(
                budget_level__in=["Budget"]
            )

        elif budget == "Moderate":

            destinations = destinations.filter(
                budget_level__in=[
                    "Budget",
                    "Moderate"
                ]
            )

        elif budget == "Luxury":

            destinations = destinations.filter(
                budget_level__in=[
                    "Budget",
                    "Moderate",
                    "Luxury"
                ]
            )

        # Trip type preference
        if trip_type == "Family":

            preferred = [
                "Nature",
                "Heritage",
                "Religious"
            ]

        elif trip_type == "Couple":

            preferred = [
                "Beach",
                "Heritage",
                "Nature"
            ]

        elif trip_type == "Solo":

            preferred = [
                "Heritage",
                "Nature",
                "Adventure"
            ]

        else:

            preferred = [
                "Beach",
                "Nature",
                "Adventure"
            ]

        # Arrange destinations
        if category == "All":

            ordered = []

            for preferred_category in preferred:

                for destination in destinations:

                    if destination.category == preferred_category:
                        ordered.append(destination)

            for destination in destinations:

                if destination not in ordered:
                    ordered.append(destination)

            destinations = ordered

        else:

            destinations = list(destinations)

        # Create itinerary
        itinerary = []

        for i in range(days):

            day_destinations = destinations[i::days]

            itinerary.append({
                "day": i + 1,
                "destinations": day_destinations
            })

        return render(
            request,
            "planner.html",
            {
                "destinations": all_destinations,
                "itinerary": itinerary,
                "selected_days": days,
                "selected_category": category,
                "selected_trip_type": trip_type,
                "selected_budget": budget,
            }
        )

    return render(
        request,
        "planner.html",
        {
            "destinations": all_destinations
        }
    )