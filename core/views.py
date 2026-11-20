from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import Item, Claim
from .forms import UserRegisterForm, ItemReportForm, ClaimVerificationForm

def staff_required(view_func):
    """Decorator to restrict view to staff/superusers only."""
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='login')(view_func)


def home_view(request):
    """Browse lost and found items with search, category, location, and type filters."""
    items = Item.objects.select_related('reported_by').all()

    # Keyword search (title, description, location)
    query = request.GET.get('q', '').strip()
    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )

    # Category filter
    category = request.GET.get('category', '').strip()
    if category:
        items = items.filter(category=category)

    # Report type filter (LOST / FOUND)
    item_type = request.GET.get('type', '').strip().upper()
    if item_type in ['LOST', 'FOUND']:
        items = items.filter(item_type=item_type)

    # Status filter
    status = request.GET.get('status', '').strip().upper()
    if status in ['OPEN', 'CLAIMED', 'RETURNED']:
        items = items.filter(status=status)

    # Location search/filter
    location_query = request.GET.get('location', '').strip()
    if location_query:
        items = items.filter(location__icontains=location_query)

    # Distinct locations for filter dropdown
    locations = Item.objects.values_list('location', flat=True).distinct()[:15]

    # Pagination
    paginator = Paginator(items, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Quick counters
    open_lost_count = Item.objects.filter(item_type='LOST', status='OPEN').count()
    open_found_count = Item.objects.filter(item_type='FOUND', status='OPEN').count()
    returned_count = Item.objects.filter(status='RETURNED').count()

    context = {
        'page_obj': page_obj,
        'categories': Item.CATEGORY_CHOICES,
        'locations': locations,
        'selected_q': query,
        'selected_category': category,
        'selected_type': item_type,
        'selected_status': status,
        'open_lost_count': open_lost_count,
        'open_found_count': open_found_count,
        'returned_count': returned_count,
    }
    return render(request, 'home.html', context)


def item_detail_view(request, pk):
    """View detailed information about a single reported item."""
    item = get_object_or_404(Item.objects.select_related('reported_by'), pk=pk)

    user_has_claimed = False
    user_claim = None
    if request.user.is_authenticated:
        user_claim = Claim.objects.filter(item=item, claimant=request.user).first()
        if user_claim:
            user_has_claimed = True

    can_claim = (
        request.user.is_authenticated and
        item.item_type == 'FOUND' and
        item.status == 'OPEN' and
        item.reported_by != request.user and
        not user_has_claimed
    )

    claims_list = None
    if request.user.is_staff:
        claims_list = item.claims.select_related('claimant').all()

    context = {
        'item': item,
        'can_claim': can_claim,
        'user_has_claimed': user_has_claimed,
        'user_claim': user_claim,
        'claims_list': claims_list,
    }
    return render(request, 'item_detail.html', context)


@login_required
def report_item_view(request):
    """Report a new lost or found item."""
    if request.method == 'POST':
        form = ItemReportForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(user=request.user)
            messages.success(
                request,
                f"Successfully reported '{item.title}' as {item.get_item_type_display()}."
            )
            return redirect('item_detail', pk=item.pk)
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        initial_type = request.GET.get('type', 'LOST').upper()
        if initial_type not in ['LOST', 'FOUND']:
            initial_type = 'LOST'
        form = ItemReportForm(initial={'item_type': initial_type})

    return render(request, 'report_item.html', {'form': form})


@login_required
def claim_item_view(request, pk):
    """Two-step cryptographic verification and claim submission for found items."""
    item = get_object_or_404(Item, pk=pk)

    # Validation: item must be FOUND and not returned
    if item.item_type != 'FOUND':
        messages.error(request, "Only found items can be claimed.")
        return redirect('item_detail', pk=item.pk)

    if item.status == 'RETURNED':
        messages.warning(request, "This item has already been returned to its owner.")
        return redirect('item_detail', pk=item.pk)

    # Validation: reporter cannot claim own item
    if item.reported_by == request.user:
        messages.error(request, "You cannot claim an item that you reported yourself.")
        return redirect('item_detail', pk=item.pk)

    # Validation: check for existing claim
    existing_claim = Claim.objects.filter(item=item, claimant=request.user).first()
    if existing_claim:
        messages.info(request, f"You have already submitted a claim for this item (Status: {existing_claim.get_status_display()}).")
        return redirect('item_detail', pk=item.pk)

    if request.method == 'POST':
        form = ClaimVerificationForm(request.POST)
        if form.is_valid():
            raw_answer = form.cleaned_data['verification_answer']
            claim_note = form.cleaned_data.get('claim_note', '')

            # Secure cryptographic comparison using check_password
            is_correct = item.check_verification_answer(raw_answer)

            if is_correct:
                # Create pending claim with passed verification
                Claim.objects.create(
                    item=item,
                    claimant=request.user,
                    status='PENDING',
                    verification_passed=True,
                    claim_note=claim_note
                )
                # Keep item in OPEN or mark CLAIMED
                item.status = 'CLAIMED'
                item.save()

                messages.success(
                    request,
                    "Verification successful! Your claim has been submitted to campus administration for final handover."
                )
                return redirect('my_items')
            else:
                messages.error(
                    request,
                    "The verification answer you submitted did not match. Please verify the unique detail or check the item description."
                )
    else:
        form = ClaimVerificationForm()

    context = {
        'item': item,
        'form': form,
    }
    return render(request, 'claim_item.html', context)


@login_required
def my_items_view(request):
    """Student portal showing reports filed by user and claims submitted."""
    my_reports = Item.objects.filter(reported_by=request.user).order_by('-created_at')
    my_claims = Claim.objects.filter(claimant=request.user).select_related('item').order_by('-created_at')

    context = {
        'my_reports': my_reports,
        'my_claims': my_claims,
    }
    return render(request, 'my_items.html', context)


@staff_required
def admin_dashboard_view(request):
    """Custom Administrator Dashboard: metrics, item moderation, and claim approvals."""
    total_lost = Item.objects.filter(item_type='LOST').count()
    total_found = Item.objects.filter(item_type='FOUND').count()
    pending_claims = Claim.objects.filter(status='PENDING').count()
    returned_items = Item.objects.filter(status='RETURNED').count()

    all_items = Item.objects.select_related('reported_by').order_by('-created_at')
    claims = Claim.objects.select_related('item', 'claimant').order_by('-created_at')

    context = {
        'total_lost': total_lost,
        'total_found': total_found,
        'pending_claims': pending_claims,
        'returned_items': returned_items,
        'all_items': all_items,
        'claims': claims,
    }
    return render(request, 'admin_dashboard.html', context)


@staff_required
def admin_claim_action_view(request, claim_id, action):
    """Handle administrative claim approvals or rejections."""
    claim = get_object_or_404(Claim, pk=claim_id)

    if action == 'approve':
        claim.status = 'APPROVED'
        claim.reviewed_at = timezone.now()
        claim.save()
        # Update associated item to RETURNED
        claim.item.status = 'RETURNED'
        claim.item.save()
        messages.success(request, f"Claim #{claim.id} for '{claim.item.title}' approved! Item marked as RETURNED.")
    elif action == 'reject':
        claim.status = 'REJECTED'
        claim.reviewed_at = timezone.now()
        claim.save()
        # Reset item status to OPEN if no other approved claims
        claim.item.status = 'OPEN'
        claim.item.save()
        messages.info(request, f"Claim #{claim.id} rejected. Item reopened for claims.")

    return redirect('admin_dashboard')


@staff_required
def admin_item_action_view(request, item_id, action):
    """Handle administrative item moderation: mark returned or delete."""
    item = get_object_or_404(Item, pk=item_id)

    if action == 'mark_returned':
        item.status = 'RETURNED'
        item.save()
        messages.success(request, f"Item '{item.title}' marked as RETURNED to owner.")
    elif action == 'delete':
        title = item.title
        item.delete()
        messages.warning(request, f"Report '{title}' removed permanently.")

    return redirect('admin_dashboard')


def register_view(request):
    """Register a new student account."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Campus Lost & Found, {user.username}!")
            return redirect('home')
    else:
        form = UserRegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """Student and Administrator login view."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Log out current user."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')
