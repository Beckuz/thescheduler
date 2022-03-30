import collections
from datetime import date, datetime, time, timedelta
import itertools
import json

from ortools.sat.python.cp_model import CpModel, CpSolver
##from ortools.util.sorted_interval_list import Domain


class Day:
    def __init__(self, date, slots) -> None:
        self.date = date
        self.slots = slots
    
    def __iter__(self):
        return (slot for slot in self.slots)

    def __str__(self) -> str:
        return self.date.__str__()
    
class Calendar:
    """
    A Calendar represents a time period into a set of timeslots in that period.
    It is also used to convert a timeslot index back to a datetime.
    """
    def __init__(self, start_date = None, end_date = None, slot_length = 2, hours = (8, 10, 13, 15), weekdays = (1, 2, 3, 4, 5)) -> None:
        self.start = datetime.fromisoformat(start_date) if isinstance(start_date, str) else datetime.combine(start_date or date.today(), time())
        self.end = datetime.fromisoformat(end_date) if isinstance(end_date, str) else datetime.combine(end_date or self.start + timedelta(days=100), time())
        self.slot_size = slot_length
        self.hours = hours 
        self.weekdays = weekdays
        if self.start.isoweekday() not in weekdays:
            self.start = self._next_day(self.start)
        if self.end.isoweekday() not in weekdays:
            self.end = self._previous_day(self.end)
        self._length = ((self.end - self.start).days + 1) * len(self.hours)
        self._slots = None

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Calendar):
            return False
        return self.start == o.start \
            and self.end == o.end \
            and self.slot_size == o.slot_size \
            and set(self.hours) == set(o.hours) \
            and set(self.weekdays) == set(self.weekdays)

    def __len__(self) -> int:
        return self._length

    def _next_day(self, date):
        weekday = date.isoweekday() + 1
        days = 1
        while weekday not in self.weekdays:
            weekday = (weekday + 1) % 7
            days += 1
        next_day = date + timedelta(days)
        return next_day if next_day <= self.end else None

    def _previous_day(self, date):
        weekday = date.isoweekday() - 1
        days = -1
        while weekday not in self.weekdays:
            weekday = (weekday - 1) % 7
            days -= 1
        previous_day = date + timedelta(days)
        return previous_day if previous_day >= self.start else None

    def __iter__(self):
        return self._slots.__iter__() if self._slots else (slot for slot in range(len(self)))

    def days(self):
        day_length_in_slots = len(self.hours)
        slot = 0
        while slot < self._length:
            yield Day(self.datetimeOf(slot).date(), range(slot, day_length_in_slots))
            slot += day_length_in_slots

    def datetimeOf(self, slot_index):
        return self.start + timedelta(
            days = slot_index // len(self.hours), 
            hours = self.hours[slot_index % len(self.hours)]
        )

    def canBeUsed(self, slot):
        return self.datetimeOf(slot).isoweekday() in self.weekdays

    def asJSON(self):
        return {
            'start_date': self.start.isoformat(),
            'end_date': self.end.isoformat(),
            'hours': self.hours,
            'weekdays': self.weekdays,
            'slot_length': self.slot_size
        }

    @classmethod
    def all(cls, start, end):
        return cls(start or date(2021, 8, 23), end or date(2021, 12,30), (8, 10, 13, 15, 17, 19, 21), (1,2,3,4,5,6,7))

    @classmethod
    def schoolYear2122(cls):
        return cls(date(2021, 8, 23), date(2021, 12, 11))
    
    @classmethod
    def aboamareYear21(cls):
        return cls(date(2021, 8, 23), date(2021, 12, 30), (8, 10, 13, 15, 17, 19), (1, 2, 3, 4, 5, 6, 7))

class ClassRoom:

    def __init__(self, name, capacity=20) -> None:
        self.name = name
        self.capacity = capacity

    def __str__(self) -> str:
        return str(self.name)

    def asJSON(self):
        return {
            'name': self.name,
            'capacity': self.capacity
        }

class Group:
    def __init__(self, name, participants = None, calendar = None) -> None:
        self.name = name
        self.size = 15 if participants is None else participants if isinstance(participants, int) else len(participants)
        self.participants = participants if isinstance(participants, list) else None
        self.calendar = calendar or Calendar.aboamareYear21()
        self.courses = []

    def __str__(self) -> str:
        return str(self.name)
        
    def addCourse(self, course):
        self.courses.append(course)

    def asJSON(self):
        return {
            'name': self.name,
            'calendar': self.calendar.asJSON(),
            'size': self.size,
            'participants': [p.id for p in self.participants or []],
            'courses': [c.name for c in self.courses]
        }

class Course:

    def __init__(self, group = 'Novia_yr1', name = 'Astronavigation', hours = 40, sessions = 20, teachers=[], participants = None) -> None:
        self.name = name
        self.group = group
        self.hours = hours
        self.preferred_number_of_sessions = sessions if isinstance(sessions, int) else len(sessions)
        self.participants = participants or self.group.participants
        self.nr_participants = len(self.participants) if self.participants else self.group.size
        self.teachers = teachers

    def __str__(self) -> str:
        return '%s:%s' % (self.group, self.name)
        
    def asJSON(self):
        return {
            'name': self.name,
            'group': self.group.name,
            'hours': self.hours,
            'sessions': self.preferred_number_of_sessions,
            'participants': [p.id for p in self.participants or []],
            'teachers': self.teachers
        }

    def canBeTaughtBy(self, teacher):
        return teacher in self.teachers

    def canBeTaughtIn(self, room):
        return isinstance(room, ClassRoom) and room.capacity >= self.nr_participants

    def canBeTaughtInSlot(self, slot):
        return self.group.calendar.canBeUsed(slot)

    def printSchedule(self):
        print(self.name)
        for session in self._sessions:
            print('\t%s:\t%s\t%s' % (session.time, session.room.name, session.teacher))

    def sessionsFor(self, teacher):
        return [session for session in self._sessions if session.teacher == teacher]

class Schedule:
    Session = collections.namedtuple('Session', ('course', 'group', 'time', 'room', 'teacher'))

    def __init__(self, name, calendar) -> None:
        self.name = name
        self.calendar = calendar
        self.groups = []
        self.courses = []
        self.classrooms = []
        self.teachers = []
    
    def addClassRoom(self, name, capacity=20):
        if self.hasClassRoom(name):
            return
        self.classrooms.append(ClassRoom(name, capacity))
    
    def hasClassRoom(self, name):
        for room in self.classrooms:
            if room.name == name:
                return True
        return False

    def addTeachers(self, teachers):
        for teacher in teachers:
            if teacher not in self.teachers:
                self.teachers.append(teacher)

    def addCourse(self, group = 'Novia_yr1', name = 'Astronavigation', hours = 40, sessions = 20, teachers=[], participants = None) -> None:
        if self.hasCourse(group, name):
            return
        group = self.addGroup(group, participants)
        self.addTeachers(teachers)
        course = Course(group, name, hours, sessions, teachers, participants)
        group.addCourse(course)
        self.courses.append(course)

    def hasCourse(self, group, name):
        for course in self.courses:
            if course.name == name and course.group.name == group:
                return True
        return False

    def addGroup(self, name, participants, calendar=None):
        group = self.groupNamed(name)
        if not group:
            group = Group(name, participants or 15, calendar or self.calendar)
            self.groups.append(group)
        return group

    def groupNamed(self, name):
        for group in self.groups:
            if group.name == name:
                return group
        return None

    def createSessions(self, assignments, solver: CpSolver):
        calendar = self.calendar
        sessions = []
        for ci, course in enumerate(self.courses):
            gi = self.groups.index(course.group)
            for slot in calendar:
                for ri, room in enumerate(self.classrooms):
                    for ti, teacher in enumerate(self.teachers):
                        if solver.Value(assignments[slot, gi, ci, ri, ti]):
                            sessions.append(Schedule.Session(course, course.group, calendar.datetimeOf(slot), room, teacher))
        self._sessions = sessions

    def loadSessions(self, sessions):
        def loadSession(course, time, room, teacher):
            return Schedule.Session(
                self._getEntity(course, 'course'),
                datetime.fromisoformat(time),
                self._getEntity(room, 'classroom'),
                self._getEntity(teacher, 'teacher'))
        self._sessions = [loadSession(**session) for session in sessions]

    def _getEntity(self, name, type):
        entity = None
        for e in self.__getattribute__('%ss' % type):
                if str(e) == name:
                    entity = e
                    break
        return entity

    def forEntity(self, name, type=None, fmt='JSON'):
        types = ['group', 'course', 'classroom', 'teacher']

        entity = None
        if type:
            if type not in types:
                raise TypeError('%s is not a valid entity type' % type)
            entity = self._getEntity(name, type)
        else:
            for type in types:
                entity = self._getEntity(name, type)
                if entity:
                    break 
        if not entity:
            raise ValueError('Entity named %s does not exist in schedule %s' % (name, self.name))            
        
        sessions = self.__getattribute__('get%sSchedule' % type.capitalize())(entity)
        if fmt == 'JSON':
            sessions = [dict(course=str(s.course), time=s.time.isoformat(), room=s.room.name, teacher=s.teacher) for s in sessions]
        return sessions
        
    def getGroupSchedule(self, group):
        return sorted([session for session in self._sessions if session.course in group.courses], key=lambda s: s.time)

    def printGroupSchedule(self, group):
        print(group.name)
        for session in self.getGroupSchedule(group):
            print('%s\t%s\t%s\t(%s)' % (session.time, session.course.name, session.room.name, session.teacher))

    def getTeacherSchedule(self, teacher):
        return sorted([session for session in self._sessions if session.teacher == teacher], key=lambda s: s.time)
    
    def printTeacherSchedule(self, teacher):
        print(teacher)
        for session in self.getTeacherSchedule(teacher):
            print('%s\t%s\t%s' % (session.time, session.course.name, session.room.name))

    def save(self):
        # Save schedule as JSON to file
        with open('schedule-manager/src/%s.json' % (self.name), 'w') as f:
            json.dump({
                'name': self.name,
                'calendar': self.calendar.asJSON(),
                'classrooms': [room.asJSON() for room in self.classrooms],
                'groups': [group.asJSON() for group in self.groups],
                'courses': [course.asJSON() for course in self.courses],
                'teachers': self.teachers,
                'sessions': [dict(course=str(s.course), group=str(s.group), time=s.time.isoformat(),
                                  end=(s.time+timedelta(hours=2)).isoformat(),
                                  room=s.room.name, teacher=s.teacher) for s in self._sessions or []]
                }, f, indent=2)
    
    def update(self):
        model = CpModel()
        #TODO: use current schedule as hint for CP model

        #TODO: determine the union calendar (of teachers and groups, and possibly rooms and courses) and adapt all calendars to it.
        cal = self.calendar or Calendar(date(2021, 8, 9), date(2021, 8, 27))
        print(len(cal))

        assignments = {}
        for slot in cal:
            for gi, group in enumerate(self.groups):
                for ci, course in enumerate(self.courses):
                    for ri, room in enumerate(self.classrooms):
                        allow = course.group == group and course.canBeTaughtInSlot(slot) and course.canBeTaughtIn(room)
                        for ti, teacher in enumerate(self.teachers):
                            var_name = '%s:%s_%i_%s_%s' % (group.name, course.name, slot, room.name, teacher)
                            if allow and course.canBeTaughtBy(teacher):
                                assignments[slot, gi, ci, ri, ti] = model.NewIntVar(0, 1, var_name)
                            else:
                                assignments[slot, gi, ci, ri, ti] = model.NewIntVar(0, 0, var_name)

        for ci, course in enumerate(self.courses):
            # ensure sufficient sessions (assignments) for each course
            gi = self.groups.index(course.group)
            model.Add(sum(assignments[slot, gi, ci, ri, ti]
                for slot in cal
                for ri in range(len(self.classrooms))
                for ti in range(len(self.teachers))
                ) == course.preferred_number_of_sessions)

        for slot in cal:
            # each course can have at most one session per time slot
            for ci, course in enumerate(self.courses):
                gi = self.groups.index(course.group)
                model.Add(sum(assignments[slot, gi, ci, ri, ti]
                    for ri in range(len(self.classrooms))
                    for ti in range(len(self.teachers))
                ) <= 1)
            # each group can have at most one session per time slot
            for gi in range(len(self.groups)):
                model.Add(sum(assignments[slot, gi, ci, ri, ti]
                    for ci in range(len(self.courses))
                    for ri in range(len(self.classrooms))
                    for ti in range(len(self.teachers))
                ) <= 1)
            # each room can have at most one session per time slot
            for ri in range(len(self.classrooms)):
                model.Add(sum(assignments[slot, gi, ci, ri, ti]
                    for gi in range(len(self.groups))
                    for ci in range(len(self.courses))
                    for ti in range(len(self.teachers))
                ) <= 1)
            # each teacher can do at most one session per time slot
            for ti in range(len(self.teachers)):
                model.Add(sum(assignments[slot, gi, ci, ri, ti]
                    for gi in range(len(self.groups))
                    for ci in range(len(self.courses))
                    for ri in range(len(self.classrooms))
                ) <= 1)

        penalties = []
        for ti, teacher in enumerate(self.teachers):
            for day in cal.days():
                sessions_per_teacher_per_day = model.NewIntVar(0, 6, 'sessions_%s_%s' % (day, teacher))
                model.Add(sum(assignments[slot, gi, ci, ri, ti]
                    for slot in day
                    for gi in range(len(self.groups))
                    for ci in range(len(self.courses))
                    for ri in range(len(self.classrooms))
                ) == sessions_per_teacher_per_day)
                sessions_per_teacher_per_day_penalty = model.NewIntVar(0, 36, 'sessions_penalty_%s_%s' % (day, teacher))
                penalties.append(sessions_per_teacher_per_day_penalty)
                model.AddMultiplicationEquality(sessions_per_teacher_per_day_penalty, [sessions_per_teacher_per_day, sessions_per_teacher_per_day])

        model.Minimize(sum(penalties))
        solver = CpSolver()
        status = solver.Solve(model)

        print(solver.StatusName(status))

        if status > 3:
            self.createSessions(assignments, solver)
            for group in self.groups:
                self.printGroupSchedule(group)

            for teacher in self.teachers:
                self.printTeacherSchedule(teacher)

    @classmethod
    def load(cls, fileName):
    
        with open(fileName, 'r') as fp:
            saved = json.load(fp)
            schedule = Schedule(saved['name'], Calendar(**saved['calendar']))
            for room in saved['classrooms']:
                schedule.addClassRoom(**room)
            for g in saved['groups']:
                gCalendar = Calendar(**g['calendar'])
                if (schedule.calendar == gCalendar):
                    gCalendar = schedule.calendar
                schedule.addGroup(g['name'], g['participants'] or g['size'], gCalendar)
            for course in saved['courses']:
                schedule.addCourse(**course)
            schedule.addTeachers(saved['teachers'])
            sessions = saved.get('sessions')
            if sessions:
                schedule.loadSessions(sessions)

            return schedule

if __name__ == '__main__':
    cal = Calendar(date(2022, 1, 9), date(2022, 5, 30))
    schedule = Schedule('default', cal)
    schedule.addClassRoom('Aura', 18)
    schedule.addClassRoom('Hermes', 20)
    schedule.addGroup('NoviaYr1', 17, cal)
    schedule.addGroup('NoviaYr2', 20, cal)

    schedule.addCourse('NoviaYr1', 'Math I', teachers=['EL'])
    schedule.addCourse('NoviaYr1', 'COLREGS', teachers=['BL', 'JL', 'PN'])
    schedule.addCourse('NoviaYr1', 'Nav I', teachers=['JL', 'BL'])
    schedule.addCourse('NoviaYr2', 'Math II', teachers=['EL'])
    schedule.addCourse('NoviaYr2', 'Manoeuvres', teachers=['BL', 'PN'])
    schedule.addCourse('NoviaYr2', 'Nav II', teachers=['JL', 'BL'])

    schedule.update()
    schedule.save()

    # schedule = Schedule.load("default.json")
    # print(schedule.forEntity('JL'))