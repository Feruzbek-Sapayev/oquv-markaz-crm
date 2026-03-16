from rest_framework.routers import DefaultRouter
from accounts.api_views import UserViewSet
from students.api_views import StudentViewSet
from teachers.api_views import TeacherViewSet
from courses.api_views import CourseViewSet, GroupViewSet, EnrollmentViewSet, ExamViewSet
from payments.api_views import PaymentViewSet
from attendance.api_views import AttendanceSessionViewSet, AttendanceViewSet
from notifications.api_views import NotificationViewSet

router = DefaultRouter()

router.register(r'users', UserViewSet)
router.register(r'students', StudentViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'exams', ExamViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'attendance-sessions', AttendanceSessionViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = router.urls
