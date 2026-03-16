from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import AttendanceSession, Attendance
from .serializers import AttendanceSessionSerializer, AttendanceSerializer
from students.models import Student
from courses.models import Group
import calendar
from datetime import date
from django.db.models import Count, Q

class AttendanceSessionViewSet(viewsets.ModelViewSet):
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['group', 'date']
    ordering_fields = ['date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def matrix(self, request):
        group_id = request.query_params.get('group')
        month = int(request.query_params.get('month', date.today().month))
        year = int(request.query_params.get('year', date.today().year))
        
        if not group_id:
            return Response({'error': 'Group is required'}, status=400)
            
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return Response({'error': 'Group not found'}, status=404)
            
        students = group.students.all().order_by('last_name', 'first_name')
        
        # Build month dates (only days group has lessons normally, simplified here to all month days)
        _, num_days = calendar.monthrange(year, month)
        all_dates = []
        today = date.today()
        
        # Simplified day names
        days_uz = ['DU', 'SE', 'CH', 'PA', 'JU', 'SH', 'YA']
        
        for day in range(1, num_days + 1):
            d = date(year, month, day)
            all_dates.append({
                'date': d.strftime('%Y-%m-%d'),
                'day': day,
                'weekday': days_uz[d.weekday()],
                'is_today': d == today
            })
            
        # Get all attendance records for this month
        sessions = AttendanceSession.objects.filter(group=group, date__year=year, date__month=month)
        attendances = Attendance.objects.filter(session__in=sessions).select_related('student', 'session')
        
        att_dict = {}
        total_present = 0
        total_absent = 0
        total_sessions = sessions.count()
        
        for att in attendances:
            s_id = str(att.student.id)
            d_str = att.session.date.strftime('%Y-%m-%d')
            if s_id not in att_dict:
                att_dict[s_id] = {}
            att_dict[s_id][d_str] = att.status
            
            if att.status == 'present': total_present += 1
            if att.status == 'absent': total_absent += 1
            
        matrix_data = []
        for student in students:
            s_id = str(student.id)
            student_atts = []
            
            s_present = 0
            s_total = total_sessions
            
            for date_info in all_dates:
                d_str = date_info['date']
                status = att_dict.get(s_id, {}).get(d_str, '')
                student_atts.append({
                    'date': d_str,
                    'status': status
                })
                if status == 'present': s_present += 1
                
            percentage = round((s_present / s_total * 100) if s_total > 0 else 0)
            
            matrix_data.append({
                'student': {
                    'id': student.id,
                    'full_name': f"{student.last_name} {student.first_name}"
                },
                'attendances': student_atts,
                'percentage': percentage
            })
            
        overall_pct = round((total_present / (total_present + total_absent) * 100) if (total_present + total_absent) > 0 else 0)

        return Response({
            'stats': {
                'present': total_present,
                'absent': total_absent,
                'percent': overall_pct
            },
            'all_dates': all_dates,
            'matrix_data': matrix_data
        })

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['session', 'student', 'status']

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Allows updating multiple attendance records at once."""
        records = request.data.get('records', [])
        for item in records:
            record_id = item.get('id')
            new_status = item.get('status')
            if record_id and new_status:
                Attendance.objects.filter(id=record_id).update(status=new_status)
        return Response({'status': 'bulk update successful'}, status=status.HTTP_200_OK)
