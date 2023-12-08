from vk_api import VkApi
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import gspread
from datetime import datetime
import json

print('start')

GROUP_ID = '223656008'
GROUP_TOKEN = 'vk1.a.1Oko7BDg2QYMfsULXBIjYxjw_GomO5woi_VAmXt2bKp3-1h4pr2uvImK2UQVcUQltJYg0qMuq7h_7lHO-BBCZZJM28VepMHQGTa7jAg4IkWfJDWz7v-hlvw_qPlLUy5_Yrq5qg5F1GzQYmObAOi24JUbGLFkOWOiJ9y4qPHaXuwXxJlKTwz-iHnHSHyVeZDpzI1JY-6ziDfpjwk3R-b_Og'

API_VERSION = '5.120'

gc = gspread.service_account(filename="calm-vine-332204-924334d7332a.json")
sh_of_codes = gc.open_by_url('https://docs.google.com/spreadsheets/d/1nCGk8r3ILS7VbuArDtIgiMhDhgr1kk4UHlRVyjtt2EQ')
worksheet = sh_of_codes.sheet1
list_of_lists = worksheet.get_all_values()

HI = ["start", "начать", "начало", "бот", "старт", "скидки"]
text_inst = """
1. Для начала работы нажмите : "запустить бота"
2. Выберите нужную Вам  категорию, если не нашли на первой странице, нажмите : "вперед"
Затем введите номер нужной услуги и отправьте сообщением боту.
3. Также вы всегда можете найти актуальный перечень всех акций и предложений нажав кнопку : "таблица со всеми промокодами"
4. Чтобы всегда оставаться на связи, подпишитесь на нас в телеграмм канале, нажав кнопку : "Мы в Телеграме"
"""

start = 0
end = 5
categories = {}
companies_info = {}
users = []
bot_starts = {}
use_of_categories = {}

for elem in list_of_lists[1:]:
    # создаем словарь со словарями где ключ - название категории, значение -список магазинов
    if elem[8] not in categories.keys():
        categories[elem[8]] = []
    if elem[0] not in categories[elem[8]]:
        categories[elem[8]].append(elem[0])
    # создаем словарь со словарями где ключ - название магазинаб значение- инфа
    if elem[0] not in companies_info:
        companies_info[elem[0]] = []
    companies_info[elem[0]].append(elem[2:8])

vk_session = VkApi(token=GROUP_TOKEN, api_version=API_VERSION)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)

# обновляем статистику в json файлах(сохраняем сегодня за вчерашний день) условие в обработчике
def save_stats():
    with open('bot_starts.json', 'r+') as file:
        data = json.load(file)  # Загружаем старые данные(файл обязательно должен содержать данные)
        data.update(bot_starts)  # Обновляем данные
        file.seek(0)  # Перемещение к началу файла
        json.dump(data, file)  # Записываем обновленные данные

    with open('use_of_categories.json', 'r+') as file2:
        data2 = json.load(file2)
        data2.update(use_of_categories)
        file2.seek(0)
        json.dump(data2, file2)

# открываем json файл(название в параметре), выводим статистику в зависимости от параметра
def show_stats(stat_name):
    if str(stat_name) == 'bot_starts':
        with open(f'{stat_name}.json', 'r') as file:
            stat_info = json.load(file)
        stat_info = {key: value for key, value in stat_info.items() if value}
        if len(stat_info) > 0:
            stat = [f"{key} - {value} раз(а)\n" for key, value in stat_info.items()]
    elif str(stat_name) == 'use_of_categories':
        with open(f'{stat_name}.json', 'r') as file:
            stat_info = json.load(file)
        if len(stat_info) > 0:
            stat = []
            for date, categories_info in stat_info.items():
                stat.append(f"{date}:")
                for category, count in categories_info.items():
                    stat.append(f"{category} - {count} раз(а) \n")
                stat.append("")
    else:
        stat = ['Информация отсутствует.']
    return f"Статистика:\n{''.join(stat)}"

# создаем основное меню, при нажтии на название магазина заменяем 'Запустить бота!' на 'Меню!' (условие в обработчике)
def main_keyboard(menu='bot'):
    keyboard = VkKeyboard(inline=False)

    keyboard.add_callback_button(label='Таблица со всеми промокодами!', color=VkKeyboardColor.POSITIVE,
                                 payload={"type": "open_link", "link": "https://docs.google.com/spreadsheets/d/1FhYGE5IODqbtXSfQGBs0BGUaUJYAWBGAC2SRWqYzf6M"})
    keyboard.add_line()
    if menu == 'bot':
        keyboard.add_button(label='Запустить бота!', color=VkKeyboardColor.NEGATIVE, payload={"type": "меню"})
        keyboard.add_line()
    elif menu == 'menu':
        keyboard.add_button(label='Меню!', color=VkKeyboardColor.NEGATIVE, payload={"type": "меню"})
        keyboard.add_line()
    keyboard.add_callback_button(label='Мы в Телеграме!', color=VkKeyboardColor.PRIMARY,
                                 payload={"type": "open_link", "link": "https://t.me/skidkinezagorami"})
    return keyboard.get_keyboard()

# создаем слайдер клавиатуру для категорий и магазинов. (кнопки отображаем по индексам, которые в параметрах), для "вперед", "назад" условия в обработчике
def slider_keyboard(category_name=None, start=0, end=5):
    keyboard = VkKeyboard(inline=True)
    if category_name is None:
        category_names = list(categories.keys())
        for category_name in category_names[start:end]:
            keyboard.add_callback_button(label=category_name, color=VkKeyboardColor.SECONDARY,
                                         payload={"type": "text", "category": category_name})
            keyboard.add_line()
        if start != 0:
            keyboard.add_callback_button(label='назад', color=VkKeyboardColor.PRIMARY, payload={"type": "back"})
        if end <= len(category_names):
            keyboard.add_callback_button(label='вперед', color=VkKeyboardColor.PRIMARY, payload={"type": "forward"})
    else:
        shops = categories.get(category_name, [])
        if end > len(shops):
            end = len(shops)
        for shop in shops[start:end]:
            keyboard.add_button(label=shop, color=VkKeyboardColor.SECONDARY, payload={"type": "text", "name": shop})
            keyboard.add_line()
        if start != 0:
            keyboard.add_callback_button(label='назад', color=VkKeyboardColor.PRIMARY, payload={"type": "back2",
                                                                                            'category': category_name})
        if end + 1 <= len(shops):
            keyboard.add_callback_button(label='вперед', color=VkKeyboardColor.PRIMARY, payload={"type": "forward2",
                                                                                                 'category': category_name})
        else:
            keyboard.add_callback_button(label='меню', color=VkKeyboardColor.PRIMARY, payload={"type": "меню",
                                                                                                 'category': category_name})
    return keyboard.get_keyboard()

# отображаем данные по конкретному магазину
def get_info(name):
    info = []
    for i in companies_info[name]:
        text = ""
        if i != None:
            text = f"Название: {name}"
        if i[1] != None:
            text += f"\nСкидка: {i[1]}"
        if i[5] != None:
            text += f"\nОписание: {i[5]}"
        if i[3] != None:
            text += f"\nДействует до: {i[3]}"
        if i[4] != None:
            text += f"\nРегион: {i[4]}"
        if i[2] != None:
            text += f"\nСсылка: \n{i[2]}"
        if i[0] != None and i[0] != "":
            text += "\nПромокод ниже👇" + f'\n {i[0]}'
        else:
            text += "\nДействует только по ссылке"
        info.append(text)
    return '\n\n'.join(info) + '\n\nНажмите Меню, для вызова главного меню.'

print("Ready")

for event in longpoll.listen():

    if event.type == VkBotEventType.MESSAGE_NEW:

        if event.obj.message['text'] != '':

            if event.from_user:

                if event.obj.message['text'] == 'Запустить бота!' or event.obj.message['text'] == "Меню!":
                    start = 0
                    end = 5
                    if event.obj.message['text'] == 'Запустить бота!':
                        current_date = datetime.now().date()
                        formatted_date = current_date.strftime("%d.%m.%Y")
                        if formatted_date not in bot_starts.keys():
                            if formatted_date not in use_of_categories:
                                use_of_categories[formatted_date] = {}
                                save_stats()
                                bot_starts = {}
                                use_of_categories = {}
                                bot_starts[formatted_date] = 1
                        else:
                            bot_starts[formatted_date] += 1
                    vk.messages.send(
                        user_id=event.obj.message['from_id'],
                        random_id=get_random_id(),
                        peer_id=event.obj.message['from_id'],
                        keyboard=slider_keyboard(start=start, end=end),
                        message='Выбирайте категорию')

                elif event.obj.message['text'].lower() == 'инструкция':
                    vk.messages.send(
                        user_id=event.obj.message['from_id'],
                        random_id=get_random_id(),
                        peer_id=event.obj.message['from_id'],
                        keyboard=main_keyboard(),
                        message=text_inst)

                elif event.obj.message['text'].lower() == 'запуск бота':
                    vk.messages.send(
                        user_id=event.obj.message['from_id'],
                        random_id=get_random_id(),
                        peer_id=event.obj.message['from_id'],
                        keyboard=main_keyboard(),
                        message=show_stats('bot_starts'))

                elif event.obj.message['text'].lower() == 'статистика категорий':
                    vk.messages.send(
                        user_id=event.obj.message['from_id'],
                        random_id=get_random_id(),
                        peer_id=event.obj.message['from_id'],
                        keyboard=main_keyboard(),
                        message=show_stats('use_of_categories'))

                elif event.obj.message['text'].lower() in HI:
                    if event.obj.message['from_id'] not in users:
                        users.append(event.obj.message['from_id'])
                    vk.messages.send(
                        user_id=event.obj.message['from_id'],
                        random_id=get_random_id(),
                        peer_id=event.obj.message['from_id'],
                        keyboard=main_keyboard(),
                        message=text_inst)

                elif event.obj.message['text'] in companies_info.keys():
                    shop_name = event.obj.message['text']
                    vk.messages.send(
                        user_id=event.obj.message['from_id'],
                        random_id=get_random_id(),
                        peer_id=event.obj.message['from_id'],
                        keyboard=main_keyboard(menu='menu'),
                        message=get_info(shop_name))


    elif event.type == VkBotEventType.MESSAGE_EVENT:
        payload_type = event.object.payload.get('type')
        if payload_type == 'text' and event.object.payload.get('category'):
            category_name = event.object.payload.get('category')
            if formatted_date not in use_of_categories:
                use_of_categories[formatted_date] = {}
            if category_name not in use_of_categories[formatted_date]:
                use_of_categories[formatted_date][category_name] = 1
            else:
                use_of_categories[formatted_date][category_name] += 1
            vk.messages.send(
                user_id=event.object['user_id'],
                random_id=get_random_id(),
                peer_id=event.object['peer_id'],
                keyboard=slider_keyboard(category_name, start=0, end=5),
                message='Выберите магазин')

        elif payload_type == 'shops':
            shop = event.object.payload.get('name')
            vk.messages.send(
                user_id=event.object['user_id'],
                random_id=get_random_id(),
                peer_id=event.object['peer_id'],
                keyboard=slider_keyboard(shop, start=0, end=5),
                message='Выберите магазин')

        if payload_type == 'back' or payload_type == 'forward':
            category_name = None
            if payload_type == 'back':
                start -= 5
                if start < 0:
                    start = 0
            elif payload_type == 'forward':
                start += 5
            vk.messages.edit(
                peer_id=event.object['peer_id'],
                message="Выбирайте категорию",
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=slider_keyboard(category_name, start=start, end=start + 5))

        elif payload_type == 'back2' or payload_type == 'forward2':
            category_name = event.object.payload.get('category')
            if payload_type == 'back2':
                start -= 5
                if start < 0:
                    start = 0
            elif payload_type == 'forward2':
                start += 5
            vk.messages.edit(
                peer_id=event.object['peer_id'],
                message="Выбирайте категорию",
                conversation_message_id=event.obj.conversation_message_id,
                keyboard=slider_keyboard(category_name, start=start, end=start + 5))

        elif payload_type == 'меню':
            start = 0
            end = 5
            vk.messages.send(
                user_id=event.object['user_id'],
                random_id=get_random_id(),
                peer_id=event.object['peer_id'],
                message="Выбирайте категорию",
                keyboard=slider_keyboard(start=start, end=end))
