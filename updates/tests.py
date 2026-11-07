from datetime import date
from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .image_utils import prepare_image
from .models import Attendance, AttendanceEntry, Comment, Log, Notice, Person


class PublicPagesTests(TestCase):
	def test_public_pages_render(self):
		paths = [
			'/',
			'/stan/',
			'/stan/logs/',
			'/stan/logs/new/',
			'/stan/attendance/',
			'/stan/attendance/summary/',
			'/stan/notices/',
			'/president/login/',
			'/robots.txt',
		]
		for path in paths:
			with self.subTest(path=path):
				response = self.client.get(path)
				self.assertEqual(response.status_code, 200)
				if path != '/robots.txt':
					self.assertContains(response, 'noindex')

	@override_settings(DEBUG=False)
	def test_unknown_department_uses_thai_404(self):
		response = self.client.get('/unknown/')
		self.assertEqual(response.status_code, 404)
		self.assertContains(response, 'ไม่พบหน้านี้', status_code=404)


class LogWorkflowTests(TestCase):
	def test_detail_shows_reported_issue_and_uploaded_photo(self):
		image_buffer = BytesIO()
		Image.new('RGB', (32, 24), color='red').save(image_buffer, format='PNG')
		photo = SimpleUploadedFile('issue.png', image_buffer.getvalue(), content_type='image/png')

		with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			response = self.client.post(reverse('log_create', args=['stan']), {
				'author_name': 'หัวหน้าทีม',
				'work_done': 'ตรวจอุปกรณ์',
				'progress': '60',
				'issue': 'ไมโครโฟนมีปัญหา',
				'status': Log.Status.ISSUE,
				'photos': [photo],
			})
			log = Log.objects.get()
			self.assertRedirects(response, reverse('department_home', args=['stan']))

			response = self.client.get(reverse('log_detail', args=['stan', log.pk]))

			self.assertContains(response, 'ไมโครโฟนมีปัญหา')
			self.assertContains(response, 'รูปประกอบบันทึก')
			self.assertContains(response, 'media/logs/')

	def test_create_comment_and_today_edit(self):
		response = self.client.post(reverse('log_create', args=['stan']), {
			'author_name': 'ทีมแสตน',
			'work_done': 'ซ้อมเชียร์และจัดพื้นที่',
			'progress': '65',
			'issue': '',
			'status': Log.Status.NORMAL,
		})
		log = Log.objects.get()
		self.assertRedirects(response, reverse('department_home', args=['stan']))
		self.assertEqual(log.date, date.today())

		response = self.client.post(reverse('log_detail', args=['stan', log.pk]), {
			'author_name': 'ผู้ช่วย',
			'message': 'รับทราบ ขอบคุณ',
		})
		self.assertRedirects(response, reverse('log_detail', args=['stan', log.pk]))
		self.assertEqual(Comment.objects.get().message, 'รับทราบ ขอบคุณ')

		log.date = date(2020, 1, 1)
		log.save(update_fields=['date'])
		response = self.client.get(reverse('log_edit', args=['stan', log.pk]))
		self.assertEqual(response.status_code, 404)


class AttendanceWorkflowTests(TestCase):
	def test_attendance_is_saved_for_department_people(self):
		person = Person.objects.create(name='น้องแดง', department='stan')
		today = date.today().isoformat()
		response = self.client.post(reverse('attendance', args=['stan']), {
			'action': 'save_attendance',
			'date': today,
			f'person_{person.pk}': AttendanceEntry.Status.LEAVE,
		})
		self.assertEqual(response.status_code, 302)
		record = Attendance.objects.get(department='stan')
		self.assertEqual(record.date, date.today())
		self.assertEqual(record.entries.get(person=person).status, AttendanceEntry.Status.LEAVE)


@override_settings(PRESIDENT_PASSWORD='test-president-password')
class PresidentAccessTests(TestCase):
	def test_dashboard_requires_login_and_password_works(self):
		response = self.client.get(reverse('president_dashboard'))
		self.assertRedirects(response, reverse('president_login'))

		response = self.client.post(reverse('president_login'), {'password': 'wrong'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'รหัสผิด ใส่อีกครั้ง')

		response = self.client.post(reverse('president_login'), {'password': 'รหัสผิดภาษาไทย'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'รหัสผิด ใส่อีกครั้ง')

		response = self.client.post(reverse('president_login'), {'password': 'test-president-password'})
		self.assertRedirects(response, reverse('president_dashboard'))
		self.assertEqual(self.client.get(reverse('president_dashboard')).status_code, 200)

	def test_dashboard_shows_issue_text_even_when_log_is_not_urgent(self):
		Log.objects.create(
			department='stan',
			author_name='หัวหน้าทีม',
			work_done='จัดเตรียมงาน',
			issue='อุปกรณ์เสียงมีปัญหา',
			progress=60,
			status=Log.Status.NORMAL,
		)
		self.client.post(reverse('president_login'), {'password': 'test-president-password'})

		response = self.client.get(reverse('president_dashboard'))

		self.assertContains(response, 'ปัญหาที่พบล่าสุด')
		self.assertContains(response, 'อุปกรณ์เสียงมีปัญหา')

	def test_president_sees_view_today_instead_of_edit_link(self):
		log = Log.objects.create(
			department='stan',
			author_name='หัวหน้าทีม',
			work_done='เตรียมงาน',
			progress=60,
			status=Log.Status.NORMAL,
		)
		log_list_url = reverse('log_list', args=['stan'])
		edit_url = reverse('log_edit', args=['stan', log.pk])

		regular_response = self.client.get(log_list_url)
		self.assertContains(regular_response, 'แก้ไขบันทึกวันนี้')

		self.client.post(reverse('president_login'), {'password': 'test-president-password'})
		president_response = self.client.get(log_list_url)
		self.assertContains(president_response, 'ดูบันทึกวันนี้')
		self.assertNotContains(president_response, edit_url)

		detail_response = self.client.get(reverse('log_detail', args=['stan', log.pk]))
		self.assertNotContains(detail_response, 'แก้ไขบันทึกวันนี้')

	def test_president_can_delete_person(self):
		person = Person.objects.create(name='ลบได้', department='sport')
		response = self.client.post(reverse('president_person_delete', args=[person.pk]))
		self.assertRedirects(response, reverse('president_login'))
		self.client.post(reverse('president_login'), {'password': 'test-president-password'})
		response = self.client.post(reverse('president_person_delete', args=[person.pk]))
		self.assertRedirects(response, reverse('president_dashboard'))
		self.assertFalse(Person.objects.filter(pk=person.pk).exists())


class ImageProcessingTests(TestCase):
	def test_image_is_rotated_resized_and_reencoded_without_exif(self):
		source = Image.new('RGB', (1800, 900), color='red')
		exif = Image.Exif()
		exif[274] = 6
		buffer = BytesIO()
		source.save(buffer, format='PNG', exif=exif)
		upload = SimpleUploadedFile('camera.png', buffer.getvalue(), content_type='image/png')

		name, content = prepare_image(upload)
		result = Image.open(content)
		self.assertTrue(name.endswith('.jpg'))
		self.assertEqual(result.format, 'JPEG')
		self.assertEqual(result.size, (800, 1600))
		self.assertEqual(len(result.getexif()), 0)
