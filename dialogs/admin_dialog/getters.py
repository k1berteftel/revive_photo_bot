import os
import datetime

from aiogram import Bot
from aiogram.types import CallbackQuery, User, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.build_ids import get_random_id
from utils.schedulers import send_messages
from database.action_data_class import DataInteraction
from config_data.config import load_config, Config
from states.state_groups import startSG, adminSG


async def get_static(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    users = await session.get_users()
    active = 0
    entry = {
        'today': 0,
        'yesterday': 0,
        '2_day_ago': 0
    }
    activity = 0
    for user in users:
        if user.active:
            active += 1
        for day in range(0, 3):
            #print(user.entry.date(), (datetime.datetime.today() - datetime.timedelta(days=day)).date())
            if user.entry.date() == (datetime.datetime.today() - datetime.timedelta(days=day)).date():
                if day == 0:
                    entry['today'] = entry.get('today') + 1
                elif day == 1:
                    entry['yesterday'] = entry.get('yesterday') + 1
                else:
                    entry['2_day_ago'] = entry.get('2_day_ago') + 1
        if user.activity.timestamp() > (datetime.datetime.today() - datetime.timedelta(days=1)).timestamp():
            activity += 1

    static = await session.get_static()

    text = (f'<b>Статистика на {datetime.datetime.today().strftime("%d-%m-%Y")}</b>\n\nВсего пользователей: {len(users)}'
            f'\n - Активные пользователи(не заблокировали бота): {active}\n - Пользователей заблокировали '
            f'бота: {len(users) - active}\n - Провзаимодействовали с ботом за последние 24 часа: {activity}\n\n'
            f'<b>Прирост аудитории:</b>\n - За сегодня: +{entry.get("today")}\n - Вчера: +{entry.get("yesterday")}'
            f'\n - Позавчера: + {entry.get("2_day_ago")}\n\n<b>Доход</b>:\n - За сегодня: {static.today}₽'
            f'\n - За неделю: {static.week}₽\n - За месяц: {static.month}₽\n - За все время: {static.total}₽')
    await clb.message.answer(text=text)


async def get_users_txt(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    users = await session.get_users()
    with open('users.txt', 'a+') as file:
        for user in users:
            file.write(f'{user.user_id}\n')
    await clb.message.answer_document(
        document=FSInputFile(path='users.txt')
    )
    try:
        os.remove('users.txt')
    except Exception:
        ...


async def get_user_data(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    try:
        user_id = int(text)
        user = await session.get_user(user_id)
    except Exception:
        if not text.startswith('@'):
            await msg.answer('Юзернейм должен начинаться с @ , пожалуйста попробуйте снова')
            return
        user = await session.get_user_by_username(text[1::])
    if not user:
        await msg.answer('Такого пользователя в боте не найдено, пожалуйста попробуйте еще раз')
        return
    dialog_manager.dialog_data['user_id'] = user.user_id
    await dialog_manager.switch_to(adminSG.choose_delivery_type)


async def choose_delivery_type(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data['rate'] = clb.data.split('_')[0]
    await dialog_manager.switch_to(adminSG.get_delivery_amount)


async def get_delivery_amount(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        amount = int(text)
    except Exception:
        await msg.answer('Кол-во генераций должно быть числом, пожалуйста попробуйте снова')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user_id = dialog_manager.dialog_data.get('user_id')
    rate = dialog_manager.dialog_data.get('rate')

    await session.increment_user_value(user_id, rate, amount)
    await msg.answer('Генерации были успешно начислены данному пользователю')

    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.start)


async def deeplinks_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    buttons = dialog_manager.dialog_data.get('deeplinks')
    if not buttons:
        links = await session.get_deeplinks()
        buttons = [(f'{link.name} ({link.entry})', link.id) for link in links]
        buttons = [buttons[i:i + 10] for i in range(0, len(buttons), 10)]
        dialog_manager.dialog_data['deeplinks'] = buttons
    page = dialog_manager.dialog_data.get('page')
    if not page:
        page = 0
        dialog_manager.dialog_data['page'] = page
    not_first = False
    not_last = False
    if page != 0:
        not_first = True
    if len(buttons) and page != len(buttons) - 1:
        not_last = True
    print(buttons)
    return {
        'items': buttons[page] if buttons else [],
        'page': f'{page + 1}/{len(buttons)}',
        'not_first': not_first,
        'not_last': not_last
    }


async def deeplinks_pager(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    page = dialog_manager.dialog_data.get('page')
    action = clb.data.split('_')[0]
    if action == 'back':
        page -= 1
    else:
        page += 1
    dialog_manager.dialog_data['page'] = page
    await dialog_manager.switch_to(adminSG.deeplinks_menu)


async def get_deeplink_name(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.add_deeplink(get_random_id(), text)
    links = await session.get_deeplinks()
    buttons = [(f'{link.name} ({link.entry})', link.id) for link in links]
    buttons = [buttons[i:i + 10] for i in range(0, len(buttons), 10)]
    print(buttons)
    dialog_manager.dialog_data['deeplinks'] = buttons
    await dialog_manager.switch_to(adminSG.deeplinks_menu)


async def deeplink_choose(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['deeplink_id'] = int(item_id)
    await dialog_manager.switch_to(adminSG.deeplink_menu)


async def deeplink_menu_getter(dialog_manager: DialogManager, **kwargs):
    deeplink_id = dialog_manager.dialog_data.get('deeplink_id')
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    deeplink = await session.get_deeplink(deeplink_id)
    users = [user for user in await session.get_users() if user.join and user.join == deeplink.link]
    active = 0
    entry = {
        'today': 0,
        'yesterday': 0,
        '2_day_ago': 0
    }
    activity = 0
    for user in users:
        if user.active:
            active += 1
        for day in range(0, 3):
            #print(user.entry.date(), (datetime.datetime.today() - datetime.timedelta(days=day)).date())
            if user.entry.date() == (datetime.datetime.now() - datetime.timedelta(days=day)).date():
                if day == 0:
                    entry['today'] = entry.get('today') + 1
                elif day == 1:
                    entry['yesterday'] = entry.get('yesterday') + 1
                else:
                    entry['2_day_ago'] = entry.get('2_day_ago') + 1
        if user.activity.timestamp() > (datetime.datetime.today() - datetime.timedelta(days=1)).timestamp():
            activity += 1

    text = (f'<b>({deeplink.name}) 🗓 Cоздано: {datetime.datetime.today().strftime("%d-%m-%Y")}</b>\n\nОбщее:\nВсего: {len(users)}'
            f'\n - Активны: {active}\n - Заблокировали бота: {len(users) - active}\n'
            f' - Заходили в бота последние сутки: {activity}\n\nРост:\n - За сегодня: +{entry.get("today")}\n'
            f' - Вчера: +{entry.get("yesterday")}\n - Позавчера: + {entry.get("2_day_ago")}\n\nЗаработано:\n'
            f' - Всего: {deeplink.earned}₽\n - За сегодня: {deeplink.today}₽\n - За неделю: {deeplink.week}₽\n\n'
            f'<b>🔗 Ссылка:</b> <code>https://t.me/Fotovmagic_bot?start={deeplink.link}</code>')
    return {'text': text}


async def del_deeplink(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    deeplink_id = dialog_manager.dialog_data.get('deeplink_id')
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_deeplink(deeplink_id)

    await clb.answer('Данный диплинк был успешно удален')

    links = await session.get_deeplinks()
    buttons = [(f'{link.name} ({link.entry})', link.id) for link in links]
    buttons = [buttons[i:i + 10] for i in range(0, len(buttons), 10)]
    dialog_manager.dialog_data['deeplinks'] = buttons
    dialog_manager.dialog_data['page'] = 0
    dialog_manager.dialog_data['deeplink_id'] = None
    await dialog_manager.switch_to(adminSG.deeplinks_menu)


async def rate_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    rates = await session.get_rates()
    text = ''
    counter = 1
    for rate in rates:
        text += f'(<em>{"Реставрация" if rate.rate == "restore" else "Оживление"}</em>)|({counter}) - {rate.amount} за {rate.cost}₽\n'
        counter += 1
    return {'rate': text if text else 'Отсутствуют'}


async def rate_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    rate = clb.data.split('_')[0]
    dialog_manager.dialog_data['rate'] = rate
    await dialog_manager.switch_to(adminSG.get_rate_amount)


async def get_rate_amount(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        amount = int(text)
    except Exception:
        await msg.answer('Кол-во генераций должно быть числом, пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['amount'] = amount
    await dialog_manager.switch_to(adminSG.get_rate_cost)


async def get_rate_cost(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        cost = int(text)
    except Exception:
        await msg.answer('Кол-во генераций должно быть числом, пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['cost'] = cost
    await dialog_manager.switch_to(adminSG.get_rate_text)


async def get_rate_text(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    if len(text) > 15:
        await msg.answer('В дополнительном тексте должно быть не более 10 символов, пожалуйста попробуйте снова')
        return
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    rate = dialog_manager.dialog_data.get('rate')
    amount = dialog_manager.dialog_data.get('amount')
    cost = dialog_manager.dialog_data.get('cost')
    await session.add_rate(amount, int(cost), text, rate)
    await msg.answer('Новый тариф был успешно добавлен')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.rate_menu)


async def save_rate(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    rate = dialog_manager.dialog_data.get('rate')
    amount = dialog_manager.dialog_data.get('amount')
    cost = dialog_manager.dialog_data.get('cost')
    await session.add_rate(amount, int(cost), None, rate)
    await clb.message.answer('Новый тариф был успешно добавлен')
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.rate_menu)


async def del_rate_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    rates = await session.get_rates()
    buttons = []
    counter = 1
    for rate in rates:
        buttons.append((f'({counter})-{rate.amount}|{rate.cost}₽', rate.id))
        counter += 1
    return {
        'items': buttons
    }


async def del_rate(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: int):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_rate(int(item_id))
    await clb.answer('Данный тариф был успешно удален')
    await dialog_manager.switch_to(adminSG.del_rate)


async def del_admin(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    await session.del_admin(int(item_id))
    await clb.answer('Админ был успешно удален')
    await dialog_manager.switch_to(adminSG.admin_menu)


async def admin_del_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    admins = await session.get_admins()
    buttons = []
    for admin in admins:
        buttons.append((admin.name, admin.user_id))
    return {'items': buttons}


async def refresh_url(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    id: str = dialog_manager.dialog_data.get('link_id')
    dialog_manager.dialog_data.clear()
    await session.del_link(id)
    await dialog_manager.switch_to(adminSG.admin_add)


async def admin_add_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    id = get_random_id()
    dialog_manager.dialog_data['link_id'] = id
    await session.add_link(id)
    return {'id': id}


async def admin_menu_getter(dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    admins = await session.get_admins()
    text = ''
    for admin in admins:
        text += f'{admin.name}\n'
    return {'admins': text}


async def get_mail(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    if msg.text:
        dialog_manager.dialog_data['text'] = msg.text
    elif msg.photo:
        dialog_manager.dialog_data['photo'] = msg.photo[0].file_id
        dialog_manager.dialog_data['caption'] = msg.caption
    elif msg.video:
        dialog_manager.dialog_data['video'] = msg.video.file_id
        dialog_manager.dialog_data['caption'] = msg.caption
    else:
        await msg.answer('Что-то пошло не так, пожалуйста попробуйте снова')
    await dialog_manager.switch_to(adminSG.get_time)


async def get_time(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        time = datetime.datetime.strptime(text, '%H:%M %d.%m')
    except Exception as err:
        print(err)
        await msg.answer('Вы ввели данные не в том формате, пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['time'] = text
    await dialog_manager.switch_to(adminSG.get_keyboard)


async def get_mail_keyboard(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        buttons = text.split('\n')
        keyboard: list[tuple] = [(i.split('-')[0].strip(), i.split('-')[1].strip()) for i in buttons]
    except Exception as err:
        print(err)
        await msg.answer('Вы ввели данные не в том формате, пожалуйста попробуйте снова')
        return
    dialog_manager.dialog_data['keyboard'] = keyboard
    await dialog_manager.switch_to(adminSG.confirm_mail)


async def cancel_malling(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.start)


async def start_malling(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    bot: Bot = dialog_manager.middleware_data.get('bot')
    scheduler: AsyncIOScheduler = dialog_manager.middleware_data.get('scheduler')
    time = dialog_manager.dialog_data.get('time')
    keyboard = dialog_manager.dialog_data.get('keyboard')
    if keyboard:
        keyboard = [InlineKeyboardButton(text=i[0], url=i[1]) for i in keyboard]
    users = await session.get_users()
    if not time:
        if dialog_manager.dialog_data.get('text'):
            text: str = dialog_manager.dialog_data.get('text')
            for user in users:
                try:
                    await bot.send_message(
                        chat_id=user.user_id,
                        text=text.format(name=user.name),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None
                    )
                    if user.active == 0:
                        await session.set_active(user.user_id, 1)
                except Exception as err:
                    print(err)
                    await session.set_active(user.user_id, 0)
        elif dialog_manager.dialog_data.get('caption'):
            caption: str = dialog_manager.dialog_data.get('caption')
            if dialog_manager.dialog_data.get('photo'):
                for user in users:
                    try:
                        await bot.send_photo(
                            chat_id=user.user_id,
                            photo=dialog_manager.dialog_data.get('photo'),
                            caption=caption.format(name=user.name),
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None
                        )
                        if user.active == 0:
                            await session.set_active(user.user_id, 1)
                    except Exception as err:
                        print(err)
                        await session.set_active(user.user_id, 0)
            else:
                for user in users:
                    try:
                        await bot.send_video(
                            chat_id=user.user_id,
                            video=dialog_manager.dialog_data.get('video'),
                            caption=caption.format(name=user.name),
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None
                        )
                        if user.active == 0:
                            await session.set_active(user.user_id, 1)
                    except Exception as err:
                        print(err)
                        await session.set_active(user.user_id, 0)
    else:
        date = datetime.datetime.strptime(time, '%H:%M %d.%m')
        date = date.replace(year=datetime.datetime.today().year)
        scheduler.add_job(
            func=send_messages,
            args=[bot, session, InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None],
            kwargs={
                'text': dialog_manager.dialog_data.get('text'),
                'caption': dialog_manager.dialog_data.get('caption'),
                'photo': dialog_manager.dialog_data.get('photo'),
                'video': dialog_manager.dialog_data.get('video')
            },
            next_run_time=date
        )
    dialog_manager.dialog_data.clear()
    await dialog_manager.switch_to(adminSG.start)

