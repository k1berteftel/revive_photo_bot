from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.user_dialog import getters

from states.state_groups import startSG, adminSG, PaymentSG

user_dialog = Dialog(
    Window(
        Format('<b>Добро пожаловать, {full_name}</b>\n\nЯ помогаю восстанавливать и оживлять Ваши памятные снимки ✨'
               '\n\nЧто я умею?\n<b>🖼Реставрация</b>: Уберу царапины, пятна, восстановлю резкость и детали на Вашем фото.'
               '\n<b>🎬Оживление</b>: Создам короткое видео из Вашего фото, где персонажи слегка улыбаются, двигают '
               'головой, целуются или выполняют какие-то действия по вашему запросу.'
               '\n\n👇 Используйте кнопки ниже для навигации.'),
        Row(
            SwitchTo(Const('🖼️ Реставрация'), id='get_restore_photo_switcher', state=startSG.get_restore_photo),
            SwitchTo(Const('🎬Оживить фото'), id='get_revive_photo_switcher', state=startSG.get_revive_photo),
        ),
        Column(
            SwitchTo(Const('📋Инструкция'), id='manual_switcher', state=startSG.manual),
            SwitchTo(Const('🎁Бесплатные генерации'), id='ref_menu_switcher', state=startSG.ref_menu),
            Start(Const('💰Пополнить баланс'), id='payment_dialog_start', state=PaymentSG.choose_rate_type),
            SwitchTo(Const('👤Профиль'), id='profile_switcher', state=startSG.profile),
            Url(Const('🛠Тех поддержка'), id='support_url', url=Const('https://t.me/svetlanka_support')),
            Start(Const('Админ панель'), id='admin', state=adminSG.start, when='admin')
        ),
        getter=getters.start_getter,
        state=startSG.start
    ),
    Window(
        Const('🖼 Пришлите фотографию и я восстановлю её для Вас 🪄'),
        MessageInput(
            func=getters.get_restore_photo,
            content_types=ContentType.PHOTO
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        state=startSG.get_restore_photo
    ),
    Window(
        DynamicMedia('media'),
        Const('✅Ваша реставрация фото готова'),
        Group(
            SwitchTo(Const('🖼️ Реставрация'), id='get_restore_photo_switcher', state=startSG.get_restore_photo, show_mode=ShowMode.SEND),
            SwitchTo(Const('🎬Оживить фото'), id='get_revive_photo_switcher', state=startSG.get_revive_photo, show_mode=ShowMode.SEND),
            SwitchTo(Const('🏠️Главное меню'), id='back', state=startSG.start, show_mode=ShowMode.SEND),
            width=2
        ),
        getter=getters.restore_result_getter,
        state=startSG.restore_result
    ),
    Window(
        Const('🎬Пришлите фотографию и я оживлю её для Вас ✨'),
        MessageInput(
            func=getters.get_revive_image,
            content_types=ContentType.PHOTO
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        state=startSG.get_revive_photo
    ),
    Window(
        Const('Выберите действие для оживления фото:'),
        Group(
            Button(Const('🤗Объятие'), id='hug_action_choose', on_click=getters.revive_action_choose),
            Button(Const('💋Поцелуй'), id='kiss_action_choose', on_click=getters.revive_action_choose),
            Button(Const('👋Приветствие'), id='greeting_action_choose', on_click=getters.revive_action_choose),
            Button(Const('💨Воздушный поцелуй'), id='air_action_choose', on_click=getters.revive_action_choose),
            Button(Const('🛠✨Реставрировать и оживить'), id='basic_action_choose', on_click=getters.revive_action_choose),
            width=2
        ),
        SwitchTo(Const('📝Прописать свое действие на фото'), id='get_revive_prompt_switcher', state=startSG.get_revive_prompt),
        SwitchTo(Const('⬅️Назад'), id='back_get_revive_photo', state=startSG.get_revive_photo),
        state=startSG.revive_action_menu
    ),
    Window(
        Const('📝Напишите, что должны сделать люди.\nПример: <em>Оживи так, чтобы люди на фото…</em>'),
        TextInput(
            id='get_revive_prompt',
            on_success=getters.get_revive_prompt
        ),
        SwitchTo(Const('⬅️Назад'), id='back_revive_action_menu', state=startSG.revive_action_menu),
        state=startSG.get_revive_prompt
    ),
    Window(
        DynamicMedia('media'),
        Const('✅Ваше оживление фото готово'),
        Group(
            SwitchTo(Const('🖼️ Реставрация'), id='get_restore_photo_switcher', state=startSG.get_restore_photo, show_mode=ShowMode.SEND),
            SwitchTo(Const('🎬Оживить фото'), id='get_revive_photo_switcher', state=startSG.get_revive_photo, show_mode=ShowMode.SEND),
            SwitchTo(Const('🏠️Главное меню'), id='back', state=startSG.start, show_mode=ShowMode.SEND),
            width=2
        ),
        getter=getters.revive_result_getter,
        state=startSG.revive_result
    ),
    Window(
        Format('{text}'),
        Column(
            Start(Const('💰Пополнить баланс'), id='payment_dialog_start', state=PaymentSG.choose_rate_type),
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        getter=getters.profile_getter,
        state=startSG.profile
    ),
    Window(
        Format('{text}'),
        Column(
            Url(Const('📤Пригласить друга'), id='ref_menu_link', url=Format('{ref_link}'))
        ),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        getter=getters.ref_menu_getters,
        state=startSG.ref_menu
    ),
    Window(
        Format('❌ Недостаточно средств:\n<blockquote> {balance} </blockquote>\n\n<b>Как продолжить?</b>\n'
               '🎁 <b>Получить бонусные средства</b> — пригласите друга по реферальной программе.\n'
               '💳 <b>Пополнить баланс</b> — мгновенное пополнение картой.'),
        Column(
            SwitchTo(Const('🎁Реферальная программа'), id='ref_menu_switcher', state=startSG.ref_menu),
            Start(Const('💳Пополнить баланс'), id='payment_dialog_start', state=PaymentSG.choose_rate_type),
        ),
        SwitchTo(Const('🏠️Главное меню'), id='back', state=startSG.start),
        getter=getters.enough_balance_getter,
        state=startSG.enough_balance
    ),
    Window(
        Format('{text}'),
        SwitchTo(Const('⬅️Назад'), id='back', state=startSG.start),
        getter=getters.manual_getter,
        state=startSG.manual
    ),
)