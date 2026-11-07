from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('president/', views.president_dashboard, name='president_dashboard'),
    path('president/login/', views.president_login, name='president_login'),
    path('president/logout/', views.president_logout, name='president_logout'),
    path('president/notices/new/', views.president_notice_form, name='president_notice_new'),
    path('president/notices/<int:pk>/edit/', views.president_notice_form, name='president_notice_edit'),
    path('president/notices/<int:pk>/delete/', views.president_notice_delete, name='president_notice_delete'),
    path('president/logs/<int:pk>/delete/', views.president_log_delete, name='president_log_delete'),
    path('president/comments/<int:pk>/delete/', views.president_comment_delete, name='president_comment_delete'),
    path('president/photos/<int:pk>/delete/', views.president_photo_delete, name='president_photo_delete'),
    path('president/people/<int:pk>/delete/', views.president_person_delete, name='president_person_delete'),
    path('<slug:slug>/', views.department_home, name='department_home'),
    path('<slug:slug>/logs/', views.log_list, name='log_list'),
    path('<slug:slug>/logs/new/', views.log_create, name='log_create'),
    path('<slug:slug>/logs/<int:pk>/', views.log_detail, name='log_detail'),
    path('<slug:slug>/logs/<int:pk>/edit/', views.log_edit, name='log_edit'),
    path('<slug:slug>/logs/<int:pk>/resolved/', views.mark_resolved, name='mark_resolved'),
    path('<slug:slug>/attendance/', views.attendance, name='attendance'),
    path('<slug:slug>/attendance/summary/', views.attendance_summary, name='attendance_summary'),
    path('<slug:slug>/people/add/', views.person_add, name='person_add'),
    path('<slug:slug>/notices/', views.notice_list, name='notice_list'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]