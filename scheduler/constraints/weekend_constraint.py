from .constraint import TimetableConstraint

class WeekendConstraint(TimetableConstraint):
    def __init__(self, timetable):
        self.timetable = timetable
        self.weight = 1000
        self.weekend_days = [5, 6]

    def calculate_fitness(self):
        return self.weekend_fail()

    def get_taint_lessons(self):
        return self.timetable.details[self.timetable.details['dow'].isin(self.weekend_days)].index.tolist()

    def get_bad_lessons_class(self):
        bad_lessons_indices = []
        for day in self.weekend_days:
            bad_lessons_indices.extend(self.timetable.details[(self.timetable.details['dow'] == day) & (self.timetable.details['subject'] != 0)].index.tolist())

        return bad_lessons_indices

    def weekend_fail(self):
        error = len(self.get_bad_lessons_class())
        return error * self.weight