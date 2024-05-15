import logging

import aiogram.utils.exceptions
import aiohttp


#aiogram и всё утилиты для коректной работы с Telegram API
from aiogram import Bot, types, executor
from aiogram.dispatcher import Dispatcher
from aiogram.types.message import ContentType
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

#конфиг с настройками
#кастомные ответы
from cmd_bot.datingbot.DataPostgre import dbworker
from cmd_bot.datingbot import config, custom_answer as cus_ans, KeyboardButton as kb
from cmd_bot.datingbot.config import host, user, password, db_name
from state import CreateProfile, SearchProfile, EditProfile, Add_bot, check_id, req_del, QuestionStatesGroup

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
	await msg.answer('Привет!\nЯ помогу найти тебе вторую половинку или просто друзей👫', reply_markup=kb.start())
	if (not db.user_exists(msg.from_user.id)):
		db.add_user(msg.from_user.username, msg.from_user.id, msg.from_user.full_name)
		await bot.send_message(config.chat_id_group, f'[INFO]Новый пользователь!\nID - {str(msg.from_user.id)}\nusername - {str(msg.from_user.username)}')


#Функция для определения города по координатам
async def get_city_name(latitude, longitude):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json") as response:
            data = await response.json()
            city = data.get('address', {}).get('city')
            return city


@dp.message_handler(lambda msg: msg.text == 'Давай начнем👌' or msg.text == '/magic_start', state='*')
async def magic_start(msg: types.Message):
	'''Функция для меню самого бота'''
	#кнопки меню
	button_search = KeyboardButton('Поиск🔍')
	button_create_profile = KeyboardButton('Создать анкету📌')
	button_edit_profile = KeyboardButton('Профиль')
	button_remove_profile = KeyboardButton('Удалить🗑')
	button_admin = KeyboardButton('Админка⚙️')
	menu = ReplyKeyboardMarkup(resize_keyboard=True)

	if (not db.profile_exists(msg.from_user.id)):
			menu.add(button_search, button_create_profile)
	elif (db.profile_exists(msg.from_user.id)):
		menu.add(button_search, button_edit_profile, button_remove_profile)
	if msg.from_user.id in config.ADMIN_LIST:
		menu.add(button_admin)
	await msg.answer('Тебя обязательно найдут, подождем...', reply_markup=menu)


#хендлер старта для создания анкеты
@dp.message_handler(lambda message: message.text == 'Создать анкету📌', state='*')
async def create_profile(message: types.Message):
	if message.from_user.username != None:
		if(not db.profile_exists(message.from_user.id)):
			await message.answer("Для того что бы создать твою анкету нужно заполнить несколько пунктов\n\nДавай начнём с имени, как мне тебя называть?😉", reply_markup=kb.btn_exit())
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
	if len(message.text) < 250 and (not str(message.text) in cus_ans.ban_symvols):
		await state.update_data(profile_description=message.text)
		await message.answer('Из какого ты города?\nОтправь мне свою геолокацию👇 или напиши с клавиатуры', reply_markup=kb.keyboard_for_loc())
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
			await message.answer('Отлично, теперь добавим фото🖼\n\nВажно отправлять фотографией, а не файлом!')
			await CreateProfile.next()
		elif str(message.text) in cus_ans.ban_symvols:
			await message.answer('У тебя в сообщении запрещённые символы🤬🤬\nЗапятая к примеру', reply_markup=kb.keyboard_for_loc())
		else:
			await message.answer(cus_ans.random_reapeat_list())
			#прерывание функции
			return
	elif message.content_type == types.ContentType.TEXT:
		city = message.text.title()  # Получаем текст сообщения (город)
		if str(message.text) == 'Выйти❌':
			await state.finish()
			await magic_start(message)
			return
		if len(city) < 35 and (not str(city) in cus_ans.ban_symvols):
			await state.update_data(profile_city=city.lower())
			await message.answer('Отлично, теперь добавим фото🖼\n\nВажно отправлять фотографией, а не файлом!')
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
	file_id = message.photo[-1].file_id
	await state.update_data(photo=file_id)
	await message.answer('Осталось совсем немного, укажи свой пол', reply_markup=kb.btn_gender())
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
		await message.answer('Замечательно!\nДавай узнаем твой возвраст')
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
		if int(message.text) < 13:
			await message.answer('Пожалуйста, укажите верный возраст.')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 71:
			await message.answer('Пожалуйста, укажите верный возраст.‍')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 6 and int(message.text) < 54:
			await state.update_data(profile_age=message.text)
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


@dp.message_handler(lambda message: message.text == 'Ред. анкету📝')
async def edit_profile(message: types.Message):
	'''Функция для меню редактирования анкеты'''
	await send_log(message)
	try:
		if(not db.profile_exists(message.from_user.id)):
			await message.answer('У тебя нет анкеты!')
		elif(db.profile_exists(message.from_user.id)) :
			photo = db.all_profile(message.from_user.id)[0][6]
			caption = 'Твоя анкета:\n\nИмя - ' + str(db.all_profile(message.from_user.id)[0][3]).title() + '\nОписание - ' + str(db.all_profile(message.from_user.id)[0][4]) + '\nГород🌎 - ' + str(db.all_profile(message.from_user.id)[0][5]).title() + '\nВозраст - ' + str(db.all_profile(message.from_user.id)[0][8])
			await message.answer_photo(photo, caption=caption, reply_markup=kb.btn_edit())
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return


#хендлер для заполнения анкеты заново
@dp.message_handler(lambda message: message.text == 'Заполнить заново🔄')
async def edit_profile_again(message: types.Message):
	'''Функция для заполнения анкеты заново'''
	await send_log(message)
	try:
		db.delete_profile(message.from_user.id)
		await create_profile(message)

	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return


#хендлеры для изменение возвраста и описания анкеты
@dp.message_handler(lambda message: message.text == 'Изменить возраст👶' or message.text == 'Изменить описание📝')
async def edit_profile_age(message: types.Message):
	try:
		if message.text == 'Изменить возраст👶':
			await message.answer('Введи свой возвраст', reply_markup=kb.btn_cancel())
			await EditProfile.age_edit.set()
		elif message.text == 'Изменить описание📝':
			await message.answer('Введи новое описание своей анкеты!', reply_markup=kb.btn_cancel())
			await EditProfile.description_edit.set()
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		print(e)
		return

@dp.message_handler(state=EditProfile.age_edit)
async def edit_profile_age_step2(message: types.Message, state: FSMContext):
	await send_log(message)
	try:
		if str(message.text) == 'Отменить❌':
			await state.finish()
			await magic_start(message)

			return
		elif int(message.text) < 13:
			await message.answer('Пожалуйста, укажите верный возраст.')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 71:
			await message.answer('Пожалуйста, укажите верный возраст.')
			await message.answer(cus_ans.random_reapeat_list())

			#прерывание функции
			return
		elif int(message.text) > 6 and int(message.text) < 54:
			await message.answer('Возвраст успешно измененён!')
			await state.update_data(edit_profile_age=message.text)
			user_data = await state.get_data()

			db.edit_age(user_data['edit_profile_age'], str(message.from_user.id))
			await state.finish()
			await edit_profile(message)
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
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
		await message.answer('Описание успешно изменено!')
		await state.update_data(edit_profile_description=message.text)
		user_data = await state.get_data()

		db.edit_description(user_data['edit_profile_description'], str(message.from_user.id))
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


#хендлеры для поиска по анкетам
@dp.message_handler(lambda message: message.text == 'Поиск🔍')
async def search_profile(message: types.Message, state: FSMContext):
	'''Функция для ввода пользователя своего города,последующей записи в бд'''
	await send_log(message)
	try:
		if db.profile_exists(message.from_user.id) == False:
			await message.answer('У тебя нет анкеты, заполни её, а потом приходи сюда!')
		else:
			if (bool(len(db.search_profile(str(db.get_info(message.from_user.id)[8]), str(db.get_info(message.from_user.id)[7]))))):
				try:
					profile_id = db.search_profile(str(db.get_info(message.from_user.id)[8]), str(db.get_info(message.from_user.id)[7]))[db.search_profile_status(message.from_user.id)[0]][0]
				except:
					db.edit_zero_profile_status(message.from_user.id)
					profile_id = db.search_profile(str(db.get_info(message.from_user.id)[8]), str(db.get_info(message.from_user.id)[7]))[db.search_profile_status(message.from_user.id)[0]][0]
				await state.update_data(last_profile_id=profile_id)
				db.edit_profile_status(str(message.from_user.id), db.search_profile_status(str(message.from_user.id))[0])

				name_profile = str(db.get_info(profile_id)[3])
				age_profile = str(db.get_info(profile_id)[8])
				description_profile = str(db.get_info(profile_id)[4])
				photo_profile = db.get_info(profile_id)[6]

				city = str(db.get_info(profile_id)[5])

				final_text_profile = f'{name_profile},{age_profile},{city} - {description_profile}'

				await message.answer_photo(photo_profile, caption=final_text_profile, reply_markup=kb.btn_estimator())

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
		if str(message.text) == '❤️':
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
				db.add_like(message.from_user.id, user_data['last_profile_id'])
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
			city = str(db.get_info(message.from_user.id)[5]).title()

			final_text_profile_self = f'Тобой кто то заинтересовался!\n\n{name_profile_self}, {age_profile_self}, {city} - {description_profile_self}\n\nЧего ты ждёшь,беги знакомиться - @{str(message.from_user.username)}'

			await bot.send_photo(user_data['last_profile_id'], photo_profile_self, caption=final_text_profile_self)


			return
			await state.finish()
		elif str(message.text) == '👎':
			if str(message.text) == '/start' or str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)

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
	except aiogram.utils.exceptions.ChatNotFound:
		await bot.send_message(config.chat_id_group, f'[INFO] Репорт, поставили лайк ID - {db.return_id(profile_id)}')
	except Exception as e:
		await message.answer(cus_ans.random_reapeat_list())
		await state.finish()
		await magic_start(message)
		print(e)
		return

### Код для тестов/опросов

@dp.message_handler(lambda message: message.text == 'Профиль')
async def admin(msg: types.Message):
	await bot.send_message(msg.chat.id, 'Ваш профиль⬇️', reply_markup=kb.btn_for_btnprofile())


@dp.message_handler(lambda message: message.text == 'Опросы')
async def cmd_create(msg: types.Message):
    await msg.reply('Ответишь на несколько вопросов?\nПервый:\n\nЯ открытый к общению человек', reply_markup=kb.keyboard_for_question())
    await QuestionStatesGroup.q1.set()    # Установили состояние фото


@dp.message_handler(state=QuestionStatesGroup.q1)
async def q1(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que1=1.0)

        await msg.reply('Я часто подвержен стрессу и тревоге', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que1=0.5)

        await msg.reply('Я часто подвержен стрессу и тревоге', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que1=0.0)

        await msg.reply('Я часто подвержен стрессу и тревоге', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que1=-0.5)

        await msg.reply('Я часто подвержен стрессу и тревоге', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que1=-1.0)

        await msg.reply('Я часто подвержен стрессу и тревоге', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q2)
async def q2(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que2=1.0)

        await msg.reply('Я разносторонний человек и всегда готов к приобретению нового опыта', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que2=0.5)

        await msg.reply('Я разносторонний человек и всегда готов к приобретению нового опыта', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que2=0.0)

        await msg.reply('Я разносторонний человек и всегда готов к приобретению нового опыта', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que2=-0.5)

        await msg.reply('Я разносторонний человек и всегда готов к приобретению нового опыта', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que2=-1.0)

        await msg.reply('Я разносторонний человек и всегда готов к приобретению нового опыта', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q3)
async def q1(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que3=1.0)

        await msg.reply('Другие часто описывают меня как человека, проявляющего сострадание и доброту.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que3=0.5)

        await msg.reply('Другие часто описывают меня как человека, проявляющего сострадание и доброту.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que3=0.0)

        await msg.reply('Другие часто описывают меня как человека, проявляющего сострадание и доброту.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que3=-0.5)

        await msg.reply('Другие часто описывают меня как человека, проявляющего сострадание и доброту.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que3=-1.0)

        await msg.reply('Другие часто описывают меня как человека, проявляющего сострадание и доброту.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q4)
async def q1(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que4=1.0)

        await msg.reply('Меня отличает спокойствие и эмоциональная устойчивость.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que4=0.5)

        await msg.reply('Меня отличает спокойствие и эмоциональная устойчивость.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que4=0.0)

        await msg.reply('Меня отличает спокойствие и эмоциональная устойчивость.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que4=-0.5)

        await msg.reply('Меня отличает спокойствие и эмоциональная устойчивость.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que4=-1.0)

        await msg.reply('Меня отличает спокойствие и эмоциональная устойчивость.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q5)
async def q1(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que5=1.0)

        await msg.reply('Вы часто чувствуете себя уверенным в себе и своих способностях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que5=0.5)

        await msg.reply('Вы часто чувствуете себя уверенным в себе и своих способностях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que5=0.0)

        await msg.reply('Вы часто чувствуете себя уверенным в себе и своих способностях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que5=-0.5)

        await msg.reply('Вы часто чувствуете себя уверенным в себе и своих способностях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que5=-1.0)

        await msg.reply('Вы часто чувствуете себя уверенным в себе и своих способностях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q6)
async def q1(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que6=1.0)

        await msg.reply('Ты считаешь себя креативным человеком?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que6=0.5)

        await msg.reply('Ты считаешь себя креативным человеком?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que6=0.0)

        await msg.reply('Ты считаешь себя креативным человеком?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que6=-0.5)

        await msg.reply('Ты считаешь себя креативным человеком?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que6=-1.0)

        await msg.reply('Ты считаешь себя креативным человеком?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q7)
async def q1(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que7=1.0)

        await msg.reply('Когда я нахожусь в компании, я обычно делаю то, что предлагают другие, а сам инициативы не проявляю.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que7=0.5)

        await msg.reply('Когда я нахожусь в компании, я обычно делаю то, что предлагают другие, а сам инициативы не проявляю.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que7=0.0)

        await msg.reply('Когда я нахожусь в компании, я обычно делаю то, что предлагают другие, а сам инициативы не проявляю.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que7=-0.5)

        await msg.reply('Когда я нахожусь в компании, я обычно делаю то, что предлагают другие, а сам инициативы не проявляю.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que7=-1.0)

        await msg.reply('Когда я нахожусь в компании, я обычно делаю то, что предлагают другие, а сам инициативы не проявляю.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q8)
async def q1(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que8=1.0)

        await msg.reply('Вы часто испытываете чувство одиночества?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que8=0.5)

        await msg.reply('Вы часто испытываете чувство одиночества?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que8=0.0)

        await msg.reply('Вы часто испытываете чувство одиночества?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que8=-0.5)

        await msg.reply('Вы часто испытываете чувство одиночества?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que8=-1.0)

        await msg.reply('Вы часто испытываете чувство одиночества?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q9)
async def q1(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que9=1.0)

        await msg.reply('Вы склонны к проявлению агрессии или раздражения при стрессовых ситуациях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que9=0.5)

        await msg.reply('Вы склонны к проявлению агрессии или раздражения при стрессовых ситуациях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que9=0.0)

        await msg.reply('Вы склонны к проявлению агрессии или раздражения при стрессовых ситуациях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que9=-0.5)

        await msg.reply('Вы склонны к проявлению агрессии или раздражения при стрессовых ситуациях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que9=-1.0)

        await msg.reply('Вы склонны к проявлению агрессии или раздражения при стрессовых ситуациях?', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q10)
async def q1(msg: types.Message, state: FSMContext):
    if str(msg.text) == 'Выйти❌':
        await msg.answer('Опрос окончен!')
        await state.finish()
        return
    elif str(msg.text) == 'Да':
        await state.update_data(que10=1.0)

        await msg.reply('Я склонен к спонтанным поступкам, чем к действиям по плану.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее да':
        await state.update_data(que10=0.5)

        await msg.reply('Я склонен к спонтанным поступкам, чем к действиям по плану.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Неуверен':
        await state.update_data(que10=0.0)

        await msg.reply('Я склонен к спонтанным поступкам, чем к действиям по плану.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Скорее нет':
        await state.update_data(que10=-0.5)

        await msg.reply('Я склонен к спонтанным поступкам, чем к действиям по плану.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    elif str(msg.text) == 'Нет':
        await state.update_data(que10=-1.0)

        await msg.reply('Я склонен к спонтанным поступкам, чем к действиям по плану.', reply_markup=kb.keyboard_for_question())
        await QuestionStatesGroup.next()
    else:
        await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

@dp.message_handler(state=QuestionStatesGroup.q11)
async def q3(msg: types.Message, state: FSMContext):
	if str(msg.text) == 'Выйти❌':
		await msg.answer('Опрос окончен!')
		await state.finish()
		return
	elif str(msg.text) == 'Да':
		await state.update_data(que11=1.0)
	elif str(msg.text) == 'Скорее да':
		await state.update_data(que11=0.5)
	elif str(msg.text) == 'Неуверен':
		await state.update_data(que11=0.0)
	elif str(msg.text) == 'Скорее нет':
		await state.update_data(que11=-0.5)
	elif str(msg.text) == 'Нет':
		await state.update_data(que11=-1.0)
	else:
		await msg.reply('Для ответа используйте кнопки ниже!', reply_markup=kb.keyboard_for_question())

	user_data = await state.get_data()

	await bot.send_message(msg.from_user.id, f'{user_data["que1"]}, {user_data["que2"]}, {user_data["que3"]}\n{user_data["que4"]}, {user_data["que5"]}, {user_data["que6"]}\n{user_data["que7"]}, {user_data["que8"]}, {user_data["que9"]}\n{user_data["que10"]}, {user_data["que11"]}')
	await state.finish()
	await msg.answer('Опрос закончен, спасибо!\nВы сделали большой шаг для рекомендательной системы😊')
	await magic_start(msg)




### -----

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
		await bot.send_message(msg.from_user.id, 'Для создания бота отправь мне фото и подпись к ней в формате(имя-id для бота-описание-город-пол-возраст)')
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
				return
			if msg.text:
				photo_id = msg.photo[-1].file_id
				caption = msg.caption
				mss_caption = caption.split('-')
				tg_id = mss_caption[1]
				tg_username = '@---'
				name_profile = mss_caption[0]
				description_profile = mss_caption[2]
				city = mss_caption[3]
				sex = mss_caption[4]
				age_profile = mss_caption[5]

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

@dp.message_handler(text='Count-Bot')
async def get_number_bots(message: types.Message):
	if message.from_user.id in config.ADMIN_LIST:
		await bot.send_message(message.from_user.id, f'Id ботов: {db.get_count_bot()}')
	else:
		await bot.send_message(message.from_user.id, 'Отказано в доступе')

@dp.message_handler(text='Id-profile')
async def check_profile(message: types.Message):
	if message.from_user.id in config.ADMIN_LIST:
		await bot.send_message(message.from_user.id, 'Введите номер профиля(ID)')
		await check_id.id.set()
	else:
		await bot.send_message(message.from_user.id, 'Отказано в доступе')

@dp.message_handler(state=check_id.id)
async def input_id(message: types.Message, state: FSMContext):
	try:
		if message.from_user.id in config.ADMIN_LIST:
			if str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)

			array = db.get_profile(int(message.text))

			city = array[0][5]
			name = array[0][3]
			photo = array[0][6]
			description = array[0][4]
			sex = array[0][7]
			age = array[0][8]
			id = array[0][0]
			await bot.send_photo(message.from_user.id, photo=photo, caption=f'Номер - {id}\n{name}, {city}, {description}\n{sex}, {age}')

		else:
			await bot.send_message(message.from_user.id, 'Отказано в доступе')
	except Exception as e:
		await bot.send_message(message.from_user.id, cus_ans.random_reapeat_list())
		await state.finish()
		await magic_start(message)
		print(e)
		return


@dp.message_handler(text='Del-Bot')
async def check_profile(message: types.Message):
	if message.from_user.id in config.ADMIN_LIST:
		await bot.send_message(message.from_user.id, 'Введите номер профиля(ID)')
		await req_del.id.set()
	else:
		await bot.send_message(message.from_user.id, 'Отказано в доступе')


@dp.message_handler(state=req_del.id)
async def input_id(message: types.Message, state: FSMContext):
	try:
		if message.from_user.id in config.ADMIN_LIST:
			if str(message.text) == 'Выйти❌':
				await state.finish()
				await magic_start(message)

			db.request_delete_profile(int(message.text))
			await bot.send_message(message.from_user.id, 'Удалено!')
		else:
			await bot.send_message(message.from_user.id, 'Отказано в доступе')
	except Exception as e:
		await bot.send_message(message.from_user.id, cus_ans.random_reapeat_list())
		await state.finish()
		await magic_start(message)
		print(e)
		return


@dp.message_handler(state='*')
async def send_log(message: types.Message):
	await bot.send_message(config.chat_id_group, f'ID - {str(message.from_user.id)}\nusername - {str(message.from_user.username)}\nmessage - {str(message.text)}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)