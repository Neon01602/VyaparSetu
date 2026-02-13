# ==============================
# IMPORTS
# ==============================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse

from .forms import VendorSignupForm, InvestorSignupForm
from .models import CustomUser, VendorDocument, VendorProfile, Investment
from .utils import generate_qr


# ==============================
# AUTH HELPER
# ==============================
def authenticate_user(aadhaar, password, role):
    """
    Authenticate a user (vendor or investor) based on Aadhaar and role.
    """
    try:
        user = CustomUser.objects.get(
            aadhaar_pan=aadhaar,
            role=role
        )
        if user.check_password(password):
            return user
    except CustomUser.DoesNotExist:
        return None
    return None


# ==============================
# VENDOR AUTH
# ==============================
def vendor_auth(request):
    """
    Handle Vendor login and signup.
    """
    if request.method == "POST":

        # ---------- LOGIN ----------
        if "vendor_login" in request.POST:
            aadhaar = request.POST.get("login_aadhaar")
            password = request.POST.get("login_password")
            user = authenticate_user(aadhaar, password, "vendor")

            if user:
                login(request, user)
                return redirect("dashboard")
            messages.error(request, "Vendor not found.")

        # ---------- SIGNUP ----------
        elif "vendor_signup" in request.POST:
            name = request.POST.get("signup_name")
            phone = request.POST.get("signup_phone")
            email = request.POST.get("signup_email")
            aadhaar = request.POST.get("signup_aadhaar")
            password = request.POST.get("signup_password")

            # Basic validation
            if not name or not aadhaar or not password:
                messages.error(request, "All required fields must be filled.")
                return redirect("vendor_auth")

            if CustomUser.objects.filter(aadhaar_pan=aadhaar).exists():
                messages.error(request, "Vendor already exists.")
                return redirect("vendor_auth")

            # Create user
            user = CustomUser.objects.create_user(
                username=name,
                email=email,
                phone=phone,
                aadhaar_pan=aadhaar,
                password=password,
                role="vendor"
            )

            # ---------- MULTIPLE DOCUMENTS ----------
            titles = request.POST.getlist("doc_title[]")
            files = request.FILES.getlist("document[]")
            uploaded = False

            for title, file in zip(titles, files):
                if file:
                    VendorDocument.objects.create(vendor=user, title=title, file=file)
                    uploaded = True

            # Create vendor profile
            VendorProfile.objects.create(vendor=user, document_uploaded=uploaded)

            login(request, user)
            return redirect("dashboard")

    return render(request, "vendor_auth.html")


# ==============================
# INVESTOR AUTH
# ==============================
def investor_auth(request):
    """
    Handle Investor login and signup.
    """
    if request.method == "POST":

        # ---------- LOGIN ----------
        if "investor_login" in request.POST:
            aadhaar = request.POST.get("login_aadhaar")
            password = request.POST.get("login_password")
            user = authenticate_user(aadhaar, password, "investor")

            if user:
                login(request, user)
                return redirect("dashboard")
            messages.error(request, "Investor not found or wrong password.")

        # ---------- SIGNUP ----------
        elif "investor_signup" in request.POST:
            name = request.POST.get("signup_name")
            phone = request.POST.get("signup_phone")
            email = request.POST.get("signup_email")
            aadhaar = request.POST.get("signup_aadhaar")
            password = request.POST.get("signup_password")

            if not name or not aadhaar or not password:
                messages.error(request, "All required fields must be filled.")
                return redirect("investor")

            if CustomUser.objects.filter(aadhaar_pan=aadhaar).exists():
                messages.error(request, "User already exists. Please login.")
                return redirect("investor")

            # Create investor
            user = CustomUser.objects.create_user(
                username=name,
                email=email,
                phone=phone,
                aadhaar_pan=aadhaar,
                password=password,
                role="investor"
            )

            login(request, user)
            return redirect("dashboard")

    return render(request, "investor_auth.html")


# ==============================
# DASHBOARD
# ==============================

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("landing")

    # For vendors: fetch all investments made in their business
    vendor_investments = []
    if request.user.role == "vendor":
        vendor_investments = Investment.objects.filter(vendor=request.user).select_related("investor")

    return render(request, "dashboard.html", {
        "user": request.user,
        "vendor_investments": vendor_investments
    })


# ==============================
# LOGOUT
# ==============================
def logout_view(request):
    """
    Logout user and redirect to landing.
    """
    logout(request)
    return redirect("landing")


# ==============================
# LANDING PAGE
# ==============================
def landing(request):
    """
    Render landing page.
    """
    return render(request, "landing.html")


# ==============================
# VENDOR VERIFICATION
# ==============================
def vendor_verify(request, uid):
    """
    Verify vendor by matching first half of unique_id.
    """
    try:
        profile = VendorProfile.objects.select_related("vendor").get(
            unique_id__startswith=str(uid)[:16]
        )
        documents = VendorDocument.objects.filter(vendor=profile.vendor)
    except VendorProfile.DoesNotExist:
        return render(request, "vendor_invalid.html")

    return render(request, "vendor_verify.html", {
        "profile": profile,
        "documents": documents
    })


# ==============================
# INVESTOR INVESTMENTS
# ==============================
def investor_investments(request):
    """
    Show all vendors this investor has invested in.
    """
    if request.user.role != "investor":
        return render(request, "not_authorized.html")

    investments = Investment.objects.select_related("vendor").filter(investor=request.user)

    return render(request, "investor_investments.html", {"investments": investments})


# ==============================
# INVEST IN VENDOR
# ==============================
def invest_vendor(request, short_uid):
    """
    Investment page for a vendor using first half of UUID.
    """
    profile = get_object_or_404(VendorProfile.objects.select_related("vendor"),
                                unique_id__startswith=str(short_uid)[:16])
    vendor = profile.vendor

    if request.method == "POST":
        amount = request.POST.get("amount")
        if not amount:
            messages.error(request, "Please enter an investment amount.")
            return redirect(request.path)

        try:
            amount = float(amount)
        except ValueError:
            messages.error(request, "Invalid amount entered.")
            return redirect(request.path)

        if amount < 5000:
            messages.error(request, "Minimum investment is ₹5000.")
            return redirect(request.path)

        # Create Investment and optional PDF generation handled in models
        investment = Investment.objects.create(investor=request.user, vendor=vendor, amount=amount)

        messages.success(request, f"Successfully invested ₹{amount} in {vendor.username}!")
        return redirect("investor_investments")

    return render(request, "invest_vendor.html", {"profile": profile, "vendor": vendor})
