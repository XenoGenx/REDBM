from datetime import date
from functools import wraps
import secrets

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .constants import DEPARTMENTS
from .forms import CommentForm, LogForm, NoticeForm, PersonForm, PresidentLoginForm
from .image_utils import prepare_image
from .models import Attendance, AttendanceEntry, Comment, Log, LogPhoto, Notice, Person


def department_data(slug):
    if slug not in DEPARTMENTS:
        raise Http404
    return {'slug': slug, **DEPARTMENTS[slug]}


def notices_for(slug):
    return Notice.objects.filter(Q(recipient='all') | Q(recipient=slug))


def save_prepared_photos(log, uploads):
    prepared = [prepare_image(upload) for upload in uploads]
    for name, content in prepared:
        photo = LogPhoto(log=log)
        photo.image.save(name, content, save=True)


def home(request):
    return render(request, 'updates/home.html')


def department_home(request, slug):
    department = department_data(slug)
    today = timezone.localdate()
    event_date = date.fromisoformat(settings.EVENT_DATE)
    logs = Log.objects.filter(department=slug).prefetch_related('photos')[:5]
    context = {
        'department': department,
        'today': today,
        'has_today_log': Log.objects.filter(department=slug, date=today).exists(),
        'latest_logs': logs,
        'notices': notices_for(slug)[:5],
        'days_until_event': (event_date - today).days,
        'event_date': event_date,
    }
    return render(request, 'updates/department_home.html', context)


def log_list(request, slug):
    department = department_data(slug)
    logs = Log.objects.filter(department=slug).prefetch_related('photos', 'comments')
    return render(request, 'updates/log_list.html', {'department': department, 'logs': logs, 'today': timezone.localdate()})


def log_create(request, slug):
    department = department_data(slug)
    form = LogForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            prepared = [prepare_image(upload) for upload in request.FILES.getlist('photos')]
        except ValidationError as error:
            form.add_error(None, error)
        else:
            log = form.save(commit=False)
            log.department = slug
            log.date = timezone.localdate()
            log.save()
            for name, content in prepared:
                photo = LogPhoto(log=log)
                photo.image.save(name, content, save=True)
            messages.success(request, 'บันทึกเรียบร้อย')
            return redirect('department_home', slug=slug)
    return render(request, 'updates/log_form.html', {'department': department, 'form': form, 'page_title': 'เขียนบันทึกวันนี้'})


def log_edit(request, slug, pk):
    department = department_data(slug)
    log = get_object_or_404(Log, pk=pk, department=slug)
    if log.date != timezone.localdate():
        raise Http404
    form = LogForm(request.POST or None, instance=log)
    if request.method == 'POST' and form.is_valid():
        try:
            prepared = [prepare_image(upload) for upload in request.FILES.getlist('photos')]
        except ValidationError as error:
            form.add_error(None, error)
        else:
            form.save()
            for name, content in prepared:
                photo = LogPhoto(log=log)
                photo.image.save(name, content, save=True)
            messages.success(request, 'แก้ไขบันทึกเรียบร้อย')
            return redirect('department_home', slug=slug)
    return render(request, 'updates/log_form.html', {'department': department, 'form': form, 'page_title': 'แก้ไขบันทึกวันนี้', 'log': log})


def log_detail(request, slug, pk):
    department = department_data(slug)
    log = get_object_or_404(Log.objects.prefetch_related('photos', 'comments'), pk=pk, department=slug)
    form = CommentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.log = log
        if request.session.get('president_authenticated'):
            comment.author_name = 'ประธานสี'
        comment.save()
        messages.success(request, 'ส่งความคิดเห็นแล้ว')
        return redirect('log_detail', slug=slug, pk=log.pk)
    return render(request, 'updates/log_detail.html', {'department': department, 'log': log, 'form': form, 'today': timezone.localdate()})


def mark_resolved(request, slug, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    department_data(slug)
    log = get_object_or_404(Log, pk=pk, department=slug)
    log.is_resolved = True
    log.save(update_fields=['is_resolved'])
    messages.success(request, 'ทำเครื่องหมายว่าแก้ปัญหาแล้ว')
    return redirect('log_detail', slug=slug, pk=pk)


def notice_list(request, slug):
    department = department_data(slug)
    return render(request, 'updates/notice_list.html', {'department': department, 'notices': notices_for(slug)})


def selected_date(request):
    value = parse_date(request.GET.get('date', ''))
    return value or timezone.localdate()


def attendance(request, slug):
    department = department_data(slug)
    day = parse_date(request.POST.get('date', '')) if request.method == 'POST' else selected_date(request)
    if day is None:
        day = timezone.localdate()
        messages.error(request, 'กรุณาเลือกวันที่ให้ถูกต้อง')
    people = list(Person.objects.filter(department=slug))
    record = Attendance.objects.filter(department=slug, date=day).first()

    if request.method == 'POST' and request.POST.get('action') == 'add_person':
        person_form = PersonForm(request.POST)
        if person_form.is_valid():
            person = person_form.save(commit=False)
            person.department = slug
            person.save()
            messages.success(request, f'เพิ่มชื่อ {person.name} แล้ว')
            return redirect(f'{request.path}?date={day.isoformat()}')
    else:
        person_form = PersonForm()

    if request.method == 'POST' and request.POST.get('action') == 'save_attendance':
        try:
            prepared_evidence = prepare_image(request.FILES['evidence']) if request.FILES.get('evidence') else None
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            record, _ = Attendance.objects.get_or_create(department=slug, date=day)
            if prepared_evidence:
                name, content = prepared_evidence
                if record.evidence:
                    record.evidence.delete(save=False)
                record.evidence.save(name, content, save=True)
            valid_statuses = {choice[0] for choice in AttendanceEntry.Status.choices}
            for person in people:
                status = request.POST.get(f'person_{person.pk}', AttendanceEntry.Status.PRESENT)
                if status not in valid_statuses:
                    status = AttendanceEntry.Status.PRESENT
                AttendanceEntry.objects.update_or_create(
                    attendance=record,
                    person=person,
                    defaults={'status': status},
                )
            messages.success(request, f'บันทึกเช็คชื่อวันที่ {day.day}/{day.month}/{day.year + 543} แล้ว')
            return redirect(f'{request.path}?date={day.isoformat()}')

    statuses = {}
    if record:
        statuses = {entry.person_id: entry.status for entry in record.entries.all()}
    for person in people:
        person.attendance_status = statuses.get(person.pk, AttendanceEntry.Status.PRESENT)
    return render(request, 'updates/attendance.html', {
        'department': department,
        'day': day,
        'people': people,
        'statuses': statuses,
        'record': record,
        'person_form': person_form,
    })


def attendance_summary(request, slug):
    department = department_data(slug)
    people = Person.objects.filter(department=slug).annotate(
        present_days=Count('attendance_entries', filter=Q(attendance_entries__status=AttendanceEntry.Status.PRESENT)),
        absent_days=Count('attendance_entries', filter=Q(attendance_entries__status=AttendanceEntry.Status.ABSENT)),
        leave_days=Count('attendance_entries', filter=Q(attendance_entries__status=AttendanceEntry.Status.LEAVE)),
    )
    return render(request, 'updates/attendance_summary.html', {'department': department, 'people': people})


def person_add(request, slug):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    department = department_data(slug)
    form = PersonForm(request.POST)
    if form.is_valid():
        person = form.save(commit=False)
        person.department = slug
        person.save()
        messages.success(request, f'เพิ่มชื่อ {person.name} แล้ว')
    else:
        messages.error(request, 'กรุณาตรวจสอบชื่อที่กรอก')
    return redirect('attendance', slug=department['slug'])


def president_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.session.get('president_authenticated'):
            return redirect('president_login')
        return view_func(request, *args, **kwargs)
    return wrapped


def president_login(request):
    if request.session.get('president_authenticated'):
        return redirect('president_dashboard')
    form = PresidentLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        submitted = form.cleaned_data['password']
        configured = settings.PRESIDENT_PASSWORD
        if configured and secrets.compare_digest(submitted.encode('utf-8'), configured.encode('utf-8')):
            request.session.cycle_key()
            request.session['president_authenticated'] = True
            messages.success(request, 'เข้าสู่ระบบประธานสีแล้ว')
            return redirect('president_dashboard')
        form.add_error('password', 'รหัสผิด ใส่อีกครั้ง')
    return render(request, 'updates/president_login.html', {'form': form})


@president_required
def president_logout(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    request.session.flush()
    messages.success(request, 'ออกจากระบบแล้ว')
    return redirect('home')


@president_required
def president_dashboard(request):
    today = timezone.localdate()
    department_cards = []
    for slug, data in DEPARTMENTS.items():
        latest_log = Log.objects.filter(department=slug).first()
        attendance_record = Attendance.objects.filter(department=slug, date=today).first()
        counts = {status: 0 for status, _ in AttendanceEntry.Status.choices}
        if attendance_record:
            counts.update({item['status']: item['total'] for item in attendance_record.entries.values('status').annotate(total=Count('id'))})
        department_cards.append({
            'slug': slug,
            **data,
            'has_today_log': Log.objects.filter(department=slug, date=today).exists(),
            'latest_log': latest_log,
            'counts': counts,
        })
    urgent_logs = Log.objects.filter(status=Log.Status.URGENT, is_resolved=False).select_related().order_by('-date', '-created_at')
    issue_logs = Log.objects.exclude(issue='').order_by('-date', '-created_at')[:10]
    people = Person.objects.all()
    return render(request, 'updates/president_dashboard.html', {
        'department_cards': department_cards,
        'urgent_logs': urgent_logs,
        'issue_logs': issue_logs,
        'people': people,
        'notices': Notice.objects.all()[:5],
        'today': today,
    })


@president_required
def president_notice_form(request, pk=None):
    notice = get_object_or_404(Notice, pk=pk) if pk else None
    form = NoticeForm(request.POST or None, instance=notice)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'บันทึกประกาศ/งานเรียบร้อย')
        return redirect('president_dashboard')
    return render(request, 'updates/president_notice_form.html', {
        'form': form,
        'notice': notice,
        'page_title': 'แก้ไขประกาศ/งาน' if notice else 'โพสต์ประกาศ/มอบหมายงาน',
    })


@president_required
def president_notice_delete(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    notice = get_object_or_404(Notice, pk=pk)
    notice.delete()
    messages.success(request, 'ลบประกาศ/งานแล้ว')
    return redirect('president_dashboard')


@president_required
def president_log_delete(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    log = get_object_or_404(Log, pk=pk)
    for photo in log.photos.all():
        photo.image.delete(save=False)
    log.delete()
    messages.success(request, 'ลบบันทึกแล้ว')
    return redirect('president_dashboard')


@president_required
def president_comment_delete(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    comment = get_object_or_404(Comment, pk=pk)
    slug = comment.log.department
    log_pk = comment.log_id
    comment.delete()
    messages.success(request, 'ลบความคิดเห็นแล้ว')
    return redirect('log_detail', slug=slug, pk=log_pk)


@president_required
def president_photo_delete(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    photo = get_object_or_404(LogPhoto, pk=pk)
    slug = photo.log.department
    log_pk = photo.log_id
    photo.image.delete(save=False)
    photo.delete()
    messages.success(request, 'ลบรูปแล้ว')
    return redirect('log_detail', slug=slug, pk=log_pk)


@president_required
def president_person_delete(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    person = get_object_or_404(Person, pk=pk)
    slug = person.department
    person.delete()
    messages.success(request, 'ลบรายชื่อแล้ว')
    return redirect('president_dashboard')


def robots_txt(request):
    return render(request, 'updates/robots.txt', content_type='text/plain')


def not_found(request, exception):
    return render(request, '404.html', status=404)