from aiogram.dispatcher.filters.state import State, StatesGroup

class CreateProfile(StatesGroup):
    name = State()
    description = State()
    city = State()
    photo = State()
    sex = State()
    age = State()
    hobbies = State()


class EditProfile(StatesGroup):
    description_edit = State()
    photo_edit = State()


class SearchProfile(StatesGroup):
    in_doing = State()


class Add_bot(StatesGroup):
	date = State()

class check_id(StatesGroup):
    id = State()

class req_del(StatesGroup):
    id = State()

class QuestionStatesGroup(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()
    q6 = State()
    q7 = State()
    q8 = State()
    q9 = State()
    q10 = State()
    q11 = State()

