from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Button, Group, Select, Start, Url, Cancel
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs.payment_dialog import getters

from states.state_groups import PaymentSG


payment_dialog = Dialog(
    Window(
        Const('Выберите тариф, который Вы хотели бы приобрести:'),
        Column(
            Button(Const('🖼️ Реставрации'), id='restore_rate_choose', on_click=getters.choose_rate_type),
            Button(Const('🎬 Оживления'), id='revive_rate_choose', on_click=getters.choose_rate_type),
        ),
        Cancel(Const('⬅️Назад'), id='close_dialog'),
        state=PaymentSG.choose_rate_type
    ),
    Window(
        Format('Выберите количество {rate}, которое вы хотели бы приобрести'),
        Group(
            Select(
                Format('{item[0]}'),
                id='rate_choose_builder',
                item_id_getter=lambda x: x[1],
                items='items',
                on_click=getters.rate_selector
            ),
            width=1
        ),
        SwitchTo(Const('⬅️Назад'), id='back_choose_rate_type', state=PaymentSG.choose_rate_type),
        getter=getters.choose_rate_getter,
        state=PaymentSG.choose_rate
    ),
    Window(
        Const('🏦<b>Выберите способ оплаты</b>\n'),
        Format('{text}'),
        Column(
            Button(Const('💳Карта, СБП, SberPay'), id='card_payment_choose', on_click=getters.payment_choose),
            Button(Const('💲Крипта'), id='crypto_payment_choose', on_click=getters.payment_choose),
            #Button(Const('⭐️Звезды'), id='stars_payment_choose', on_click=getters.payment_choose),
        ),
        SwitchTo(Const('⬅️Назад'), id='back_choose_rate', state=PaymentSG.choose_rate),
        getter=getters.choose_payment_getter,
        state=PaymentSG.choose_payment
    ),
    Window(
        Const('<b>⌛️Ожидание оплаты</b>'),
        Format('{text}'),
        Column(
            Url(Const('🔗Оплатить'), id='url', url=Format('{url}')),
        ),
        Button(Const('⬅️Назад'), id='back_choose_payment', on_click=getters.close_payment),
        getter=getters.process_payment_getter,
        state=PaymentSG.process_payment
    ),
)
