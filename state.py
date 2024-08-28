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
