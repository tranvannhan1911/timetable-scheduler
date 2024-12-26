from django.contrib import admin
from unfold.admin import StackedInline, TabularInline

from unfold.admin import ModelAdmin

from .models import (
    Semester, Lesson, Room, Grade, Class, ClassTeacherSchedule,
    Teacher, Subject, SubjectSchedule, TeacherSubject, 
    TimetableSchedule, TimetableGenerationHistory
)
from django.urls import path, reverse
from django.http import HttpResponse
from django import forms
from .scheduler import TimetableScheduler

class SemesterSubjectInline(TabularInline):
    model = SubjectSchedule
    extra = 0

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

class TeacherAdmin(ModelAdmin):
    list_display = ('teacher_id', 'name', 'class_count')
    search_fields = ('teacher_id', 'name')
    inlines = [TeacherSubjectInline]

    def class_count(self, obj):
        # Assuming a relationship between Teacher and Class models through a Subject model
        return obj.class_teachers.count()  # Adjust based on your actual models
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
    readonly_fields = [field.name for field in TimetableGenerationHistory._meta.fields]  # Make all fields read-only

    def has_add_permission(self, request, obj=None):
        # Prevent adding new records
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent editing existing records
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow deletion of records
        return True

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
    list_display = ('semester', 'name', 'date_created')
    search_fields = ('name', )
    readonly_fields = ('date_created', )
    change_form_template = 'admin/scheduler/timetable_schedule/change_form.html'
    form = TimetableScheduleForm
    inlines = [LessonInline, TimetableGenerationHistoryInline]
    # fieldsets = (
    #     ('Main', {
    #         'fields': ('label', ),
    #         'classes': ('baton-tabs-init', 'baton-tab-group-fs-kyc--inline-lesson'),
    #         'description': 'This is a description text'

    #     }),
    #     ('Lesson', {
    #         'fields': (),
    #         'classes': ('tab-fs-lesson', ),
    #     }),
    # )

    # # add button to create timetable details in change form
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

    def generate_timetable(self, request, object_id):
        timetable_schedule = TimetableSchedule.objects.get(pk=object_id)
        timetable_sceduler = TimetableScheduler(timetable_schedule)
        timetable_sceduler.schedule()
        return HttpResponse(f"Generated timetable for TimetableSchedule ID: {object_id}")


admin.site.register(TimetableSchedule, TimetableScheduleAdmin)