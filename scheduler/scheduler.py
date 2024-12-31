import random
import pandas as pd
import numpy as np
import copy
import time
from .models import (
    Semester, Lesson, Room, Grade, Class, 
    Teacher, Subject, SubjectSchedule, TeacherSubject, 
    TimetableSchedule, TimetableAssignment, TimetableGenerationHistory
)
from .constraints import TeacherConstraint, WeekendConstraint, NoGapConstraint

class Timetable:
    constraints = [TeacherConstraint, WeekendConstraint]

    def __init__(self, timetable_schedule):
        self.timetable_schedule = timetable_schedule
        classes = timetable_schedule.classes.all()
        dow = range(0, 7)
        lessons = timetable_schedule.lessons.all()

        data = []
        for class_obj in classes:
            
            class_data = []
            for day in dow:
                for lesson in lessons:
                    class_data.append({
                        'class': class_obj.pk,
                        'dow': day,
                        'lesson': lesson.pk,
                        'subject': 0,
                        'teacher': 0,
                        'room': 0  # Có thể thêm logic gán phòng học tại đây
                    })
            
            data.extend(class_data)
        self.details = pd.DataFrame(data)

        for class_obj in classes:
            subjects = class_obj.grade.subjects.filter(schedules__semester = timetable_schedule.semester)
            
            for subject in subjects:
                subject_counter = subject.schedules.get(semester = timetable_schedule.semester).lesson_count
                for _ in range(subject_counter):
                    idx, lesson = self.get_empty_lessons_schedule(class_obj, subject)
                    self.details.iloc[idx] = lesson

        self.adjust_schedule()
        self.calculate_fitness()

    def adjust_schedule(self):
        from django.db.models import F

        lesson_sessions = Lesson.objects.values('id', 'session')
        lesson_session_map = {entry['id']: entry['session'] for entry in lesson_sessions}
        self.details['session'] = self.details['lesson'].map(lesson_session_map)
        grouped = self.details.groupby(['class', 'dow', 'session'])
        
        for (class_id, day, session_id), group in grouped:
            group = group.sort_values(by='lesson')
            
            non_empty = group[group['subject'] != 0]
            empty = group[group['subject'] == 0]
            
            adjusted_session = pd.concat([non_empty, empty])
            
            self.details.loc[group.index, ['subject', 'teacher', 'room']] = adjusted_session[['subject', 'teacher', 'room']].values
        return


    def copy(self):
        timetable = copy.deepcopy(self)
        timetable.details = self.details.copy()
        return timetable

    def calculate_fitness(self):
        total = 0
        for constraint in self.constraints:
            cons_obj = constraint(self)
            total += cons_obj.calculate_fitness()
        self.fitness_score = total
        return total

    def get_taint_lessons(self):
        taint_lessons = []
        for constraint in self.constraints:
            taint_lessons.extend(constraint(self).get_taint_lessons())
        return taint_lessons

    def get_valid_lessons_indices(self, class_id=None, subject_id=None, teacher_id=None):
        taint_lessons = self.get_taint_lessons()
        valid_lessons = self.details[~self.details.index.isin(taint_lessons)]
        if class_id is not None:
            valid_lessons = valid_lessons[valid_lessons['class'] == class_id]
        if subject_id is not None:
            valid_lessons = valid_lessons[valid_lessons['subject'] == subject_id]
        if teacher_id is not None:
            valid_lessons = valid_lessons[valid_lessons['teacher'] == teacher_id]
        return valid_lessons.index.tolist()

    def get_bad_lessons_class(self):
        bad_lessons_indices = []
        for constraint in self.constraints:
            bad_lessons_indices.extend(constraint(self).get_bad_lessons_class())
        bad_lessons_indices.sort()
        # print(bad_lessons_indices)
        return bad_lessons_indices

    def get_empty_lessons_schedule(self, class_obj, subject):
        # get available lesson from data
        available_lessons = self.details[self.details.index.isin(self.get_valid_lessons_indices())]
        available_lessons = available_lessons[(available_lessons['class'] == class_obj.pk) & (available_lessons['subject'] == 0)]
        if len(available_lessons) == 0:
            raise Exception("No available lesson")

        lesson = available_lessons.sample(n=1)
        teacher_schedule = class_obj.class_teachers.filter(subject=subject).first()
        if teacher_schedule is None:
            raise Exception("No teacher schedule")
        lesson_schedule = {
            "class": class_obj.pk,
            "dow": lesson['dow'].tolist()[0],
            "lesson": lesson['lesson'].tolist()[0],
            "subject": subject.pk,
            "teacher": teacher_schedule.teacher.pk,
            "room": class_obj.main_room.pk
        }
        return lesson.index.tolist()[0], lesson_schedule

    def reset_lesson(self, lesson_idx):
        lesson = self.details.iloc[lesson_idx]
        lesson['subject'] = 0
        lesson['teacher'] = 0
        lesson['room'] = 0


class TimetableScheduler:
    def __init__(self, timetable_schedule):
        self.timetable_schedule = timetable_schedule
        self.population_size = timetable_schedule.population_size
        self.generations = timetable_schedule.generations_limit
        self.excellent_population = 0.2
        self.good_population_size = 0.4

    def mutate(self, individual):
        individual = individual.copy()
        individual.fitness_score = -1
        classes = self.timetable_schedule.classes.all()
        bad_lessons_indices = individual.get_bad_lessons_class()

        for class_obj in classes:
            # get first index of class in df
            class_first_idx = individual.details[individual.details['class'] == class_obj.pk].index[0]
            # get last index of class  in df
            class_end_idx = individual.details[individual.details['class'] == class_obj.pk].index[-1]
            class_bad_lesson_idxs = [idx for idx in bad_lessons_indices if class_first_idx <= idx <= class_end_idx]
            
            valid_lesson_idxs = individual.get_valid_lessons_indices(class_id=class_obj.pk)
            if len(class_bad_lesson_idxs) == 0:
                continue
            
            for i in range(min(len(class_bad_lesson_idxs), 20)):
                rand = random.random()
                probs = [0.2, 0.7, 0.1]
                if len(class_bad_lesson_idxs) == 1:
                    probs = [0, 0.8, 0.2]
                action = np.random.choice([1, 2, 3], p=probs)

                if action == 1:
                    lesson1_idx = random.choice(class_bad_lesson_idxs)
                    lesson2_idx = random.choice(class_bad_lesson_idxs)
                elif action == 2:
                    lesson1_idx = random.choice(class_bad_lesson_idxs)
                    lesson2_idx = random.choice(valid_lesson_idxs)
                else:
                    lesson1_idx = random.choice(valid_lesson_idxs)
                    lesson2_idx = random.choice(valid_lesson_idxs)

                columns_to_swap = ['subject', 'teacher', 'room']
                individual.details.loc[[lesson1_idx, lesson2_idx], columns_to_swap] = (
                    individual.details.loc[[lesson2_idx, lesson1_idx], columns_to_swap].values
                )
            
        individual.adjust_schedule()
        individual.calculate_fitness()


        return individual

    def crossover(self, parent1, parent2):
        # 1: Get the parent have higher fitness as base
        # at each step, decide whether to take the gene from another parent?
        dominant = parent1.copy()
        weak = parent2.copy()
        p1_fitness = parent1.fitness_score
        p2_fitness = parent2.fitness_score
        if p1_fitness > p2_fitness:
            dominant = parent2.copy()
            weak = parent1.copy()

        dominant.fitness_score = -1

        for i in range(len(dominant.details)):
            # TODO: avoid to hardcode 0.4
            if random.random() < 0.4:
                dominant.details.iloc[i] = weak.details.iloc[i]
        
        # fix the timetable if subject is not enough
        for lesson_class_id in dominant.details['class'].unique():
            df_class = dominant.details[dominant.details['class'] == lesson_class_id]
            class_obj = Class.objects.get(pk = lesson_class_id)
            lack_subjects = []
            redundant_subjects = []

            # get subjects of class that have subject schedule in semester
            subjects = class_obj.grade.subjects.filter(schedules__semester = self.timetable_schedule.semester)
            for subject in subjects:
                subject_schedule = subject.schedules.get(semester = self.timetable_schedule.semester)
                lesson_count = subject_schedule.lesson_count
                if len(df_class[df_class['subject'] == subject.pk]) < lesson_count:
                    lack_subjects.append(subject.pk)
                    for _ in range(lesson_count - len(df_class[df_class['subject'] == subject.pk])):
                        idx, lesson = dominant.get_empty_lessons_schedule(class_obj, subject)
                        dominant.details.iloc[idx] = lesson
                    # print(dominant.get_empty_lessons_schedule(class_obj, subject))

                elif len(df_class[df_class['subject'] == subject.pk]) > lesson_count:
                    redundant_subjects.append(subject.pk)
                    lesson_idxs = df_class[df_class['subject'] == subject.pk].index.tolist()
                    redundant = len(lesson_idxs) - lesson_count
                    for _ in range(redundant):
                        random_idx = random.choice(lesson_idxs)
                        dominant.reset_lesson(random_idx)
                        lesson_idxs.remove(random_idx)
                        # lesson_idx = lessons.sample(n=1).index.tolist()[0]
                        # lesson['subject'][lesson_idx] = 0
                        # lesson['teacher'][lesson_idx] = 0
                        # lesson['room'][lesson_idx] = 0
                
        # print(dominant.details[dominant.details['class'] == 1])
        # print(len(parent1.details[parent1.details['subject'] != 0]))
        # for each subject in parent1.details and then show number of lesson
        for lesson_class_id in dominant.details['class'].unique():
            df_class = dominant.details[dominant.details['class'] == lesson_class_id]
            class_obj = Class.objects.get(pk = lesson_class_id)
            lack_subjects = []
            redundant_subjects = []

            # subjects = class_obj.grade.subjects
            # for subject in subjects:
            #     subject.schedules.get(semester = self.timetable.semester).
            # get subjects of class that have subject schedule in semester
            subjects = class_obj.grade.subjects.filter(schedules__semester = self.timetable_schedule.semester)
            for subject in subjects:
                subject_schedule = subject.schedules.get(semester = self.timetable_schedule.semester)
                lesson_count = subject_schedule.lesson_count
                if len(df_class[df_class['subject'] == subject.pk]) < lesson_count:
                    print(f"Class {class_obj.name} lack {subject.name}: {len(df_class[df_class['subject'] == subject.pk])} < {lesson_count}")
                    print(len(parent1.details[(parent1.details['subject'] == subject.pk) & (parent1.details['class'] == lesson_class_id)]))
                    

                elif len(df_class[df_class['subject'] == subject.pk]) > lesson_count:
                    print(f"Class {class_obj.name} redundant {subject.name}: {len(df_class[df_class['subject'] == subject.pk])} > {lesson_count}")
                    print(len(parent1.details[(parent1.details['subject'] == subject.pk) & (parent1.details['class'] == lesson_class_id)]))
                    
                # else:
                #     print(f"Class {class_obj.name} has enough {subject.name}: {len(df_class[df_class['subject'] == subject.pk])} == {lesson_count}")
                #     print(len(parent1.details[(parent1.details['subject'] == subject.pk) & (parent1.details['class'] == lesson_class_id)]))
        dominant.calculate_fitness()
        # 2: at each step, random chance to take gene from both parents
        # at the end, fix the timetable if subject is not enough
        return dominant

    def generate_population(self):
        return [Timetable(self.timetable_schedule) for _ in range(self.population_size)]

    def generate_probabilities(self, size):
        # Assign weights inversely proportional to index (e.g., 1, 1/2, 1/3, ...)
        weights = np.array([1 / (i + 1) for i in range(size)])
        # Normalize weights to sum up to 1
        probabilities = weights / weights.sum()
        return probabilities

    def schedule(self):
        start_time = time.time()
        print("start schedule")
        # timetable1 = Timetable(self.timetable_schedule)

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     # print(timetable1.details[timetable1.details['class'] == 1])

        #     timetable1.get_bad_lessons_class()

        #     # print(len(timetable1.details[timetable1.details['subject'] != 0]))
        #     print(timetable1.fitness_score)

        #     # print(len(timetable1.details[(timetable1.details['class'] == 1) & (timetable1.details['subject'] != 0)]))
        #     child = timetable1
        #     for i in range(10):
        #         child = self.mutate(child)
        #     print(child.fitness_score)

        #     child.details.to_csv("timetable.csv")
        # self.save(child)
        # return
        population = self.generate_population()
        print(population[0].details)

        excellent_population_size = int(self.excellent_population * self.population_size)
        # good_population_size = int(self.good_population_size * self.population_size)
        probabilities = self.generate_probabilities(excellent_population_size)
        print(probabilities)
        
        start_gen_time = time.time()
        end_gen_time = time.time()
        for generation in range(self.generations):
            population.sort(key=lambda x: x.fitness_score)
            print(f"Generation {generation}: Best Fitness = {population[0].fitness_score}, Time = {end_gen_time - start_gen_time}s")
            start_gen_time = time.time()
            if population[0].fitness_score == 0:
                break

            new_generation = population[:excellent_population_size]

            excellent_population = population[:excellent_population_size]

            for _ in range(self.population_size - excellent_population_size):
                parent1 = np.random.choice(excellent_population, p=probabilities)
                # parent2 = random.choice(population)
                # child = self.crossover(parent1, parent2)
                child = self.mutate(parent1)
                new_generation.append(child)
            population = new_generation
            end_gen_time = time.time()
        end_time = time.time()
        print("time: ", end_time - start_time)
        population[0].details.to_csv("timetable.csv")
        print("saving")
        self.save(population[0])
        return

    def save(self, timetable):
        history = TimetableGenerationHistory.objects.create(
            timetable = self.timetable_schedule,
            fitness = timetable.fitness_score
        )
        for idx, assignment in timetable.details.iterrows():
            if assignment['subject'] != 0:
                TimetableAssignment.objects.create(
                    timetable_generation_history = history,
                    lesson_class = Class.objects.get(pk = assignment['class']),
                    day_of_week = assignment['dow'],
                    lesson = Lesson.objects.get(pk = assignment['lesson']),
                    teacher = Teacher.objects.get(pk = assignment['teacher']),
                    subject = Subject.objects.get(pk = assignment['subject']),
                    room = Room.objects.get(pk = assignment['room'])
                )


