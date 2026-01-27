from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url, Cancel
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.admin_dialog import getters
from states.state_groups import adminSG


admin_dialog = Dialog(
    Window(
        Const('Админ панель'),
        Column(
            Button(Const('📊 Получить статистику'), id='get_static', on_click=getters.get_static),
            SwitchTo(Const('🛫Сделать рассылку'), id='mailing_menu_switcher', state=adminSG.get_mail),
            SwitchTo(Const('Выдать генерации'), id='get_user_delivery_switcher', state=adminSG.get_user_delivery),
            SwitchTo(Const('Управление тарифами'), id='rate_menu_switcher', state=adminSG.rate_menu),
            SwitchTo(Const('🔗 Управление диплинками'), id='deeplinks_menu_switcher', state=adminSG.deeplinks_menu),
            SwitchTo(Const('👥 Управление админами'), id='admin_menu_switcher', state=adminSG.admin_menu),
            Button(Const('📋Выгрузка базы пользователей'), id='get_users_txt', on_click=getters.get_users_txt),
        ),
        Cancel(Const('Назад'), id='close_admin'),
        state=adminSG.start
    ),
    Window(
        Const('Введите @username или Telegram ID пользователя, которому вы хотели бы выдать генерации'),
        TextInput(
            id='get_user_data',
            on_success=getters.get_user_data
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        state=adminSG.get_user_delivery
    ),
    Window(
        Const('Выберите генерацию, которую вы хотели бы начислить пользователю:'),
        Column(
            Button(Const('Реставрации'), id='restores_delivery_choose', on_click=getters.choose_delivery_type),
            Button(Const('Оживления'), id='revives_delivery_choose', on_click=getters.choose_delivery_type),
        ),
        SwitchTo(Const('🔙 Назад'), id='back_get_user_delivery', state=adminSG.get_user_delivery),
        state=adminSG.choose_delivery_type
    ),
    Window(
        Const('Введите количество генераций, которое вы хотели бы выдать пользователю'),
        TextInput(
            id='get_delivery_amount',
            on_success=getters.get_delivery_amount
        ),
        SwitchTo(Const('🔙 Назад'), id='back_choose_delivery_type', state=adminSG.choose_delivery_type),
        state=adminSG.get_delivery_amount
    ),
    Window(
        Const('<b>Созданные тарифы: </b>'),
        Format('{rate}'),
        Column(
            SwitchTo(Const('Добавить тариф'), id='get_rate_amount_switcher', state=adminSG.choose_rate_type),
            SwitchTo(Const('Удалить тариф'), id='del_rate_switcher', state=adminSG.del_rate),
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.rate_menu_getter,
        state=adminSG.rate_menu
    ),
    Window(
        Const('Выберите категорию для нового тарифа'),
        Column(
            Button(Const('Реставрация'), id='restore_rate_choose', on_click=getters.rate_choose),
            Button(Const('Оживление'), id='revive_rate_choose', on_click=getters.rate_choose),
        ),
        SwitchTo(Const('🔙 Назад'), id='back_rate_menu', state=adminSG.rate_menu),
        state=adminSG.choose_rate_type
    ),
    Window(
        Const('Введите кол-во генераций для нового тарифа'),
        TextInput(
            id='get_rate_amount',
            on_success=getters.get_rate_amount
        ),
        SwitchTo(Const('🔙 Назад'), id='back_choose_rate_type', state=adminSG.choose_rate_type),
        state=adminSG.get_rate_amount
    ),
    Window(
        Const('Введите стоимость для нового тарифа'),
        TextInput(
            id='get_rate_cost',
            on_success=getters.get_rate_cost
        ),
        SwitchTo(Const('🔙 Назад'), id='back_get_rate_amount', state=adminSG.get_rate_amount),
        state=adminSG.get_rate_cost
    ),
    Window(
        Const('Введите дополнительный текст, который будет отображаться после тарифа, н-р:\n'
              'Без доп. текста: 2 - 580₽\nС доп. текстом: 5 - 1250₽ (скидка 14%)'),
        TextInput(
            id='get_rate_text',
            on_success=getters.get_rate_text
        ),
        Column(
            Button(Const('Без доп. текста'), id='save_rate_without', on_click=getters.save_rate),
        ),
        SwitchTo(Const('🔙 Назад'), id='back_get_rate_cost', state=adminSG.get_rate_cost),
        state=adminSG.get_rate_text
    ),
    Window(
        Const('Нажмите на тариф, который вы хотели бы удалить'),
        Group(
            Select(
                Format('{item[0]}'),
                id='del_rate_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_rate
            ),
            width=1
        ),
        SwitchTo(Const('🔙 Назад'), id='back_rate_menu', state=adminSG.rate_menu),
        getter=getters.del_rate_getter,
        state=adminSG.del_rate
    ),
    Window(
        Format('🔗 *Меню управления диплинками*'),
        Column(
            Select(
                Format('{item[0]}'),
                id='deeplinks_menu_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.deeplink_choose
            ),
        ),
        Row(
            Button(Const('◀️'), id='back_deeplinks_pager', on_click=getters.deeplinks_pager, when='not_first'),
            Button(Format('{page}'), id='deeplinks_pager', when='deeplinks'),
            Button(Const('▶️'), id='next_deeplinks_pager', on_click=getters.deeplinks_pager, when='not_last')
        ),
        SwitchTo(Const('➕ Добавить диплинк'), id='add_deeplink', state=adminSG.get_deeplink_name),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.deeplinks_menu_getter,
        state=adminSG.deeplinks_menu
    ),
    Window(
        Const('Введите название для данной ссылки'),
        TextInput(
            id='get_link_name',
            on_success=getters.get_deeplink_name
        ),
        SwitchTo(Const('🔙 Назад'), id='back_deeplinks_menu', state=adminSG.deeplink_menu),
        state=adminSG.get_deeplink_name
    ),
    Window(
        Format('{text}'),
        Column(
            Button(Const('🗑Удалить диплинк'), id='del_deeplink', on_click=getters.del_deeplink),
        ),
        SwitchTo(Const('🔙 Назад'), id='back_deeplinks_menu', state=adminSG.deeplinks_menu),
        getter=getters.deeplink_menu_getter,
        state=adminSG.deeplink_menu
    ),
    Window(
        Format('👥 *Меню управления администраторами*\n\n {admins}'),
        Column(
            SwitchTo(Const('➕ Добавить админа'), id='add_admin_switcher', state=adminSG.admin_add),
            SwitchTo(Const('❌ Удалить админа'), id='del_admin_switcher', state=adminSG.admin_del)
        ),
        SwitchTo(Const('🔙 Назад'), id='back', state=adminSG.start),
        getter=getters.admin_menu_getter,
        state=adminSG.admin_menu
    ),
    Window(
        Const('👤 Выберите пользователя, которого хотите сделать админом\n'
              '⚠️ Ссылка одноразовая и предназначена для добавления только одного админа'),
        Column(
            Url(Const('🔗 Добавить админа (ссылка)'), id='add_admin',
                url=Format('http://t.me/share/url?url=https://t.me/Fotovmagic_bot?start={id}')),
            Button(Const('🔄 Создать новую ссылку'), id='new_link_create', on_click=getters.refresh_url),
            SwitchTo(Const('🔙 Назад'), id='back_admin_menu', state=adminSG.admin_menu)
        ),
        getter=getters.admin_add_getter,
        state=adminSG.admin_add
    ),
    Window(
        Const('❌ Выберите админа для удаления'),
        Group(
            Select(
                Format('👤 {item[0]}'),
                id='admin_del_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.del_admin
            ),
            width=1
        ),
        SwitchTo(Const('🔙 Назад'), id='back_admin_menu', state=adminSG.admin_menu),
        getter=getters.admin_del_getter,
        state=adminSG.admin_del
    ),
    Window(
        Const('Введите сообщение которое вы хотели бы разослать\n\n<b>Предлагаемый макросы</b>:'
              '\n{name} - <em>полное имя пользователя</em>'),
        MessageInput(
            content_types=ContentType.ANY,
            func=getters.get_mail
        ),
        SwitchTo(Const('Назад'), id='back', state=adminSG.start),
        state=adminSG.get_mail
    ),
    Window(
        Const('Введите дату и время в которое сообщение должно отправиться всем юзерам в формате '
              'час:минута:день:месяц\n Например: 18:00 10.02 (18:00 10-ое февраля)'),
        TextInput(
            id='get_time',
            on_success=getters.get_time
        ),
        SwitchTo(Const('Продолжить без отложки'), id='get_keyboard_switcher', state=adminSG.get_keyboard),
        SwitchTo(Const('Назад'), id='back_get_mail', state=adminSG.get_mail),
        state=adminSG.get_time
    ),
    Window(
        Const('Введите кнопки которые будут крепиться к рассылаемому сообщению\n'
              'Введите кнопки в формате:\n кнопка1 - ссылка1\nкнопка2 - ссылка2'),
        TextInput(
            id='get_mail_keyboard',
            on_success=getters.get_mail_keyboard
        ),
        SwitchTo(Const('Продолжить без кнопок'), id='confirm_mail_switcher', state=adminSG.confirm_mail),
        SwitchTo(Const('Назад'), id='back_get_time', state=adminSG.get_time),
        state=adminSG.get_keyboard
    ),
    Window(
        Const('Вы подтверждаете рассылку сообщения'),
        Row(
            Button(Const('Да'), id='start_malling', on_click=getters.start_malling),
            Button(Const('Нет'), id='cancel_malling', on_click=getters.cancel_malling),
        ),
        SwitchTo(Const('Назад'), id='back_get_keyboard', state=adminSG.get_keyboard),
        state=adminSG.confirm_mail
    ),
)