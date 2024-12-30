class TimetableConstraint:
    def __init__(self, timetable):
        self.timetable = timetable
    
    def calculate_fitness(self):
        raise NotImplementedError("calculate_fitness method is not implemented")

    def get_taint_lessons(self):
        return []