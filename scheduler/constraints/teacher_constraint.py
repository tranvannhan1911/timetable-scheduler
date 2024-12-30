from .constraint import TimetableConstraint

class TeacherConstraint(TimetableConstraint):
    def __init__(self, timetable):
        self.timetable = timetable
        self.weight = 1000

    def calculate_fitness(self):
        return self.teacher_conflict()

    def get_bad_lessons_class(self):
        bad_lessons_indices = []

        teachers = self.timetable.details[self.timetable.details['teacher'] != 0]['teacher'].unique()
        
        for teacher in teachers:
            teacher_lessons = self.timetable.details[self.timetable.details['teacher'] == teacher]
            duplicate_rows = teacher_lessons[teacher_lessons[['lesson', 'dow']].duplicated(keep=False)]
            bad_lessons_indices.extend(duplicate_rows.index.tolist())
        return bad_lessons_indices

    def teacher_conflict(self):
        error = 0
        teachers = self.timetable.details[self.timetable.details['teacher'] != 0]['teacher'].unique()
        for teacher in teachers:
            # get all lessons for this teacher
            teacher_lessons = self.timetable.details[self.timetable.details['teacher'] == teacher]
            duplicate_rows = teacher_lessons[teacher_lessons[['lesson', 'dow']].duplicated(keep=False)].drop_duplicates(subset=["dow", "lesson"]) 
            error += len(duplicate_rows)
        return error * self.weight