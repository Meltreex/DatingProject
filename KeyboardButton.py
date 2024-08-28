from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def start():
    button_start = KeyboardButton('Давай начнем👌')
    magic_start = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    return magic_start.add(button_start)
def btn_exit():
    # кнопки отмены
    button_exit = KeyboardButton('Выйти❌')
    menu_exit = ReplyKeyboardMarkup(resize_keyboard=True)
    return menu_exit.add(button_exit)

def btn_gender():
    # кнопки выбора пола
    button_male = KeyboardButton('Мужчина')
    button_wooman = KeyboardButton('Женщина')
    sex_input = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    return sex_input.add(button_male, button_wooman)

def keyboard_for_loc():
    loc = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    btn_loc = KeyboardButton("Отправить геолокацию", request_location=True)
    return loc.add(btn_loc)

def btn_edit():
    button_again = KeyboardButton('Заполнить заново🔄')
    button_edit_description = KeyboardButton('Изменить описание📝')
    button_edit_photo = KeyboardButton('Изменить фото')
    button_cancel = KeyboardButton('Выйти❌')

    edit_profile = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    return edit_profile.add(button_again, button_edit_description, button_edit_photo, button_cancel)

def btn_cancel():
    # кнопки для отмены
    button_cancel = KeyboardButton('Отменить❌')
    button_cancel_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    return button_cancel_menu.add(button_cancel)

def btn_estimator():
    # кнопки для оценки
    button_like = KeyboardButton('❤️')
    button_dislike = KeyboardButton('👎')
    button_other = KeyboardButton('Выйти❌')
    mark_menu = ReplyKeyboardMarkup(resize_keyboard=True)
    return mark_menu.add(button_like, button_dislike).add(button_other)

def btn_for_btnprofile():
    button_edit_profilelist = KeyboardButton('Ред. анкету📝')
    button_remove_profile = KeyboardButton('Удалить🗑')
    button_other = KeyboardButton('Выйти❌')
    mark_menu = ReplyKeyboardMarkup(resize_keyboard=True)
    return mark_menu.add(button_edit_profilelist, button_remove_profile).add(button_other)


def keyboard_for_question():
    menu = ReplyKeyboardMarkup(resize_keyboard=True)
    btn_yes = KeyboardButton('Да')
    btn_yes_50 = KeyboardButton('Скорее да')
    btn_notsure = KeyboardButton('Неуверен')
    btn_no_50 = KeyboardButton('Скорее нет')
    btn_no = KeyboardButton('Нет')
    button_exit = KeyboardButton('Выйти❌')
    return menu.add(btn_yes, btn_yes_50).add(btn_notsure).add(btn_no_50, btn_no).add(button_exit)
