from django.shortcuts import redirect, render, get_object_or_404
from .models import Destination, Favorite, Notification,Review
from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import Profile

def home(request):

    destinations = Destination.objects.all()
    hero_destination = destinations.exclude(image="").first()

    unread_count = 0
    profile = None

    if request.user.is_authenticated:

        profile, created = Profile.objects.get_or_create(
            user=request.user
        )
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

    return render(request, "home.html", {
        "destinations": destinations,
        "hero_destination": hero_destination,
        "unread_count": unread_count,
        "profile": profile
    })


def destination_detail(request, pk):

    destination = get_object_or_404(
        Destination,
        pk=pk
    )

    nearby_destinations = Destination.objects.exclude(
        pk=pk
    )[:4]


    return render(request, "destination_detail.html", {
        "destination": destination,
        "nearby_destinations": nearby_destinations,
        
    })

def explore_destinations(request):
    destinations = Destination.objects.all()

    return render(request, "explore.html", {
        "destinations": destinations
    })

def notifications(request):

    if not request.user.is_authenticated:
        return redirect("/login/")

    notification_list = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(request, "notifications.html", {
        "notifications": notification_list
    })


def mark_notification_read(request, pk):

    if not request.user.is_authenticated:
        return redirect("/login/")

    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user
    )

    notification.is_read = True
    notification.save()

    return redirect("notifications")

def feedback_view(request):
    if not request.user.is_authenticated:
        return redirect("/login/")

    if request.method == "POST":
        rating = int(request.POST.get("rating", 5))
        comment = request.POST.get("comment", "").strip()

        if 1 <= rating <= 5 and comment:
            Review.objects.create(
                user=request.user,
                rating=rating,
                comment=comment
            )

        return redirect("feedback")

    reviews = Review.objects.select_related("user").order_by("-created_at")

    return render(request, "feedback.html", {
        "reviews": reviews
    })

def safety_tips(request):
    return render(request, "safety.html")

def about(request):
    return render(request, "about.html")