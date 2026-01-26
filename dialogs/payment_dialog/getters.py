import asyncio

from aiogram.types import CallbackQuery, User, Message, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.text_utils import get_rate_form
from utils.payments.create_payment import get_yookassa_url, get_oxa_payment_data, _get_usdt_rub
from utils.payments.process_payment import wait_for_payment
from database.action_data_class import DataInteraction
from config_data.config import load_config, Config
from states.state_groups import startSG, PaymentSG


async def choose_rate_type(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    rate = clb.data.split('_')[0]
    dialog_manager.dialog_data['rate'] = rate
    await dialog_manager.switch_to(PaymentSG.choose_rate)


async def choose_rate_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    rate_type = dialog_manager.dialog_data.get('rate')
    rates = await session.get_rates()
    buttons = [(f'{rate.amount} - {rate.cost}₽ {rate.text if rate.text else ""}', rate.id) for rate in rates if rate.rate == rate_type]
    return {
        'rate': 'реставраций' if rate_type == 'restore' else 'оживлений',
        'items': buttons
    }


async def rate_selector(clb: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    rate = await session.get_rate(int(item_id))
    dialog_manager.dialog_data['cost'] = rate.cost
    dialog_manager.dialog_data['amount'] = rate.amount
    await dialog_manager.switch_to(PaymentSG.choose_payment)


async def choose_payment_getter(dialog_manager: DialogManager, **kwargs):
    amount = dialog_manager.dialog_data.get('amount')
    cost = dialog_manager.dialog_data.get('cost')
    rate_type = dialog_manager.dialog_data.get('rate')

    usdt = dialog_manager.dialog_data.get('usdt')
    if not usdt:
        usdt_rub = await _get_usdt_rub()
        usdt = round(cost / (usdt_rub), 2)
        dialog_manager.dialog_data['usdt'] = usdt

    text = (f'<em>Сумма к оплате: <b>{cost}₽ ({usdt}$)</b>\n'
            f'Покупка: <b>{amount}</b> {get_rate_form(amount, rate_type)}</em>')
    return {'text': text}


async def payment_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    if dialog_manager.start_data:
        dialog_manager.dialog_data.update(dialog_manager.start_data)
        dialog_manager.start_data.clear()
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    cost = dialog_manager.dialog_data.get('cost')
    amount = dialog_manager.dialog_data.get('amount')
    rate_type = dialog_manager.dialog_data.get('rate')
    payment = clb.data.split('_')[0]

    if payment == 'card':
        payment = await get_yookassa_url(cost, f'Покупка {amount} {"Реставраций" if rate_type == "restore" else "Оживлений"}, ID: {clb.from_user.id}')
        task = asyncio.create_task(
            wait_for_payment(
                payment_id=payment.get('id'),
                user_id=clb.from_user.id,
                bot=clb.bot,
                session=session,
                amount=amount,
                cost=cost,
                rate_type=rate_type,
                payment_type='card',
            )
        )
        for active_task in asyncio.all_tasks():
            if active_task.get_name() == f'process_payment_{clb.from_user.id}':
                active_task.cancel()
        task.set_name(f'process_payment_{clb.from_user.id}')
        dialog_manager.dialog_data['url'] = payment.get('url')
        await dialog_manager.switch_to(PaymentSG.process_payment)
        return
    elif payment == 'crypto':
        payment = await get_oxa_payment_data(cost)
        task = asyncio.create_task(
            wait_for_payment(
                payment_id=payment.get('id'),
                user_id=clb.from_user.id,
                bot=clb.bot,
                session=session,
                amount=amount,
                cost=cost,
                rate_type=rate_type,
                payment_type='crypto',
            )
        )
        for active_task in asyncio.all_tasks():
            if active_task.get_name() == f'process_payment_{clb.from_user.id}':
                active_task.cancel()
        task.set_name(f'process_payment_{clb.from_user.id}')
        task.set_name(f'process_payment_{clb.from_user.id}')
        dialog_manager.dialog_data['url'] = payment.get('url')
        await dialog_manager.switch_to(PaymentSG.process_payment)
        return
    else:
        state: FSMContext = dialog_manager.middleware_data.get('state')
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Оплатить', pay=True)],
                [InlineKeyboardButton(text='Закрыть', callback_data='close_payment')]
            ]
        )
        await state.update_data(dialog_manager.dialog_data)
        price = int(round(cost * 0.96, 0))
        prices = [LabeledPrice(label="XTR", amount=price)]
        await clb.message.answer_invoice(
            title='Пополнение баланса',
            description=f'Пополнение {cost}₽ ID: {clb.from_user.id}',
            payload=str(cost),
            currency="XTR",
            prices=prices,
            provider_token="",
            reply_markup=keyboard
        )


async def process_payment_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    amount = dialog_manager.dialog_data.get('amount')
    cost = dialog_manager.dialog_data.get('cost')
    usdt = dialog_manager.dialog_data.get('usdt')
    url = dialog_manager.dialog_data.get('url')
    text = f'<blockquote> - Сумма к оплате: {cost}₽ ({usdt})</blockquote>'
    return {
        'text': text,
        'url': url
    }


async def close_payment(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    name = f'process_payment_{clb.from_user.id}'
    for task in asyncio.all_tasks():
        if task.get_name() == name:
            task.cancel()
    await dialog_manager.switch_to(PaymentSG.choose_payment)