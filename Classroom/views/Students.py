from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..decorators import student_required
from ..models import Classroom, Enrollment, Test, Question, Answer, testTaken
import datetime
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from sklearn.feature_extraction.text import TfidfTransformer, TfidfVectorizer
import nltk
import numpy as np

@login_required(login_url='login')
@student_required
def join_class(request):
    if request.method == "POST":
        code = request.POST['code']
        user = request.user

        try:
            room = Classroom.objects.get(code=code)
        except Classroom.DoesNotExist:
            messages.warning(request, "There's no such Classroom")
            return redirect('join_class')

        if Enrollment.objects.filter(room=room, student=user).exists():
            messages.info(request, f'You Already Enrolled {room}')
        else:
            Enrollment(room=room, student=user).save()
            messages.success(request, f'{room} Class Enrolled')

        return redirect('dashboard')

    return render(request, 'students/join_class.html')


@login_required(login_url='login')
@student_required
def attend_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)

    if testTaken.objects.filter(test=test, student=request.user).exists():
        return redirect('review_test', test_id=test.id)

    qns = Question.objects.filter(test=test_id)
    return render(request, 'students/attend_test.html', {'qns': qns, 'test': test})


@login_required(login_url='login')
@student_required
def submit_test(request, test_id):
    nltk.data.path.append('../../nltk_data/')
    lemmatizer = nltk.stem.WordNetLemmatizer()

    def LemTokens(tokens):
        return [lemmatizer.lemmatize(token) for token in tokens]

    def LemNormalize(text):
        tokens = nltk.word_tokenize(text)
        words = [w.lower() for w in tokens if w.isalnum()]
        return LemTokens(words)

    def cos_similarity(textlist):
        tfidf = TfidfVec.fit_transform(textlist)
        return (tfidf * tfidf.T).toarray()

    qns = Question.objects.filter(test=test_id)
    test = get_object_or_404(Test, id=test_id)
    student = request.user

    if testTaken.objects.filter(test=test, student=request.user).exists():
        return redirect('review_test', test_id=test.id)

    tt = testTaken(test=test, student=student, actual_score=0, ml_score=0)
    tt.save()

    for q in qns:
        ans_text = request.POST.get(str(q.id), "")
        ans = Answer(student=student, question=q, answer_text=ans_text)

        documents = [q.key, ans_text]
        TfidfVec = TfidfVectorizer(tokenizer=LemNormalize, stop_words='english')

        try:
            tf_matrix = cos_similarity(documents)
            score = tf_matrix[0][1] * q.max_score
        except Exception:
            score = 0

        mark = int(round(score))
        ans.actual_score = mark
        ans.ml_score = mark
        ans.save()
        tt.actual_score += mark
        tt.ml_score += mark

    tt.save()
    return redirect('view_class', class_id=test.belongs.id)


@login_required(login_url='login')
@student_required
def review_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    qns = Question.objects.filter(test=test_id)
    student = request.user
    ans = []
    tot = 0
    act = 0

    for q in qns:
        try:
            answer = Answer.objects.get(student=student, question=q)
        except Answer.DoesNotExist:
            continue

        ans.append({'qns': q, 'ans': answer})
        act += answer.actual_score
        tot += q.max_score

    mark = f"{act} / {tot}"
    return render(request, 'students/review_test.html', {'test': test, 'ans': ans, 'mark': mark})


@login_required(login_url='login')
@student_required
def assigned_test(request, class_id):
    tests = Test.objects.filter(belongs=class_id)

    active_tests = [t for t in tests if not testTaken.objects.filter(test=t, student=request.user).exists()
                    and (not t.start_time or t.start_time < timezone.now())
                    and (not t.end_time or t.end_time > timezone.now())]

    for t in active_tests:
        t.status = "Assigned"

    search = request.GET.get('search', "")
    if search:
        active_tests = Test.objects.filter(belongs=class_id, name__icontains=search).order_by('-create_time')

    paginator = Paginator(active_tests, 5)
    page = request.GET.get('page', 1)

    try:
        tests = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        tests = paginator.page(1)

    room = get_object_or_404(Classroom, id=class_id)
    return render(request, 'classroom/view_class.html', {'tests': tests, 'room': room})


@login_required(login_url='login')
@student_required
def missing_test(request, class_id):
    tests = Test.objects.filter(belongs=class_id)
    student = request.user

    missing = []
    for t in tests:
        if testTaken.objects.filter(test=t, student=student).exists():
            continue
        if t.start_time and t.start_time > timezone.now():
            t.status = "not"
        else:
            t.status = "late"
        missing.append(t)

    search = request.GET.get('search', "")
    if search:
        missing = Test.objects.filter(belongs=class_id, name__icontains=search).order_by('-create_time')

    paginator = Paginator(missing, 5)
    page = request.GET.get('page', 1)

    try:
        tests = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        tests = paginator.page(1)

    room = get_object_or_404(Classroom, id=class_id)
    return render(request, 'classroom/view_class.html', {'tests': tests, 'room': room})


@login_required(login_url='login')
@student_required
def done_test(request, class_id):
    taken_ids = testTaken.objects.filter(student=request.user).values_list("test", flat=True)
    tests = Test.objects.filter(pk__in=taken_ids, belongs=class_id)

    for t in tests:
        t.status = "done"

    search = request.GET.get('search', "")
    if search:
        tests = Test.objects.filter(belongs=class_id, name__icontains=search).order_by('-create_time')

    paginator = Paginator(tests, 5)
    page = request.GET.get('page', 1)

    try:
        tests = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        tests = paginator.page(1)

    room = get_object_or_404(Classroom, id=class_id)
    return render(request, 'classroom/view_class.html', {'tests': tests, 'room': room})
