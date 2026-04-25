from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Classroom, Enrollment, Test, Question, Answer, testTaken
from ..forms import UserForm
from django.contrib.auth.forms import PasswordChangeForm
from ..decorators import teacher_required
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError # Added for specific error handling

def home(request):
    return render(request, 'classroom/home.html')

@login_required(login_url='login')
def dashboard(request):
    colors = ['blue', 'orange', 'green', 'red', 'purple', 'pink']
    
    if request.user.is_staff:
        rooms = Classroom.objects.filter(owner=request.user).values()
    else:
        enroll = list(Enrollment.objects.filter(student=request.user).values('room_id'))
        d = [e['room_id'] for e in enroll]
        rooms = Classroom.objects.filter(pk__in=d).values()

    rooms = list(rooms)
    for i in range(len(rooms)):
        rooms[i]["color"] = colors[i % 6]
        rooms[i]["delay"] = (i + 2) * 100  

    return render(request, 'classroom/dashboard.html', {'rooms': rooms})

@login_required(login_url='login')
def view_class(request, class_id):
    tests_list = Test.objects.filter(belongs=class_id).order_by('-create_time')

    search = request.GET.get('search')
    if search:
        tests_list = tests_list.filter(name__icontains=search)

    paginator = Paginator(tests_list, 5)
    page = request.GET.get('page', 1)

    try:
        tests = paginator.page(page)
    except PageNotAnInteger:
        tests = paginator.page(1)
    except EmptyPage:
        tests = paginator.page(paginator.num_pages)

    if not request.user.is_staff:
        for t in tests:
            if testTaken.objects.filter(student=request.user, test=t).exists():
                t.status = "done"
            elif (t.start_time is None or t.start_time < timezone.now()) and \
                 (t.end_time is None or t.end_time > timezone.now()):
                t.status = "Assigned"
            elif t.start_time and t.start_time > timezone.now():
                t.status = "not"
            else:
                t.status = "late"

    room = get_object_or_404(Classroom, id=class_id)
    return render(request, "classroom/view_class.html", {'tests': tests, 'room': room})

@login_required(login_url='login')
def people(request, class_id):
    room = get_object_or_404(Classroom, id=class_id)
    teacher = room.owner
    enrollments = Enrollment.objects.filter(room=room).select_related('student')
    students = [e.student for e in enrollments]
    
    return render(request, "classroom/people.html", {'teacher': teacher, 'student': students})

@login_required(login_url='login')
def profile(request):
    if request.method == "POST":
        form = UserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'{request.user} Modified.')
            return redirect('dashboard')
        else:
            messages.error(request, form.errors)
    else:
        form = UserForm(instance=request.user)
    return render(request, 'classroom/profile.html', {'form': form})

@login_required(login_url='login')
def password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, form.errors) 
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'classroom/password.html', {'form': form})

def signup(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_staff_checked = request.POST.get('is_staff') == 'on'

        # Critical Check: Prevent duplicate usernames (emails)
        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'classroom/login.html')

        try:
            user = User.objects.create_user(
                first_name=name, 
                email=email, 
                username=email, 
                password=password, 
                is_staff=is_staff_checked
            )
            messages.success(request, 'Account created successfully. Please login.')
            return redirect('login')

        except IntegrityError:
            messages.error(request, 'An error occurred during registration. Please try again.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'classroom/login.html')

def login(request):
    if request.method == "POST": 
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(username=email, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username or password incorrect')
    return render(request, 'classroom/login.html')

def logout(request):
    auth_logout(request)
    return redirect('home')