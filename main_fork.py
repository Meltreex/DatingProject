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
from DataPostgre import dbworker
import config
import KeyboardButton as kb
import os.path
from config import host, user, password, db_name

BOT_TOKEN = '6261688795:AAGS3FO8s6CrrvSUgCc8GUeAyljhLEgiU9Y'

#задаём логи and инициализируем бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

#инициализируем базу данных
db = dbworker(host, user, password, db_name)


#хендлер команды /start
@dp.message_handler(commands=['start'], state='*')
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
@dp.message_handler(state=CreateProfile.city, content_types=[ContentType.LOCATION, types.ContentType.TEXT])
async def create_profile_city(message: types.Message, state: FSMContext):

	if message.content_type == types.ContentType.LOCATION:
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
	elif message.content_type == types.ContentType.TEXT:
		city = message.text.title()  # Получаем текст сообщения (город)
		await state.update_data(profile_city=city.lower())
		await message.answer('Прелестно, теперь добавим фотокарточку🖼\n\nВажно отправлять фотографией, а не файлом!', reply_markup=kb.btn_for_exit())
		await CreateProfile.next()


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
async def edit_profile_age(message: types.Message):
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
async def search_profile(message: types.Message, state: FSMContext):
	'''Функция для ввода пользователя своего города,последующей записи в бд'''
	await send_log(message)
	try:
		if db.profile_exists(message.from_user.id) == False:
			await message.answer('У тебя нет анкеты, заполни её а потом приходи сюда!')
		else:
			if (bool(len(db.search_profile(str(db.get_info(message.from_user.id)[8]),
										   str(db.get_info(message.from_user.id)[7]))))):
				try:
					profile_id = db.search_profile(str(db.get_info(message.from_user.id)[8]),
												   str(db.get_info(message.from_user.id)[7]))[
						db.search_profile_status(message.from_user.id)[0]][0]
				except:
					db.edit_zero_profile_status(message.from_user.id)
					profile_id = db.search_profile(str(db.get_info(message.from_user.id)[8]),
												   str(db.get_info(message.from_user.id)[7]))[
						db.search_profile_status(message.from_user.id)[0]][0]
				await state.update_data(last_profile_id=profile_id)
				db.edit_profile_status(str(message.from_user.id),
									   db.search_profile_status(str(message.from_user.id))[0])

				# кнопки для оценки
				button_like = KeyboardButton('👍')

				button_dislike = KeyboardButton('👎')

				button_other = KeyboardButton('Выйти❌')

				mark_menu = ReplyKeyboardMarkup()

				mark_menu.add(button_dislike, button_like, button_other)

				name_profile = str(db.get_info(profile_id)[3])
				age_profile = str(db.get_info(profile_id)[8])
				description_profile = str(db.get_info(profile_id)[4])
				photo_profile = db.get_info(profile_id)[6]

				city = str(db.get_info(profile_id)[5])

				final_text_profile = f'{name_profile},{age_profile},{city} - {description_profile}'

				await message.answer_photo(photo_profile, caption=final_text_profile, reply_markup=mark_menu)

				await SearchProfile.next()
			else:
				await message.answer('Такого города нет или там нет анкет :(')
				await state.finish()

			await SearchProfile.in_doing.set()
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return


@dp.message_handler(state=SearchProfile.in_doing)
async def seach_profile_step3(message: types.Message, state: FSMContext):
	'''Функция поиска анкет после отправки пользователя своей оценки(лайк,дизлайк,репорт)'''
	await send_log(message)
	try:
		if str(message.text) == '👍':
			if str(message.text) == '/start' or str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)

			user_data = await state.get_data()

			try:
				profile_id = db.search_profile(str(db.get_info(message.from_user.id)[8]), str(db.get_info(message.from_user.id)[7]))[db.search_profile_status(message.from_user.id)[0]][0]
			except IndexError:
				db.edit_zero_profile_status(message.from_user.id)
				profile_id = db.search_profile(str(db.get_info(message.from_user.id)[8]), str(db.get_info(message.from_user.id)[7]))[db.search_profile_status(message.from_user.id)[0]][0]
			except Exception as e:
				print(e)
				await state.finish()
				await magic_start(message)
			await state.update_data(last_profile_id=profile_id)
			if db.add_like_exists(str(message.from_user.id), user_data['last_profile_id']) == False:
				db.add_like(str(message.from_user.id), user_data['last_profile_id'])
			db.edit_profile_status(message.from_user.id, db.search_profile_status(str(message.from_user.id))[0])
			name_profile = str(db.get_info(profile_id)[3])
			age_profile = str(db.get_info(profile_id)[8])
			description_profile = str(db.get_info(profile_id)[4])

			photo_profile = db.get_info(profile_id)[6]

			city = str(db.get_info(profile_id)[5]).title()

			final_text_profile = f'Смотри, кого для тебя нашёл☺️\n\n{name_profile},{age_profile},{city} - {description_profile}'

			await message.answer_photo(photo_profile, caption=final_text_profile)

			name_profile_self = str(db.get_info(message.from_user.id)[3])
			age_profile_self = str(db.get_info(message.from_user.id)[8])
			description_profile_self = str(db.get_info(message.from_user.id)[4])

			photo_profile_self = db.get_info(message.from_user.id)[6]

			final_text_profile_self = f'Тобой кто то заинтересовался!\nСам в шоке😮..\n\n{name_profile_self}, {age_profile_self}, {city} - {description_profile_self}\n\nЧего ты ждёшь,беги знакомиться - @{str(message.from_user.username)}'

			await bot.send_photo(user_data['last_profile_id'], photo_profile_self, caption=final_text_profile_self)


			return
			await state.finish()
		elif str(message.text) == '👎':
			if str(message.text) == '/start' or str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)

			user_data = await state.get_data()

			try:
				profile_id = db.search_profile(str(db.get_info(message.from_user.id)[8]), str(db.get_info(message.from_user.id)[7]))[db.search_profile_status(message.from_user.id)[0]][0]
			except IndexError:
				db.edit_zero_profile_status(message.from_user.id)
				profile_id = db.search_profile(str(db.get_info(message.from_user.id)[8]), str(db.get_info(message.from_user.id)[7]))[db.search_profile_status(message.from_user.id)[0]][0]
			except Exception as e:
				print(e)
				await state.finish()
				await magic_start(message)

			await state.update_data(last_profile_id=profile_id)

			db.edit_profile_status(message.from_user.id, db.search_profile_status(message.from_user.id)[0])
			name_profile = str(db.get_info(profile_id)[3])
			age_profile = str(db.get_info(profile_id)[8])
			description_profile = str(db.get_info(profile_id)[4])
			photo_profile = db.get_info(profile_id)[6]

			city = str(db.get_info(profile_id)[5]).title()

			final_text_profile = f'Смотри, кого для тебя нашёл☺️\n\n{name_profile},{age_profile},{city} - {description_profile}'

			await message.answer_photo(photo_profile, caption=final_text_profile)
		else:
			await state.finish()
			await magic_start(message)
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		await state.finish()
		await magic_start(message)
		print(e)
		return



class Add_bot(StatesGroup):
	date = State()

#админка
@dp.message_handler(lambda message: message.text == 'Админка⚙️')
async def admin(msg: types.Message):
	if msg.from_user.id in config.ADMIN_LIST:
		await msg.answer('Приветствую вас в админ панеле!', reply_markup=kb.keyboard_forAdmins())
	else:
		await msg.answer('Отказано в доступе')


@dp.message_handler(text='Add Bot')
async def cmd_bot_admin(msg: types.Message):
	if msg.from_user.id in config.ADMIN_LIST:
		await send_log(msg)
		await bot.send_message(msg.from_user.id, 'Для создания бота отправь мне фото и подпись к ней в формате(имя-описание-город-пол-возраст)')
		await Add_bot.date.set()
	else:
		await msg.answer('Отказано в доступе')

@dp.message_handler(content_types=['photo'], state=Add_bot.date)
async def add_bot_desc(msg: types.Message, state: FSMContext):
	try:
		if msg.from_user.id in config.ADMIN_LIST:
			if str(msg.text) == 'Выйти❌':
				await state.finish()
				await magic_start(msg)

			photo_id = msg.photo[-1].file_id
			caption = msg.caption
			mss_caption = caption.split('-')
			tg_id = config.chat_id_group
			tg_username = '@---'
			name_profile = mss_caption[0]
			description_profile = mss_caption[1]
			city = mss_caption[2]
			sex = mss_caption[3]
			age_profile = mss_caption[4]

			final_text = f'{name_profile},{age_profile},{city} - {description_profile}'
			await bot.send_photo(msg.from_user.id, photo=photo_id, caption=final_text)
			db.create_profile(tg_id, tg_username, name_profile, description_profile, city, photo_id, sex, age_profile)
			await state.finish()
		else:
			await msg.answer('Отказано в доступе')
	except Exception as e:
		await msg.answer(cus_ans.random_reapeat_list())
		await state.finish()
		await magic_start(msg)
		print(e)
		return


@dp.message_handler(lambda message: message.text.startswith('/sendmsg_admin'), state='*')
async def admin_send_msg(message: types.Message):
	if message.from_user.id in config.ADMIN_LIST:
		msg = message.text.split(',')
		await bot.send_message(msg[1], msg[2])
		await message.answer('')
	else:
		await message.answer('Отказано в доступе')


@dp.message_handler(state='*')
async def send_log(message: types.Message):
	await bot.send_message(config.chat_id_group,f'ID - {str(message.from_user.id)}\nusername - {str(message.from_user.username)}\nmessage - {str(message.text)}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
