import psycopg2


class dbworker:
    def __init__(self, host, user, password, db_name):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        self.cursor = self.connection.cursor()


    '''Добавляем нового юзера'''
    def add_user(self, telegram_username, telegram_id, full_name):
        with self.connection:
            return self.cursor.execute("INSERT INTO users(telegram_username, telegram_id, full_name) VALUES (%s, %s, %s)", (telegram_username, telegram_id, full_name))


    '''Проверка есть ли юзер в бд'''
    def user_exists(self, user_id):
        with self.connection:
            self.cursor.execute('SELECT * FROM users WHERE telegram_id = %s', (user_id, ))
            result = self.cursor.fetchall()
            return bool(result)

    '''Проверка есть ли анкета в бд'''
    def profile_exists(self, user_id):
        with self.connection:
            self.cursor.execute('SELECT * FROM profile_list WHERE telegram_id = %s', (user_id, ))
            result = self.cursor.fetchall()
            return bool(len(result))

    '''Создаём анкету'''
    def create_profile(self, telegram_id, telegram_username, name, description, city, photo, sex, age, hobbies):
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO profile_list (telegram_id, telegram_username, name, description, city, photo, sex, age, hobbies) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (telegram_id, telegram_username, name, description, city, photo, sex, age, hobbies))

    '''Удаление анкеты'''
    def delete_profile(self, user_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM profile_list WHERE telegram_id = %s", (user_id, ))

    '''поиск по анкетам'''
    def all_profile(self, user_id):
        with self.connection:
            self.cursor.execute("SELECT * FROM profile_list WHERE telegram_id = %s", (user_id, ))
            return self.cursor.fetchall()

    '''изменение описания'''
    def edit_description(self, description, user_id):
        with self.connection:
            return self.cursor.execute('UPDATE profile_list SET description = %s WHERE telegram_id = %s',(description, user_id))

    '''изменение возвраста'''
    def edit_age(self, age, user_id):
        with self.connection:
            return self.cursor.execute('UPDATE profile_list SET age = %s WHERE telegram_id = %s', (age, user_id))

    '''поиск хаты'''
    def search_profile(self, age, sex):
        try:
            if str(sex) == 'мужчина':
                sex_search = 'женщина'
            else:
                sex_search = 'мужчина'
            with self.connection:
                self.cursor.execute("SELECT telegram_id FROM profile_list WHERE sex = %s ORDER BY age DESC",
                                    (sex_search, ))
                return self.cursor.fetchall()
        except Exception as e:
            print(e)

    '''получение информации по профилю'''
    def get_info(self, user_id):
        with self.connection:
            self.cursor.execute("SELECT * FROM profile_list WHERE telegram_id = %s", (user_id,))
            return self.cursor.fetchone()

    '''изменение статуса на 0 когда анкеты заканчиваются'''
    def edit_zero_profile_status(self, user_id):
        with self.connection:
            return self.cursor.execute('UPDATE users SET search_id = 0 WHERE telegram_id = %s', (user_id, ))

    '''возвращение статуса'''
    def search_profile_status(self, user_id):
        with self.connection:
            self.cursor.execute("SELECT search_id FROM users WHERE telegram_id = %s", (user_id,))
            return self.cursor.fetchone()

    '''изменение статуса'''
    def edit_profile_status(self, user_id, num):
        with self.connection:
            return self.cursor.execute('UPDATE users SET search_id = %s WHERE telegram_id = %s',(str(int(num) + 1), user_id))

    def add_like_exists(self, sender, recipient):
        with self.connection:
            self.cursor.execute('SELECT * FROM likes WHERE sender = %s AND recipient = %s', (sender, recipient))
            result = self.cursor.fetchall()
            return bool(len(result))

    '''добавление лайка в таблицу'''
    def add_like(self, sender, recipent):
        with self.connection:
            return self.cursor.execute('INSERT INTO likes (sender, recipient) VALUES(%s, %s)', (sender, recipent))

    '''Возвращает кол-во ботов'''
    def get_count_bot(self):
        with self.connection:
            self.cursor.execute("""
            SELECT "ID" FROM profile_list WHERE telegram_username = '@---'""")
            return self.cursor.fetchall()

    '''Возвращает анкету по id'''
    def get_profile(self, id):
        with self.connection:
            self.cursor.execute("""
            SELECT * FROM profile_list WHERE "ID" = %s""", (id, ))
            return self.cursor.fetchall()

    '''Удаляет анкету по id'''
    def request_delete_profile(self, id):
        with self.connection:
            self.cursor.execute("""DELETE FROM profile_list WHERE "ID" = %s""", (id, ))

    '''Возвращает id, принимает tg_id'''
    def return_id(self, tg_id):
        with self.connection:
            self.cursor.execute("""
            SELECT "ID" FROM profile_list WHERE telegram_id = %s""", (tg_id, ))
            return self.cursor.fetchall()