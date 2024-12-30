from .constraint import TimetableConstraint

class NoGapConstraint(TimetableConstraint):
    def __init__(self, timetable):
        self.timetable = timetable
        self.weight = 500

    def calculate_fitness(self):
        return self.gap_lessons_fail()

    def get_taint_lessons(self):
        return []

    def get_bad_lessons_class(self):
        bad_lessons_indices = []
        
        # Group by 'class' and 'dow' to evaluate each class's schedule for each day
        grouped = self.timetable.details.groupby(['class', 'dow'])
        
        for (class_id, day), group in grouped:
            # Sort by lesson to ensure lessons are in order
            group = group.sort_values(by='lesson')
            
            # Reset the index to track original indices
            group = group.reset_index()
            
            # Iterate through the lessons to find gaps
            for i in range(0, len(group) - 1):
                current_lesson = group.iloc[i]
                next_lesson = group.iloc[i + 1]
                
                # Check if the current lesson has a gap (subject == 0) but is surrounded by lessons with subjects
                if current_lesson['subject'] == 0 and next_lesson['subject'] != 0:
                    # Add the index of the bad lesson
                    bad_lessons_indices.append(int(current_lesson['index']))
        # print(bad_lessons_indices)
        return bad_lessons_indices

    def gap_lessons_fail(self):
        error = len(self.get_bad_lessons_class())
        return error * self.weight