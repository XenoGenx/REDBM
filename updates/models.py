from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

from .constants import DEPARTMENT_CHOICES


class Log(models.Model):
	class Status(models.TextChoices):
		NORMAL = 'normal', 'ปกติ'
		ISSUE = 'issue', 'มีปัญหา'
		URGENT = 'urgent', 'ต้องช่วยด่วน'

	department = models.CharField('ฝ่าย', max_length=20, choices=DEPARTMENT_CHOICES)
	date = models.DateField('วันที่', default=timezone.localdate)
	author_name = models.CharField('ชื่อผู้เขียน', max_length=100)
	work_done = models.TextField('สิ่งที่ทำ')
	issue = models.TextField('ปัญหาที่พบ', blank=True)
	progress = models.PositiveSmallIntegerField(
		'ความคืบหน้า',
		default=0,
		validators=[MinValueValidator(0), MaxValueValidator(100)],
	)
	status = models.CharField('สถานะ', max_length=10, choices=Status.choices, default=Status.NORMAL)
	is_resolved = models.BooleanField('แก้ปัญหาแล้ว', default=False)
	created_at = models.DateTimeField('เวลาที่บันทึก', auto_now_add=True)

	class Meta:
		ordering = ['-date', '-created_at']
		verbose_name = 'บันทึกประจำวัน'
		verbose_name_plural = 'บันทึกประจำวัน'

	def __str__(self):
		return f'{self.get_department_display()} - {self.date} - {self.author_name}'


class LogPhoto(models.Model):
	log = models.ForeignKey(Log, on_delete=models.CASCADE, related_name='photos', verbose_name='บันทึก')
	image = models.ImageField('รูปภาพ', upload_to='logs/')
	uploaded_at = models.DateTimeField('เวลาอัปโหลด', auto_now_add=True)

	class Meta:
		verbose_name = 'รูปบันทึก'
		verbose_name_plural = 'รูปบันทึก'


class Comment(models.Model):
	log = models.ForeignKey(Log, on_delete=models.CASCADE, related_name='comments', verbose_name='บันทึก')
	author_name = models.CharField('ชื่อผู้คอมเมนต์', max_length=100)
	message = models.TextField('ข้อความ')
	created_at = models.DateTimeField('เวลา', auto_now_add=True)

	class Meta:
		ordering = ['created_at']
		verbose_name = 'ความคิดเห็น'
		verbose_name_plural = 'ความคิดเห็น'

	def __str__(self):
		return f'{self.author_name}: {self.message[:40]}'


class Person(models.Model):
	name = models.CharField('ชื่อ', max_length=100)
	department = models.CharField('ฝ่าย', max_length=20, choices=DEPARTMENT_CHOICES)

	class Meta:
		ordering = ['name']
		verbose_name = 'รายชื่อ'
		verbose_name_plural = 'รายชื่อ'

	def __str__(self):
		return f'{self.name} ({self.get_department_display()})'


class Attendance(models.Model):
	department = models.CharField('ฝ่าย', max_length=20, choices=DEPARTMENT_CHOICES)
	date = models.DateField('วันที่', default=timezone.localdate)
	evidence = models.ImageField('รูปหลักฐาน', upload_to='attendance/', blank=True)

	class Meta:
		ordering = ['-date', 'department']
		constraints = [
			models.UniqueConstraint(fields=['date', 'department'], name='unique_attendance_per_department_day'),
		]
		verbose_name = 'การเช็คชื่อ'
		verbose_name_plural = 'การเช็คชื่อ'

	def __str__(self):
		return f'{self.get_department_display()} - {self.date}'


class AttendanceEntry(models.Model):
	class Status(models.TextChoices):
		PRESENT = 'present', 'มา'
		ABSENT = 'absent', 'ขาด'
		LEAVE = 'leave', 'ลา'

	attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='entries', verbose_name='การเช็คชื่อ')
	person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='attendance_entries', verbose_name='รายชื่อ')
	status = models.CharField('สถานะ', max_length=10, choices=Status.choices, default=Status.PRESENT)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['attendance', 'person'], name='unique_person_per_attendance'),
		]
		verbose_name = 'รายการเช็คชื่อ'
		verbose_name_plural = 'รายการเช็คชื่อ'


class Notice(models.Model):
	class TaskStatus(models.TextChoices):
		TODO = 'todo', 'ยังไม่ทำ'
		IN_PROGRESS = 'in_progress', 'กำลังทำ'
		DONE = 'done', 'เสร็จ'

	title = models.CharField('หัวข้อ', max_length=200)
	content = models.TextField('เนื้อหา')
	recipient = models.CharField(
		'ส่งถึง',
		max_length=20,
		choices=[('all', 'ทุกฝ่าย'), *DEPARTMENT_CHOICES],
		default='all',
	)
	deadline = models.DateField('เดดไลน์', blank=True, null=True)
	task_status = models.CharField('สถานะงาน', max_length=20, choices=TaskStatus.choices, default=TaskStatus.TODO)
	created_at = models.DateTimeField('เวลาที่สร้าง', auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		verbose_name = 'ประกาศ/งาน'
		verbose_name_plural = 'ประกาศ/งาน'

	def __str__(self):
		return self.title
