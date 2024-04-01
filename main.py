import asyncio
import logging
import datetime
from datetime import timedelta
import random
import aiohttp


#aiogram и всё утилиты для коректной работы с Telegram API
from aiogram import Bot, types, executor
# from aiogram.utils.emoji import emojize
from aiogram.dispatcher import Dispatcher
from aiogram.types.message import ContentType
from aiogram.utils.markdown import text, bold, italic, code, pre
from aiogram.types import ParseMode, InputMediaPhoto, InputMediaVideo, ChatActions
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

#конфиг с настройками
#кастомные ответы
import custom_answer as cus_ans
from database import dbworker
import config
import KeyboardButton as kb
import os.path

BOT_TOKEN = '6261688795:AAGS3FO8s6CrrvSUgCc8GUeAyljhLEgiU9Y'

#задаём логи and инициализируем бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

#инициализируем базу данных
db = dbworker('MainBase.db')


#хендлер команды /start
@dp.message_handler(commands=['start'],state='*')
async def start(msg: types.Message):
	#кнопки для волшебного входа
	button_start = KeyboardButton('Давай начнем👌')

	magic_start = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

	magic_start.add(button_start)
	await msg.answer('Привет!\nЯ помогу найти тебе вторую половинку или просто друзей👫', reply_markup=magic_start)
	if(not db.user_exists(msg.from_user.id)):
		#если юзера нет в базе добавляем его
		db.add_user(msg.from_user.username, msg.from_user.id, msg.from_user.full_name)
		await bot.send_message(-1001406772763,f'Новый пользователь!\nID - {str(msg.from_user.id)}\nusername - {str(msg.from_user.username)}')


# Функция для определения города по координатам
async def get_city_name(latitude, longitude):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json") as response:
            data = await response.json()
            city = data.get('address', {}).get('city')
            return city



#хендлер для команды Зайти в волшебный мир
@dp.message_handler(lambda msg: msg.text == 'Давай начнем👌' or msg.text == '/magic_start', state='*')
async def magic_start(msg: types.Message):
	'''Функция для меню самого бота'''
	#кнопки меню
	button_search = KeyboardButton('Найти человечка🔍')
	button_create_profile = KeyboardButton('Создать анкету📌')
	button_edit_profile = KeyboardButton('Редактировать анкету📝')
	button_remove_profile = KeyboardButton('Удалить🗑')
	button_admin = KeyboardButton('Админка⚙️')
	menu = ReplyKeyboardMarkup(resize_keyboard=True)

	if(not db.profile_exists(msg.from_user.id)):
			menu.add(button_search, button_create_profile)
	elif (db.profile_exists(msg.from_user.id)):
		menu.add(button_search, button_edit_profile, button_remove_profile)
	if msg.from_user.id in config.ADMIN_LIST:
		menu.add(button_admin)
	await msg.answer('Привет-привет, это центральный компьютер чат бота🤖\n\nТут ты можешь управлять всеми этими штуками что внизу⚙️', reply_markup=menu)


#хендлер для создания анкеты


class CreateProfile(StatesGroup):
	name = State()
	description = State()
	city = State()
	photo = State()
	sex = State()
	age = State()
	social_link = State()

#хендлер старта для создания анкеты
@dp.message_handler(lambda message: message.text == 'Создать анкету📌', state='*')
async def create_profile(message: types.Message):
	#кнопки отмены
	button_exit = KeyboardButton('Выйти❌')

	menu_exit = ReplyKeyboardMarkup()

	menu_exit.add(button_exit)

	if message.from_user.username != None:
		if(not db.profile_exists(message.from_user.id)):
			await message.answer("Для того что бы создать твою анкету нужно заполнить несколько пунктов\nДавай начнём с имени, как мне тебя называть?😉",reply_markup=menu_exit)
			await CreateProfile.name.set()
		elif(db.profile_exists(message.from_user.id)) :
			await message.answer('У тебя уже есть активная анкета\n\n')
	else:
		await message.answer('‼️У вас не заполнен username в телеграм!\n\nПожалуйста сделайте это для коректного функционирования бота\nДля этого зайдите в настройки -> Edit Profile(Изменить профиль) и жмякайте add username\n\nТам вводите желаемый никнейм и вуаля')
#хендлер для заполнения имя
@dp.message_handler(state=CreateProfile.name)
async def create_profile_name(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)
		return
	if len(str(message.text)) < 35 and (not str(message.text) in cus_ans.ban_symvols):
		await state.update_data(profile_name=message.text.lower())
		await message.reply('Теперь заполни описание. Расскажи о себе и кого хочешь найти. Это поможет подобрать тебе компанию')
		await CreateProfile.next()
	elif str(message.text) in cus_ans.ban_symvols:
		await message.answer('У тебя в сообщении запрещённые символы🤬🤬\nЗапятая к примеру')
	else:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return

#хендлер для заполнение описания

@dp.message_handler(state=CreateProfile.description)
async def create_profile_description(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)
		return
	if len(message.text) < 35 and (not str(message.text) in cus_ans.ban_symvols):
		await state.update_data(profile_description=message.text)
		await message.answer('Из какого ты города?\nОтправь мне свою геолокацию👇', reply_markup=kb.keyboard_for_loc())
		await CreateProfile.next()
	elif str(message.text) in cus_ans.ban_symvols:
		await message.answer('У тебя в сообщении запрещённые символы🤬🤬\nЗапятая к примеру')
	else:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return

# хендлер для заполнения города
@dp.message_handler(state=CreateProfile.city, content_types=ContentType.LOCATION)
async def create_profile_city(message: types.Message, state: FSMContext):

	latitude = message.location.latitude
	longitude = message.location.longitude

	city = await get_city_name(latitude, longitude)

	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)
		return
	if len(city) < 35 and (not str(city) in cus_ans.ban_symvols):
		await state.update_data(profile_city=city.lower())
		await message.answer('Прелестно, теперь добавим фотокарточку🖼\n\nВажно отправлять фотографией, а не файлом!')
		await CreateProfile.next()
	elif str(message.text) in cus_ans.ban_symvols:
		await message.answer('У тебя в сообщении запрещённые символы🤬🤬\nЗапятая к примеру', reply_markup=kb.keyboard_for_loc())
	else:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return


#хендлер для заполнения фотографии
@dp.message_handler(state=CreateProfile.photo, content_types=ContentType.PHOTO)
async def create_profile_photo(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)

	#кнопки выбора пола
	button_male = KeyboardButton('Мужчина')
	button_wooman = KeyboardButton('Женщина')

	sex_input = ReplyKeyboardMarkup(one_time_keyboard=True)
	sex_input.add(button_male, button_wooman)


	file_id = message.photo[-1].file_id
	await state.update_data(photo=file_id)
	await message.answer('Осталось совсем немного, укажи свой пол', reply_markup=sex_input)
	await CreateProfile.next()

#хендлер для заполнения пола
@dp.message_handler(state=CreateProfile.sex)
async def create_profile_sex(message: types.Message, state: FSMContext):
	if str(message.text) == 'Выйти❌':
		await state.finish()
		await magic_start(message)
		return
	if message.text == 'Мужчина' or message.text == 'Женщина':
		await state.update_data(profile_sex=message.text.lower())
		await message.answer('Замечательно!\nОсталось совсем чуть-чуть\n\nДавай узнаем твой возвраст')
		await CreateProfile.next()
	else:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return

#хендлер для заполнения возвраста
@dp.message_handler(state=CreateProfile.age)
async def create_profile_age(message: types.Message, state: FSMContext):
	try:
		if str(message.text) == 'Выйти❌':
			await state.finish()
			await magic_start(message)
			return
		if int(message.text) < 6:
			await message.answer('ой🤭\nТы чёт маловат...')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 54:
			await message.answer('Пажилой человек👨‍')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 6 and int(message.text) < 54:
			await state.update_data(profile_age=message.text)
			#кнопки меню
			button_skip = KeyboardButton('Пропустить')

			skip_input = ReplyKeyboardMarkup(one_time_keyboard=True)
			skip_input.add(button_skip)
			await message.answer('Анкета успешно создана!')
			user_data = await state.get_data()
			db.create_profile(message.from_user.id, message.from_user.username, str(user_data['profile_name']),
						str(user_data['profile_description']), str(user_data['profile_city']), str(user_data['photo']), str(user_data['profile_sex']), str(user_data['profile_age']))
			await magic_start(message)
			await state.finish()
		else:
			await message.answer('Укажи правильный возраст, только цифры')
			return
	except:
		await message.answer(cus_ans.random_reapeat_list())
		#прерывание функции
		return


#хендлер для удаления анкеты
@dp.message_handler(lambda message: message.text == 'Удалить🗑')
async def delete_profile(message: types.Message):
	'''Функция для удаления анкеты'''
	await send_log(message)
	try:
		db.delete_profile(message.from_user.id)
		await message.answer('Анкета успешно удалена!')
		await magic_start(message)
	except:
		await message.answer(cus_ans.random_reapeat_list())
		return


@dp.message_handler(lambda message: message.text == 'Редактировать анкету📝')
async def edit_profile(message : types.Message):
	'''Функция для меню редактирования анкеты'''
	await send_log(message)
	try:
		if(not db.profile_exists(message.from_user.id)):
			await message.answer('У тебя нет анкеты!')
		elif(db.profile_exists(message.from_user.id)) :
			photo = db.all_profile(message.from_user.id)[0][6]
			#кнопки выбора пола
			button_again = KeyboardButton('Заполнить анкету заново🔄')

			button_edit_description = KeyboardButton('Изменить описание анкеты📝')

			button_edit_age = KeyboardButton('Изменить количество годиков👶')

			button_cancel = KeyboardButton('Выйти❌')

			edit_profile = ReplyKeyboardMarkup(one_time_keyboard=True)
			edit_profile.add(button_again, button_edit_description, button_edit_age, button_cancel)
			caption = 'Твоя анкета:\n\nИмя - ' + str(db.all_profile(message.from_user.id)[0][3]).title() + '\nОписание - ' + str(db.all_profile(message.from_user.id)[0][4]) + '\nМесто жительство🌎 - ' + str(db.all_profile(message.from_user.id)[0][5]).title() + '\nСколько годиков?) - ' + str(db.all_profile(message.from_user.id)[0][8])
			await message.answer_photo(photo, caption=caption, reply_markup=edit_profile)
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return


#хендлер для заполнения анкеты заново
@dp.message_handler(lambda message: message.text == 'Заполнить анкету заново🔄')
async def edit_profile_again(message : types.Message):
	'''Функция для заполнения анкеты заново'''
	await send_log(message)
	try:
		db.delete_profile(message.from_user.id)
		await create_profile(message)

	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return

#класс машины состояний FSM
class EditProfile(StatesGroup):
	description_edit = State()
	age_edit = State()

#хендлеры для изменение возвраста и описания анкеты

@dp.message_handler(lambda message: message.text == 'Изменить количество годиков👶' or message.text == 'Изменить описание анкеты📝')
async def edit_profile_age(message : types.Message):
	try:
		#кнопки для отмены
		button_cancel = KeyboardButton('Отменить❌')

		button_cancel_menu = ReplyKeyboardMarkup(one_time_keyboard=True)

		button_cancel_menu.add(button_cancel)

		if message.text == 'Изменить количество годиков👶':
			await message.answer('Введи свой новый возвраст',reply_markup=button_cancel_menu)
			await EditProfile.age_edit.set()
		elif message.text == 'Изменить описание анкеты📝':
			await message.answer('Введи новое хайп описание своей анкеты!',reply_markup=button_cancel_menu)
			await EditProfile.description_edit.set()
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return
@dp.message_handler(state=EditProfile.age_edit)
async def edit_profile_age_step2(message: types.Message, state: FSMContext):
	'''Функция для обновления возвраста в бд'''
	await send_log(message)
	try:
		if str(message.text) == 'Отменить❌':
			await state.finish()
			await magic_start(message)

			return
		elif int(message.text) < 6:
			await message.answer('ой🤭\nТы чёт маловат...')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 54:
			await message.answer('Пажилой человек👨‍')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 6 and int(message.text) < 54:
			await message.answer('Малый повзрослел получается🤗\n\nВозвраст успешно измененён!')
			await state.update_data(edit_profile_age=message.text)
			user_data = await state.get_data()

			db.edit_age(user_data['edit_profile_age'],str(message.from_user.id))
			await state.finish()
			await edit_profile(message)
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		photorint(e)
		return
@dp.message_handler(state=EditProfile.description_edit)
async def edit_profile_description(message: types.Message, state: FSMContext):
	'''Функция для обновления описания в бд'''
	await send_log(message)
	try:
		if str(message.text) == 'Отменить❌':
			await state.finish()
			await magic_start(message)

			return
		await message.answer('Прекрасное описание броди\n\nОписание успешно изменено!')
		await state.update_data(edit_profile_description=message.text)
		user_data = await state.get_data()

		db.edit_description(user_data['edit_profile_description'],str(message.from_user.id))
		await state.finish()
		await edit_profile(message)
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return

@dp.message_handler(lambda message: message.text == 'Выйти❌')
async def exit(message: types.Message):
	await magic_start(message)

''''''

#класс машины состояний FSM
class SearchProfile(StatesGroup):
	in_doing = State()

#хендлеры для поиска по анкетам
@dp.message_handler(lambda message: message.text == 'Найти человечка🔍')
async def search_profile(message: types.Message):
	'''Функция для ввода пользователя своего города,последующей записи в бд'''
	await send_log(message)
	try:
		if db.profile_exists(message.from_user.id) == False:
			await message.answer('У тебя нет анкеты, заполни её а потом приходи сюда!')
		else:
			await message.answer('Поехали!')
			await SearchProfile.next()
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return

# @dp.message_handler(state=SearchProfile.city_search)
# async def seach_profile_step2(message: types.Message, state: FSMContext):
# 	'''Функция поиска анкет после отправки пользователя своего города'''
# 	await send_log(message)
#
# 	await state.update_data(search_profile_city=message.text.lower())
#
# 	user_data = await state.get_data()
#
# 	db.set_city_search(str(user_data['search_profile_city']), str(message.from_user.id))
# 	if (bool(len(db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]),str(db.get_info(str(message.from_user.id))[8]),str(db.get_info(str(message.from_user.id))[7]))))):
# 		try:
# 			profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]), str(db.get_info(str(message.from_user.id))[8]), str(db.get_info(str(message.from_user.id))[7]))
# 		except:
# 			db.edit_zero_profile_status(message.from_user.id)
# 			profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]), str(db.get_info(str(message.from_user.id))[8]), str(db.get_info(str(message.from_user.id))[7]))
# 		await state.update_data(last_profile_id=profile_id)
# 		db.edit_profile_status(str(message.from_user.id), db.search_profile_status(str(message.from_user.id))[0])






@dp.message_handler(state=SearchProfile.in_doing)
async def seach_profile_step3(message: types.Message, state: FSMContext):
	await send_log(message)

	if (bool(len(db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]),
								   str(db.get_info(str(message.from_user.id))[8]),
								   str(db.get_info(str(message.from_user.id))[7]))))):
		try:
			profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]), str(db.get_info(str(message.from_user.id))[8]), str(db.get_info(str(message.from_user.id))[7]))
		except:
			db.edit_zero_profile_status(message.from_user.id)
			profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]), str(db.get_info(str(message.from_user.id))[8]), str(db.get_info(str(message.from_user.id))[7]))
		await state.update_data(last_profile_id=profile_id)
		db.edit_profile_status(str(message.from_user.id), db.search_profile_status(str(message.from_user.id))[0])

	# кнопки для оценки
	button_like = KeyboardButton('👍')

	button_dislike = KeyboardButton('👎')

	button_other = KeyboardButton('Всячина👜')

	button_report = KeyboardButton('Репорт👺')

	mark_menu = ReplyKeyboardMarkup()

	mark_menu.add(button_dislike, button_like, button_report, button_other)

	name_profile = str(db.get_info(profile_id)[3])
	age_profile = str(db.get_info(profile_id)[8])
	description_profile = str(db.get_info(profile_id)[4])
	photo_profile = open('photo_user/' + str(profile_id) + '.jpg', 'rb')

	city = str(db.get_info_user(profile_id)[4])

	final_text_profile = f'Смотри, кого для тебя нашёл☺️\n\n{name_profile},{age_profile},{city}\n{description_profile}'

	await message.answer_photo(photo_profile, caption=final_text_profile, reply_markup=mark_menu)


	'''Функция поиска анкет после отправки пользователя своей оценки(лайк,дизлайк,репорт)'''
	#await send_log(message)
	try:
		if str(message.text) == '👍':
			if str(message.text) == '/start' or str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)

			user_data = await state.get_data()

			try:
				profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]), str(db.get_info(str(message.from_user.id))[8]),str(db.get_info(str(message.from_user.id))[7]))[db.search_profile_status(str(message.from_user.id))[0]][0]
			except IndexError:
				db.edit_zero_profile_status(message.from_user.id)
				profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]), str(db.get_info(str(message.from_user.id))[8]),str(db.get_info(str(message.from_user.id))[7]))[db.search_profile_status(str(message.from_user.id))[0]][0]
			except Exception as e:
				print(e)
				await state.finish()
				await magic_start(message)
			await state.update_data(last_profile_id=profile_id)
			if db.add_like_exists(str(message.from_user.id),user_data['last_profile_id']) == False:
				db.add_like(str(message.from_user.id), user_data['last_profile_id'])
				db.up_rating(db.check_rating(message.from_user.id)[0], user_data['last_profile_id'])
			db.edit_profile_status(str(message.from_user.id), db.search_profile_status(str(message.from_user.id))[0])
			name_profile = str(db.get_info(message.from_user.id)[3])
			age_profile = str(db.get_info(message.from_user.id)[8])
			description_profile = str(db.get_info(message.from_user.id)[4])

			photo_profile = open('photo_user/' + str(message.from_user.id) + '.jpg','rb')

			city = str(user_data['search_profile_city']).title()

			final_text_profile = f'Смотри, кого для тебя нашёл☺️\n\n{name_profile},{age_profile},{city}\n{description_profile}'

			await message.answer_photo(photo_profile,caption=final_text_profile)

			name_profile_self = str(db.get_info(str(message.from_user.id))[3])
			age_profile_self = str(db.get_info(str(message.from_user.id))[8])
			description_profile_self = str(db.get_info(str(message.from_user.id))[4])

			photo_profile_self = open('photo_user/' + str(message.from_user.id) + '.jpg','rb')

			final_text_profile_self = f'Тобой кто то заинтересовался!\nСам в шоке😮..\n\n{name_profile_self},{age_profile_self},{city}\n{description_profile_self}\n\nЧего ты ждёшь,беги знакомиться - @{str(message.from_user.username)}'

			await bot.send_photo(user_data['last_profile_id'],photo_profile_self,caption=final_text_profile_self)


			return
			await state.finish()
		elif str(message.text) == '👎':
			if str(message.text) == '/start' or str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)

			user_data = await state.get_data()

			try:
				profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]), str(db.get_info(str(message.from_user.id))[8]),str(db.get_info(str(message.from_user.id))[7]))
			except IndexError:
				db.edit_zero_profile_status(message.from_user.id)
				profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[4]), str(db.get_info(str(message.from_user.id))[8]),str(db.get_info(str(message.from_user.id))[7]))
			except Exception as e:
				print(e)
				await state.finish()
				await magic_start(message)

			await state.update_data(last_profile_id=profile_id)

			db.edit_profile_status(str(message.from_user.id),db.search_profile_status(str(message.from_user.id))[0])
			name_profile = str(db.get_info(profile_id[0][0])[3])
			age_profile = str(db.get_info(profile_id[0][0])[8])
			description_profile = str(db.get_info(profile_id[0][0])[4])
			social_link_profile = str(db.get_info(profile_id[0][0])[9])
			photo_profile = open('photo_user/' + str(profile_id[0][0]) + '.jpg','rb')

			city = str(user_data['search_profile_city']).title()

			final_text_profile = f'Смотри, кого для тебя нашёл☺️\n\n{name_profile},{age_profile},{city}\n{description_profile}'

			await message.answer_photo(photo_profile, caption=final_text_profile)
		elif str(message.text) == 'Репорт👺':

			if str(message.text) == '/start' or str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)

			user_data = await state.get_data()



			try:
				profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[6]),str(db.get_info(str(message.from_user.id))[8]),str(db.get_info(str(message.from_user.id))[7]))[db.search_profile_status(str(message.from_user.id))[0]][0]
			except IndexError:
				db.edit_zero_profile_status(message.from_user.id)
				profile_id = db.search_profile(str(db.get_info_user(str(message.from_user.id))[6]),str(db.get_info(str(message.from_user.id))[8]),str(db.get_info(str(message.from_user.id))[7]))[db.search_profile_status(str(message.from_user.id))[0]][0]
			except Exception as e:
				print(e)
				await state.finish()
				await magic_start(message)
			#отправка репорта
			await state.update_data(last_profile_id=profile_id)
			if(db.report_exists(str(message.from_user.id),user_data['last_profile_id']) == False):
				db.throw_report(str(message.from_user.id),user_data['last_profile_id'])
				await message.answer('Репорт отправлен!\nСпасибо за улучшение комьюнити🥰')
			else:
				await message.answer('У вас уже есть репорт на данную анкету!\nЧёж вы его так хейтите..😦')
			db.edit_profile_status(str(message.from_user.id),db.search_profile_status(str(message.from_user.id))[0])

			name_profile = str(db.get_info(profile_id[0][0])[3])
			age_profile = str(db.get_info(profile_id[0][0])[8])
			description_profile = str(db.get_info(profile_id[0][0])[4])

			photo_profile = open('photo_user/' + str(profile_id[0][0]) + '.jpg', 'rb')

			city = str(user_data['search_profile_city']).title()

			final_text_profile = f'Смотри, кого для тебя нашёл☺️\n\n{name_profile},{age_profile},{city}\n{description_profile}'

			await message.answer_photo(photo_profile,caption=final_text_profile)
		elif str(message.text) == 'Всячина👜':
			await other(message)
		elif str(message.text) == 'Откат действий◀️':
			await backup(message)
		else:
			await state.finish()
			await magic_start(message)
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		await state.finish()
		await magic_start(message)
		print(e)
		return

''''''

#хендлер всячины
@dp.message_handler(lambda message: message.text == 'Всячина')
async def other(message : types.Message):
	'''Функция срабатывает при нажатии на кнопку всячина'''
	await send_log(message)
	#кнопки для всякой всячины

	button_backup = KeyboardButton('Откат действий◀️')

	button_exit = KeyboardButton('Выйти❌')

	menu_other = ReplyKeyboardMarkup()

	menu_other.add(button_exit,button_backup)
	await message.answer('Тут так же можно выполнить много хитрых и не очень махинаций',reply_markup=menu_other)


#класс машины состояний FSM для отката действий
class Backup(StatesGroup):
	step1 = State()
	mark = State()

#хендлер отката действий
@dp.message_handler(lambda message: message.text == 'Откат действий◀️')
async def backup(message : types.Message):
	await send_log(message)
	await message.answer('Часто бывает, что в потоке скучных анкет натыкаешься на “самородок”, но случайно нажимаешь диз по рефлексу.\n\nС помощью этой функции ты сможешь лайкнуть любую анкету!\nПросто перечисли имя,возвраст,город и описание.\n\nПример -  глэк,18,гомель,люблю питсу')
	await message.answer_sticker('CAACAgIAAxkBAAED6aNfAAFG6dxnzzi3__WF6jWbJ7YPNYsAAkICAAKezgsAAVYiws5K51M1GgQ')
	await Backup.step1.set()

@dp.message_handler(state=Backup.step1)
async def backup_step1(message: types.Message, state: FSMContext):
	await send_log(message)
	try:
		if message.text == 'Выйти❌':
			await magic_start(message)
			await state.finish()
		msg_text = message.text

		msg_split = msg_text.split(',')

		name = msg_split[0]
		age = msg_split[1]
		city = msg_split[2].lower()
		description = msg_split[3]

		final = name + age + city + description
		if len(db.backup(name,age,city,description)) == 1:
			print(db.backup(name,age,city,description)[0][0])
			photo_profile_self = open('photo_user/' + db.backup(name,age,city,description)[0][0] + '.jpg','rb')

			#кнопки для оценки
			button_like = KeyboardButton('👍')

			button_dislike = KeyboardButton('👎')

			mark_menu_other = ReplyKeyboardMarkup()

			mark_menu_other.add(button_dislike,button_like)

			name_profile = str(db.get_info(db.backup(name,age,city,description)[0][0])[3])
			age_profile = str(db.get_info(db.backup(name,age,city,description)[0][0])[8])
			description_profile = str(db.get_info(db.backup(name,age,city,description)[0][0])[4])
			social_link_profile = str(db.get_info(db.backup(name,age,city,description)[0][0])[9])
			city = str(db.get_info(db.backup(name,age,city,description)[0][0])[5])

			await state.update_data(last_backup=db.backup(name,age,city,description)[0][0])

			final_text_profile = f'Смотри, кого для тебя нашёл☺️\n\n{name_profile},{age_profile},{city}\n{description_profile}'
			print(final_text_profile)
			await message.answer_photo(photo_profile_self,caption=final_text_profile,reply_markup=mark_menu_other)
			await Backup.next()
		else:
			await message.answer('Я не смогу обработать данную анкету!\nВыбери другую!')
			print(len(db.backup(name,age,city,description)))
			return
	except Exception as e:
		await message.answer('Я не смогу обработать данную анкету!\nВыбери другую!')
		print(len(db.backup(name,age,city,description)))
		print(e)
		return

@dp.message_handler(state=Backup.mark)
async def backup_step2(message: types.Message, state: FSMContext):
	user_data = await state.get_data()
	print('хуй')
	if str(message.text) == '👍':
		await message.answer('Ответ отправлен!')

		photo_self = open(f'photo_user/{message.from_user.id}.jpg','rb')
		name_profile_self = str(db.get_info(str(message.from_user.id))[3])
		age_profile_self = str(db.get_info(str(message.from_user.id))[8])
		description_profile_self = str(db.get_info(str(message.from_user.id))[4])
		social_link_profile_self = str(db.get_info(str(message.from_user.id))[9])
		city = str(db.get_info(str(message.from_user.id))[5])

		photo_profile_self = open('photo_user/' + str(message.from_user.id) + '.jpg','rb')


		final_text_profile_self = f'Тобой кто то заинтересовался!\nСам в шоке😮..\n\n{name_profile_self},{age_profile_self},{city}\n{description_profile_self}\n\nЧего ты ждёшь,беги знакомиться - @{str(message.from_user.username)}'

		await bot.send_photo(str(user_data['last_backup']),photo_self,caption=final_text_profile_self)
		await state.finish()
		await magic_start(message)
	elif message.text == '👎':
		await message.answer('Ответ отправлен!')
		await state.finish()
		await magic_start(message)
	else:
		await message.answer('Нет такого варианта ответа!')
		return
	await send_log(message)


''''''
#админка
@dp.message_handler(lambda message: message.text == 'Админка⚙️')
async def admin(message: types.Message):
	if message.from_user.id in config.ADMIN_LIST:

		await message.answer('Для отправки сообщений нужно написать /sendmsg_admin,user_id,msg')
	else:
		await message.answer('Отказано в доступе')

@dp.message_handler(lambda message: message.text.startswith('/sendmsg_admin'),state='*')
async def admin_send_msg(message: types.Message):
	if message.from_user.id in config.ADMIN_LIST:
		msg = message.text.split(',')
		await bot.send_message(msg[1], msg[2])
		await message.answer('')
	else:
		await message.answer('Отказано в доступе')


# @dp.message_handler(commands='que')
# async def que(msg: types.Message):
# 	await msg.answer(db.all_profile(msg.from_user.id))
# 	await msg.answer((db.all_profile(msg.from_user.id)[0][3]).title())
# 	await msg.answer(db.all_profile(msg.from_user.id)[0][4])
# 	await msg.answer(db.all_profile(msg.from_user.id)[0][5])
# 	await msg.answer(db.all_profile(msg.from_user.id)[0][6])
# 	await msg.answer(db.all_profile(msg.from_user.id)[0][8])


@dp.message_handler(state='*')
async def send_log(message: types.Message):
	await bot.send_message(5302034245,f'ID - {str(message.from_user.id)}\nusername - {str(message.from_user.username)}\nmessage - {str(message.text)}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)