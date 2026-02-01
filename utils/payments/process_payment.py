import datetime
import random
from typing import Literal
import asyncio
from asyncio import TimeoutError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from nats.js import JetStreamContext

from utils.text_utils import get_rate_form
from utils.payments.create_payment import check_yookassa_payment, check_oxa_payment
from database.action_data_class import DataInteraction
from config_data.config import Config, load_config


config: Config = load_config()


async def wait_for_payment(
        payment_id,
        user_id: int,
        bot: Bot,
        session: DataInteraction,
        cost: int,
        amount: int,
        rate_type: str,
        payment_type: Literal['card', 'crypto'],
        timeout: int = 60 * 15,
        check_interval: int = 6
):
    """
    Ожидает оплаты в фоне. Завершается при оплате или по таймауту.
    """
    try:
        await asyncio.wait_for(_poll_payment(payment_id, user_id, amount, cost, rate_type, bot, session, payment_type, check_interval),
                                             timeout=timeout)

    except TimeoutError:
        print(f"Платёж {payment_id} истёк (таймаут)")

    except Exception as e:
        print(f"Ошибка в фоновом ожидании платежа {payment_id}: {e}")


async def _poll_payment(payment_id, user_id: int, amount: int, cost: int, rate_type: str, bot: Bot, session: DataInteraction, payment_type: str, interval: int):
    """
    Цикл опроса статуса платежа.
    Завершается, когда платёж оплачен.
    """
    while True:
        if payment_type == 'card':
            status = await check_yookassa_payment(payment_id)
        else:
            status = await check_oxa_payment(payment_id)
        if status:
            await bot.send_message(
                chat_id=user_id,
                text='✅Оплата прошла успешно'
            )
            await execute_rate(user_id, bot, amount, cost, rate_type, session)
            break
        await asyncio.sleep(interval)


async def execute_rate(user_id: int, bot: Bot, amount: int,
                       cost: int, rate_type: str, session: DataInteraction):
    user = await session.get_user(user_id)
    await session.add_income(cost)
    if user.join:
        await session.update_deeplink_earn(user.join, cost)
    if user.referral:
        await session.increment_user_value(user.referral, 'revives', 1)
        await session.increment_user_value(user.referral, 'revives_earn', 1)

    await session.increment_user_value(user_id, 'revives' if rate_type == 'revive' else 'restores', amount)
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f'Вы успешно приобрели {amount} {get_rate_form(amount, rate_type)}, '
                 f'пожалуйста перезапустите бота нажав\n/start'
        )
    except Exception:
        await session.set_active(user_id, 0)

