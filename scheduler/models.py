from django.db import models
from django.db.models import Sum, Count, F, Q

class Semester(models.Model):
    name = models.CharField(max_length=50)
    year = models.CharField(max_length=10)
    index = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"

    def __str__(self):
        return f"{self.name} - {self.year}"

class Room(models.Model):
    room_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"
    
    def __str__(self):
        return self.name

class Grade(models.Model):
    name = models.CharField(max_length=100)
    level = models.IntegerField()

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"

    def __str__(self):
        return self.name

class Class(models.Model):
    class_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="classes")
    main_room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="classes")

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"

    def __str__(self):
        return f"{self.name} - {self.grade}"

    def __lt__(self, other):
        return self.class_id < other.class_id

class Subject(models.Model):
    subject_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="subjects")

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self):
        return f"{self.name} - Grade {self.grade}"


class SubjectSchedule(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="schedules")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="schedules")
    lesson_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Subject Schedule"
        verbose_name_plural = "Subject Schedules"
        unique_together = ('subject', 'semester') 

    def __str__(self):
        return f"{self.subject.name} - {self.semester.name}: {self.lesson_count} lessons/week"

class Teacher(models.Model):
    teacher_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    min_lessons = models.IntegerField(default=0)
    max_lessons = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

    def __str__(self):
        return self.name

    def count_lessons_schedule(self, semester):
        total_lessons = (
            SubjectSchedule.objects.filter(
                subject__teachers__teacher=self, 
                semester=semester
            )
            .annotate(
                class_count=Count(
                    'subject__class_teachers__lesson_class',
                    filter=Q(subject__class_teachers__teacher=self),
                    distinct=True
                )
            )
            .aggregate(
                total=Sum(F('lesson_count') * F('class_count'))
            )['total'] or 0
        )
        return total_lessons

class TeacherSubject(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="teachers")

    class Meta:
        verbose_name = "Teacher Subject"
        verbose_name_plural = "Teacher Subjects"
        unique_together = ('teacher', 'subject')

    def __str__(self):
        return f"{self.teacher.name} - {self.subject.name}"

class ClassTeacherSchedule(models.Model):
    lesson_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_teachers")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="class_teachers")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="class_teachers")

    class Meta:
        verbose_name = "Class Teacher Schedule"
        verbose_name_plural = "Class Teacher Schedules"
        unique_together = ('subject', 'teacher', 'lesson_class') 

class TimetableSchedule(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="timetables")
    name = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)
    classes = models.ManyToManyField(Class)
    teachers = models.ManyToManyField(Teacher)
    # config
    population_size = models.PositiveIntegerField(default=100)
    generations_limit = models.PositiveIntegerField(default=100)

    class Meta:
        verbose_name = "Timetable Schedule"
        verbose_name_plural = "Timetable Schedules"

    def __str__(self):
        return self.name

class TimetableGenerationHistory(models.Model):
    timetable = models.ForeignKey(TimetableSchedule, on_delete=models.CASCADE, related_name="generations")
    generation_history = models.IntegerField(default=1)
    fitness = models.FloatField()
    date_created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.generation_history = self.timetable.generations.order_by('-generation_history').first().generation_history + 1
        super(TimetableGenerationHistory, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.timetable.name} - Generation history #{self.generation_history}"

    class Meta:
        verbose_name = "Timetable Generation History"
        verbose_name_plural = "Timetable Generation Histories"
        unique_together = ('timetable', 'generation_history')

class Lesson(models.Model):
    SESSION = [
        (1, 'Morning'),
        (2, 'Afternoon'),
        (3, 'Evening')
    ]
    session = models.IntegerField(choices=SESSION)
    start_time = models.TimeField()
    end_time = models.TimeField()
    index = models.IntegerField()
    timetable = models.ForeignKey(TimetableSchedule, on_delete=models.CASCADE, related_name="lessons")

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"

    @property
    def session_name(self):
        return dict(self.SESSION).get(self.session)

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"

class TimetableAssignment(models.Model):
    timetable_generation_history = models.ForeignKey(TimetableGenerationHistory, on_delete=models.CASCADE, related_name="assignments")
    lesson_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="assignments")
    day_of_week = models.IntegerField()
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="assignments")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="assignments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="assignments")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="assignments")

    class Meta:
        verbose_name = "Timetable Assignment"
        verbose_name_plural = "Timetable Assignments"
        unique_together = ('timetable_generation_history', 'lesson_class', 'day_of_week', 'lesson')

    def __str__(self):
        return f"{self.lesson_class.name} - {self.subject.name} - {self.teacher.name}"