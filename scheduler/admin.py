from django.contrib import admin, messages
from unfold.admin import StackedInline, TabularInline
from unfold.contrib.inlines.admin import NonrelatedTabularInline
from django.utils.html import format_html
from django.urls import resolve

from unfold.admin import ModelAdmin

from .models import (
    Semester, Lesson, Room, Grade, Class, ClassTeacherSchedule,
    Teacher, Subject, SubjectSchedule, TeacherSubject, 
    TimetableSchedule, TimetableGenerationHistory
)
from django.urls import path, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from .scheduler import TimetableScheduler

class SemesterSubjectInline(TabularInline):
    model = SubjectSchedule
    extra = 0
    tab = True

class SemesterAdmin(ModelAdmin):
    list_display = ('name', 'year', 'index', 'start_date', 'end_date')
    search_fields = ('name', )
    inlines = [SemesterSubjectInline]

admin.site.register(Semester, SemesterAdmin)


class RoomAdmin(ModelAdmin):
    list_display = ('room_id', 'name')
    search_fields = ('room_id', 'name')

admin.site.register(Room, RoomAdmin)

class GradeAdmin(ModelAdmin):
    list_display = ('name', 'level')
    search_fields = ('name', )

admin.site.register(Grade, GradeAdmin)


class ClassTeacherInline(TabularInline):
    model = ClassTeacherSchedule
    extra = 0
    readonly_fields = ('subject', )
    fields = ('subject', 'teacher')
    tab = True

class ClassAdmin(ModelAdmin):
    list_display = ('class_id', 'name', 'grade', 'main_room')
    search_fields = ('class_id', 'name')

    inlines = [ClassTeacherInline]

admin.site.register(Class, ClassAdmin)

class SubjectAdmin(ModelAdmin):
    list_display = ('subject_id', 'name', 'grade')
    search_fields = ('subject_id', 'name')

admin.site.register(Subject, SubjectAdmin)

class TeacherSubjectInline(TabularInline):
    model = TeacherSubject
    extra = 0
    tab = True

class TeacherAdmin(ModelAdmin):
    list_display = ('teacher_id', 'name', 'min_lessons', 'max_lessons', 'class_count')
    search_fields = ('teacher_id', 'name')
    inlines = [TeacherSubjectInline]

    def class_count(self, obj):
        return obj.class_teachers.count()
    class_count.short_description = 'Number of Classes'

admin.site.register(Teacher, TeacherAdmin)

# timetable

class LessonInline(TabularInline):
    model = Lesson
    extra = 0
    tab = True

class TimetableGenerationHistoryInline(TabularInline):
    model = TimetableGenerationHistory
    extra = 0
    tab = True
    readonly_fields = [field.name for field in TimetableGenerationHistory._meta.fields] + ['view_timetable']

    def view_timetable(self, obj):
        if obj and obj.id:
            url = reverse('timetable_view', args=[obj.id])
            return format_html('<a href="{}" target="_blank">View Timetable</a>', url)
        return "-"
    
    view_timetable.short_description = "View timetable"

    def has_add_permission(self, request, obj=None):
        # Prevent adding new records
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent editing existing records
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow deletion of records
        return True

class TeacherLessonCountInline(NonrelatedTabularInline):
    model = Teacher
    fields = ('name', 'min_lessons', 'max_lessons', 'current_lessons')
    readonly_fields = ('name', 'min_lessons', 'max_lessons', 'current_lessons')
    can_delete = False
    extra = 0
    tab = True
    parent_object = None

    def get_parent_object_from_request(self, request):
        from django.urls import resolve
        resolved = resolve(request.path_info)
        if resolved.kwargs and 'object_id' in resolved.kwargs:
            try:
                self.parent_object = self.parent_model.objects.get(pk=resolved.kwargs['object_id'])
                return self.parent_object
            except self.parent_model.DoesNotExist:
                return None
        return None

    def get_queryset(self, request):
        self.get_parent_object_from_request(request)
        return super().get_queryset(request)

    def get_form_queryset(self, obj):
        return obj.teachers.all()

    def save_new_instance(self, parent, instance):
        pass

    def current_lessons(self, obj):
        timetable_id = self.parent_object.id if self.parent_object else None
        if timetable_id:
            return obj.count_lessons_schedule(self.parent_object.semester)
        return 0

    current_lessons.short_description = 'Current Lessons'

    def has_add_permission(self, request, obj=None):
        return False

class TimetableScheduleForm(forms.ModelForm):
    class Meta:
        model = TimetableSchedule
        fields = '__all__'
        widgets = {
            'classes': admin.widgets.FilteredSelectMultiple(
                verbose_name='Classes',
                is_stacked=False
            ),
            'teachers': admin.widgets.FilteredSelectMultiple(
                verbose_name='Teachers',
                is_stacked=False
            )
        }

class TimetableScheduleAdmin(ModelAdmin):
    list_display = ('name', 'semester', 'date_created')
    search_fields = ('name', )
    readonly_fields = ('date_created', )
    change_form_template = 'admin/scheduler/timetable_schedule/change_form.html'
    form = TimetableScheduleForm
    inlines = [TeacherLessonCountInline, LessonInline, TimetableGenerationHistoryInline]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_create_timetable'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
        
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-timetable/<int:object_id>/', self.admin_site.admin_view(self.generate_timetable), name='generate_timetable'),
        ]
        return custom_urls + urls

    def check_teacher_lesson(self, timetable_schedule):
        teachers = timetable_schedule.teachers.all()
        invalid_teachers = []

        for teacher in teachers:
            current_lessons = teacher.count_lessons_schedule(timetable_schedule.semester)
            if not (teacher.min_lessons <= current_lessons <= teacher.max_lessons):
                invalid_teachers.append(
                    f"{teacher.name} (Current: {current_lessons}, Min: {teacher.min_lessons}, Max: {teacher.max_lessons})"
                )
        return invalid_teachers

    def generate_timetable(self, request, object_id):
        timetable_schedule = TimetableSchedule.objects.get(pk=object_id)
        invalid_teachers = self.check_teacher_lesson(timetable_schedule)
        if invalid_teachers:
            messages.error(request, f"Teachers with invalid lesson counts: {', '.join(invalid_teachers)}")
            return HttpResponseRedirect(reverse('admin:scheduler_timetableschedule_change', args=[object_id]))

        try:
            timetable_sceduler = TimetableScheduler(timetable_schedule)
            timetable_sceduler.schedule()
            messages.success(request, "Timetable generated successfully.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
        return HttpResponseRedirect(reverse('admin:scheduler_timetableschedule_change', args=[object_id]))


admin.site.register(TimetableSchedule, TimetableScheduleAdmin)