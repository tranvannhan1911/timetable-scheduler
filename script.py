from scheduler.models import Class, Subject, Teacher, ClassTeacherSchedule

classes = Class.objects.all()
for c in classes:
    print(f"{c.name} - {c.grade.name}")
    idx2 = (c.id / 4)%2
    idx3 = (c.id / 3)%3
    for s in c.grade.subjects.all():
        teacher_count = s.teachers.count()
        if teacher_count == 1:
            teacher = s.teachers.first()
            print(f"\t{s.name} - {teacher.name}")
        elif te