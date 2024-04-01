from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def start_btn():
    button_start = KeyboardButton('Давай начнем👌')
    magic_start = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    return magic_start.add(button_start)

def noname():
    pass

def keyboard_forAdmins():
    menu = ReplyKeyboardMarkup(resize_keyboard=True)
    add_user = KeyboardButton('Add Bot')
    button_exit = KeyboardButton('Выйти❌')
    return menu.add(add_user, button_exit)

def btn_for_exit():
    # кнопки отмены
    button_exit = KeyboardButton('Выйти❌')
    menu_exit = ReplyKeyboardMarkup(resize_keyboard=True)
    return menu_exit.add(button_exit)

def btn_for_gender():
    # кнопки выбора пола
    button_male = KeyboardButton('Мужчина')
    button_wooman = KeyboardButton('Женщина')
    sex_input = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    return sex_input.add(button_male, button_wooman)

def keyboard_for_loc():
    loc = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    btn_loc = KeyboardButton("Отправить геолокацию", request_location=True)
    return loc.add(btn_loc)