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

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import numpy as np
import os

# --- NLTK Data Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NLTK_DATA_PATH = os.path.join(BASE_DIR, 'nltk_data')
if NLTK_DATA_PATH not in nltk.data.path:
    nltk.data.path.append(NLTK_DATA_PATH)

lemmatizer = nltk.stem.WordNetLemmatizer()

def LemTokens(tokens):
    return [lemmatizer.lemmatize(token) for token in tokens]

def LemNormalize(text):
    tokens = nltk.word_tokenize(text.lower())
    words = [w for w in tokens if w.isalnum()]
    return LemTokens(words)

@login_required(login_url='login')
@student_required
def join_class(request):
    if request.method == "POST":
        code = request.POST.get('code')
        try:
            room = Classroom.objects.get(code=code)
            if Enrollment.objects.filter(room=room, student=request.user).exists():
                messages.info(request, f'You are already enrolled in {room.name}')
            else:
                Enrollment.objects.create(room=room, student=request.user)
                messages.success(request, f'Successfully enrolled in {room.name}')
            return redirect('dashboard')
        except Classroom.DoesNotExist:
            messages.warning(request, "Invalid classroom code.")
    return render(request, 'students/join_class.html')

@login_required(login_url='login')
@student_required
def submit_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    student = request.user

    if testTaken.objects.filter(test=test, student=student).exists():
        return redirect('review_test', test_id=test.id)

    qns = Question.objects.filter(test=test)
    tt = testTaken.objects.create(test=test, student=student, actual_score=0, ml_score=0)

    # Capturing logical context with ngram_range (1, 2)
    # This captures word sequences like "not good" vs "good"
    tfidf_vec = TfidfVectorizer(tokenizer=LemNormalize, stop_words='english', ngram_range=(1, 2))

    for q in qns:
        ans_text = request.POST.get(str(q.id), "").strip()
        
        if not ans_text:
            mark = 0
        else:
            try:
                documents = [q.key, ans_text]
                tfidf_matrix = tfidf_vec.fit_transform(documents)
                
                # Cosine similarity captures semantic direction/thematic overlap
                sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
                score = float(sim_matrix[0][0]) * q.max_score
                
                # Length check: Penalty for answers too short to be logically complete
                len_ratio = len(ans_text.split()) / max(len(q.key.split()), 1)
                if len_ratio < 0.2:
                    score *= 0.6 
                
                mark = int(round(score))
            except Exception:
                mark = 0

        Answer.objects.create(
            student=student, question=q, answer_text=ans_text, 
            actual_score=mark, ml_score=mark
        )
        tt.actual_score += mark
        tt.ml_score += mark

    tt.save()
    return redirect('view_class', class_id=test.belongs.id)

@login_required(login_url='login')
@student_required
def review_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    qns = Question.objects.filter(test=test)
    student = request.user
    ans_list = []
    total_max, total_act = 0, 0
    for q in qns:
        answer = Answer.objects.filter(student=student, question=q).first()
        if answer:
            ans_list.append({'qns': q, 'ans': answer})
            total_act += answer.actual_score
        total_max += q.max_score
    mark = f"{total_act} / {total_max}"
    return render(request, 'students/review_test.html', {'test': test, 'ans': ans_list, 'mark': mark})

@login_required(login_url='login')
@student_required
def assigned_test(request, class_id):
    all_tests = Test.objects.filter(belongs=class_id)
    active_tests = [t for t in all_tests if not testTaken.objects.filter(test=t, student=request.user).exists()]
    paginator = Paginator(active_tests, 5)
    tests = paginator.get_page(request.GET.get('page', 1))
    room = get_object_or_404(Classroom, id=class_id)
    return render(request, 'classroom/view_class.html', {'tests': tests, 'room': room})

@login_required(login_url='login')
@student_required
def missing_test(request, class_id):
    all_tests = Test.objects.filter(belongs=class_id)
    missing = [t for t in all_tests if not testTaken.objects.filter(test=t, student=request.user).exists() and t.end_time and t.end_time < timezone.now()]
    paginator = Paginator(missing, 5)
    tests = paginator.get_page(request.GET.get('page', 1))
    room = get_object_or_404(Classroom, id=class_id)
    return render(request, 'classroom/view_class.html', {'tests': tests, 'room': room})

@login_required(login_url='login')
@student_required
def done_test(request, class_id):
    taken_ids = testTaken.objects.filter(student=request.user).values_list("test", flat=True)
    done_tests = Test.objects.filter(pk__in=taken_ids, belongs=class_id)
    paginator = Paginator(done_tests, 5)
    tests = paginator.get_page(request.GET.get('page', 1))
    room = get_object_or_404(Classroom, id=class_id)
    return render(request, 'classroom/view_class.html', {'tests': tests, 'room': room})

@login_required(login_url='login')
@student_required
def attend_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    if testTaken.objects.filter(test=test, student=request.user).exists():
        return redirect('review_test', test_id=test.id)
    qns = Question.objects.filter(test=test)
    return render(request, 'students/attend_test.html', {'qns': qns, 'test': test})