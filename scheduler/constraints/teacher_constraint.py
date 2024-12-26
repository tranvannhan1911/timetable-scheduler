from .constraint import TimetableConstraint

class TeacherConstraint(TimetableConstraint):
    def __init__(self, timetable):
        self.timetable = timetable
        self.weight = 999

    def calculate_fitness(self):
        return self.teacher_conflict()

    def get_bad_lessons_class(self):
        # get all lesson teacher conflicts
        # teacher can only teach one class at a time
        bad_lessons_indices = []

        # get all teacher except zero
        teachers = self.timetable.details[self.timetable.details['teacher'] != 0]['teacher'].unique()
        
        for teacher in teachers:
            teacher_lessons = self.timetable.details[self.timetable.details['teacher'] == teacher]
            duplicate_rows = teacher_lessons[teacher_lessons[['lesson', 'dow']].duplicated(keep=False)]
            # print("duplicate_rows", teacher, duplicate_rows)
            bad_lessons_indices.extend(duplicate_rows.index.tolist())
        return bad_lessons_indices

    def teacher_conflict(self):
        # check teacher conflict
        # teacher can only teach one class at a time
        error = 0
        # get all teachers
        teachers = self.timetable.details[self.timetable.details['teacher'] != 0]['teacher'].unique()
        for teacher in teachers:
            # get all lessons for this teacher
            teacher_lessons = self.timetable.details[self.timetable.details['teacher'] == teacher]
            duplicate_rows = teacher_lessons[teacher_lessons[['lesson', 'dow']].duplicated(keep=False)].drop_duplicates(subset=["dow", "lesson"]) 
            error += len(duplicate_rows)
        return error 
        # return error * self.weight