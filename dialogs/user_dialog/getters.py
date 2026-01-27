from aiogram.types import CallbackQuery, User, Message, ContentType
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput

from utils.text_utils import get_action_prompt
from utils.wrapper_funcs import generate_wrapper
from utils.ai_funcs import restore_image, revive_image
from database.action_data_class import DataInteraction
from config_data.config import load_config, Config
from states.state_groups import startSG


config: Config = load_config()


async def start_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    admin = False
    admins = [*config.bot.admin_ids]
    admins.extend([admin.user_id for admin in await session.get_admins()])
    if event_from_user.id in admins:
        admin = True
    return {
        'full_name': event_from_user.full_name,
        'admin': admin
    }


async def get_restore_photo(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(msg.from_user.id)
    if not user.restores:
        dialog_manager.dialog_data['gen'] = 'restore'
        await dialog_manager.switch_to(startSG.enough_balance)
        return
    enable_photos = [photo for photo in msg.photo[::-1] if photo.width in range(300, 820) and photo.height in range(300, 820)]
    photo = enable_photos[0] if enable_photos else msg.photo[-1]
    result = await generate_wrapper(
        restore_image,
        msg.bot,
        msg.from_user.id,
        4.5,
        photo, msg.bot
    )
    print(result)
    if isinstance(result, dict):
        await msg.answer(f'🚨Во время реставрации вашего фото произошла какая-то ошибка\n<code>'
                         f'{result.get("error") if result else ""}</code>\nПожалуйста попробуйте снова или '
                         f'обратитесь в поддержку')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    await session.increment_user_value(msg.from_user.id, 'restores', -1)
    await session.increment_user_value(msg.from_user.id, 'restores_count', 1)
    dialog_manager.dialog_data['media'] = result
    await dialog_manager.switch_to(startSG.restore_result)


async def restore_result_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    media = dialog_manager.dialog_data.get('media')
    media = MediaAttachment(type=ContentType.PHOTO, url=media)
    return {
        'media': media
    }


async def get_revive_image(msg: Message, widget: MessageInput, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(msg.from_user.id)
    if user.revives < 1:
        dialog_manager.dialog_data['gen'] = 'revive'
        await dialog_manager.switch_to(startSG.enough_balance)
        return
    enable_photos = [photo for photo in msg.photo[::-1] if photo.width in range(300, 820) and photo.height in range(300, 820)]
    photo = enable_photos[0] if enable_photos else msg.photo[-1]
    dialog_manager.dialog_data['photo'] = photo
    await dialog_manager.switch_to(startSG.revive_action_menu, show_mode=ShowMode.DELETE_AND_SEND)


async def revive_action_choose(clb: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    photo = dialog_manager.dialog_data.get('photo')

    action = clb.data.split('_')[0]
    prompt, motion_id = get_action_prompt(action)

    result = await generate_wrapper(
        revive_image,
        clb.bot,
        clb.from_user.id,
        12.5,
        prompt, photo, clb.bot, motion_id
    )
    if isinstance(result, dict) or result is None:
        await clb.message.answer(f'🚨Во время оживления вашего фото произошла какая-то ошибка\n<code>'
                                 f'{result.get("error") if result else ""}</code>\nПожалуйста попробуйте снова или '
                                 f'обратитесь в поддержку')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    print(result)
    await session.increment_user_value(clb.from_user.id, 'revives', -1)
    await session.increment_user_value(clb.from_user.id, 'revives_count', 1)
    dialog_manager.dialog_data['media'] = result
    await dialog_manager.switch_to(startSG.revive_result)


async def get_revive_prompt(msg: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    photo = dialog_manager.dialog_data.get('photo')

    template = (
        "cinematic short film, professional color grading, person {action}, "
        "natural subtle movement, realistic expression, soft cinematic lighting, "
        "realistic skin textures, film grain, 4k, photorealistic, "
        "modest and tasteful presentation"
    )
    prompt = template.replace("{action}", text.lower().strip())
    motion_id = 'd2389a9a-91c2-4276-bc9c-c9e35e8fb85a'

    result = await generate_wrapper(
        revive_image,
        msg.bot,
        msg.from_user.id,
        12.5,
        prompt, photo, msg.bot, motion_id
    )
    if isinstance(result, dict) or result is None:
        await msg.answer(f'🚨Во время оживления вашего фото произошла какая-то ошибка\n<code>'
                         f'{result.get("error") if result else ""}</code>\nПожалуйста попробуйте снова или '
                         f'обратитесь в поддержку')
        dialog_manager.dialog_data.clear()
        await dialog_manager.switch_to(startSG.start)
        return
    print(result)
    await session.increment_user_value(msg.from_user.id, 'revives', -1)
    await session.increment_user_value(msg.from_user.id, 'revives_count', 1)
    dialog_manager.dialog_data['media'] = result
    await dialog_manager.switch_to(startSG.revive_result)


async def revive_result_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    media = dialog_manager.dialog_data.get('media')
    media = MediaAttachment(type=ContentType.VIDEO, url=media)
    return {
        'media': media
    }


async def manual_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    text = ('<b>Инструкция по использованию бота</b>\n\nПривет! 👋\nЭтот бот помогает оживлять фотографии — добавлять '
            'движение, мимику и эмоции в портрет.\n\n<b>Вот как всё работает:</b>\n1. Отправь фото человека или '
            'нескольких людей — просто загрузите снимок в чат.\n2. Бот обработает изображение и создаст короткую '
            'видео-анимацию.\n3. С готовым результатом можно делать что угодно: скачать или отправить друзьям.\n\n'
            '<b>💡 Совет для лучшего результата:</b>\nЧтобы анимация выглядела естественно и качественно, важно '
            'хорошее исходное фото.\n\n<b>Рекомендации</b>\n<em>✅ Подходящие фото:</em>\n\n1. Лицо чётко видно, '
            'нет размытия.\n2. Человек смотрит прямо или слегка в сторону.\n3. Хорошее освещение, без резких теней.\n'
            '4. Два человека в кадре допустимы, если нужно оживить обоих.\n5. Чем лучше проработаны черты лица, тем '
            'естественнее получится эффект ✨\n\n<em>⛔️ Не подходят:</em>\n\n1. Фото с затемнённым, слишком тёмным или'
            ' пересвеченным лицом.\n2. Снимки, где лицо слишком маленькое или далеко от камеры.\n3. Размытые, '
            'искажённые или слишком отфильтрованные изображения.\n4. Фото, где человек стоит спиной к камере.\n\n<em>В '
            'любом случае, если что-то не получилось, не устроил результат или есть какие-то вопросы смело обращайтесь '
            'в нашу поддержку - @ , всегда поможем и всё расскажем.</em>')
    return {
        'text': text
    }


async def ref_menu_getters(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    text = (f'<b>🎁 Реферальная программа</b>\n\n<b>❓Как получить бесплатно оживление:</b>\nПригласите друга по '
            f'Вашей ссылке. Когда он <b>пополнит свой</b> баланс, вам автоматически начислится бонус в виде 1-го '
            f'оживления.\n\n<b>📊 Ваша статистика:</b>\n👥 Всего приглашено: {user.refs}\n'
            f'🫰 Всего получено оживлений: {user.revives_earn}\n\n🎞Оживлений на балансе: {user.revives}'
            f'\n\n🔗Ваша реферальная ссылка:\n<code>https://t.me/Fotovmagic_bot?start={user.user_id}</code>'
            f'\n\n<em>Поделитесь ссылкой и получите одно оживление бесплатно!</em>')
    return {
        'text': text,
        'ref_link': f'http://t.me/share/url?url=https://t.me/Fotovmagic_bot?start={user.user_id}'
    }


async def profile_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    text = (f'<b>👤 Ваш профиль</b>\n\n<blockquote>🆔ID: {event_from_user.id}\nОсталось реставраций: {user.restores}\n'
            f'Осталось оживлений: {user.revives}\n🖼Восстановлено фотографий: {user.restores_count}'
            f'\n🎬Оживлено фотографий: {user.revives_count}</blockquote>')
    return {
        'text': text
    }


async def enough_balance_getter(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    session: DataInteraction = dialog_manager.middleware_data.get('session')
    user = await session.get_user(event_from_user.id)
    gen = dialog_manager.dialog_data.get('gen')
    return {
        'balance': f'Всего реставраций на балансе: {user.restores}\nНеобходимо: 1' if gen == 'restore'
        else f'Всего оживлений на балансе: {user.restores}\nНеобходимо: 1'
    }

