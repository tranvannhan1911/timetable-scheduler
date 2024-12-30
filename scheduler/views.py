from django.shortcuts import render
from django.db.models import Prefetch
from .models import (
    TimetableAssignment, TimetableGenerationHistory, 
    Lesson, Class, Teacher, Subject, Room
)

def timetable_view(request, timetable_history_id):
    # Extract query parameters

    class_id = request.GET.get('class')
    teacher_id = request.GET.get('teacher')
    subject_id = request.GET.get('subject')

    history = TimetableGenerationHistory.objects.get(pk=timetable_history_id)
    timetable = history.timetable

    # Base query
    assignments = history.assignments.order_by('lesson_class', 'day_of_week',  'lesson__session')

    # Apply filters
    if class_id:
        assignments = assignments.filter(lesson_class_id=class_id)
    if teacher_id:
        assignments = assignments.filter(teacher_id=teacher_id)
    if subject_id:
        assignments = assignments.filter(subject_id=subject_id)

    # sessions = timetable.lessons.values_list('session', flat=True).distinct()
    # print(sessions)

    # Group assignments by class
    grouped_assignments = {}
    for assignment in assignments:
        lesson_class = assignment.lesson_class
        if lesson_class not in grouped_assignments:
            grouped_assignments[lesson_class] = {}

        session = assignment.lesson.session
        if session not in grouped_assignments[lesson_class]:
            grouped_assignments[lesson_class][session] = {}

        lesson_index = assignment.lesson.index
        if lesson_index not in grouped_assignments[lesson_class][session]:
            grouped_assignments[lesson_class][session][lesson_index] = {}

        day = assignment.day_of_week
        grouped_assignments[lesson_class][session][lesson_index][day] = assignment
    # sort by class, then session, then lesson_index, then day
    grouped_assignments = dict(sorted(grouped_assignments.items()))
    for class_id, sessions in grouped_assignments.items():
        grouped_assignments[class_id] = dict(sorted(sessions.items()))
        for session, lessons in grouped_assignments[class_id].items():
            grouped_assignments[class_id][session] = dict(sorted(lessons.items()))
            for lesson_index, days in grouped_assignments[class_id][session].items():
                grouped_assignments[class_id][session][lesson_index] = dict(sorted(days.items()))

    context = {
        'grouped_assignments': grouped_assignments,
        'classes': Class.objects.all(),
        'teachers': Teacher.objects.all(),
        'subjects': Subject.objects.all(),
        'days_of_week': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'day_indices': range(0, 7),
        'sessions_name': Lesson.SESSION,
    }
    return render(request, 'timetable/timetable.html', context)
