import os
import logging
import asyncio
import aiohttp
import base64
from pathlib import Path
from aiohttp import ClientTimeout

from PIL import Image
from aiogram import Bot
from aiogram.types import PhotoSize

from config_data.config import Config, load_config


config: Config = load_config()


format = '[{asctime}] #{levelname:8} {filename}:' \
         '{lineno} - {name} - {message}'

logging.basicConfig(
    level=logging.DEBUG,
    format=format,
    style='{'
)


logger = logging.getLogger(__name__)

ALLOWED_ASPECT_RATIOS = {
    '16:9': 16 / 9, '4:3': 4 / 3, '1:1': 1, '3:4': 3 / 4,
    '9:16': 9 / 16, '2:3': 2 / 3, '1:2': 0.5, '2:1': 2,
    '4:5': 0.8, '3:2': 1.5, '5:4': 1.25, '21:9': 21 / 9
}


def _find_closest_aspect_ratio(width: int, height: int, use_min: bool = True) -> str:
    """
    Находит ближайшее или наиболее отдаленное допустимое соотношение сторон.

    Args:
        width: ширина изображения
        height: высота изображения
        use_min: если True - находит минимально отличающееся соотношение,
                если False - находит максимально отличающееся соотношение
    """
    if height == 0:
        return '1:1'  # fallback

    current_ratio = width / height

    if use_min:
        # Находим ближайшее допустимое соотношение (минимальное отклонение)
        closest_ratio = min(ALLOWED_ASPECT_RATIOS.items(),
                            key=lambda x: abs(x[1] - current_ratio))
    else:
        # Находим наиболее отдаленное допустимое соотношение (максимальное отклонение)
        closest_ratio = max(ALLOWED_ASPECT_RATIOS.items(),
                            key=lambda x: abs(x[1] - current_ratio))

    return closest_ratio[0]


def _resize_to_target_aspect(image: Image.Image, target_ratio: str) -> Image.Image:
    """Изменяет изображение до целевого соотношения сторон"""
    width, height = image.size
    target_ratio_value = ALLOWED_ASPECT_RATIOS[target_ratio]
    current_ratio = width / height

    # Если соотношение уже достаточно близкое, не меняем
    if abs(current_ratio - target_ratio_value) < 0.01:
        return image

    # Определяем новые размеры для обрезки
    if current_ratio > target_ratio_value:
        # Текущее изображение шире целевого (обрезаем по бокам)
        new_height = height
        new_width = int(height * target_ratio_value)
        left = (width - new_width) // 2
        top = 0
        right = left + new_width
        bottom = height
    else:
        # Текущее изображение уже целевого (обрезаем сверху и снизу)
        new_width = width
        new_height = int(width / target_ratio_value)
        left = 0
        top = (height - new_height) // 2
        right = width
        bottom = top + new_height

    # Обрезаем изображение с центра
    cropped = image.crop((left, top, right, bottom))
    return cropped


async def _image_to_url(image: PhotoSize, bot: Bot, resize: bool = False, use_min: bool = True) -> str | None:
    """
    Загружает изображение и возвращает URL

    Args:
        image: PhotoSize объект из aiogram
        bot: Bot объект для скачивания
        resize: Если True, изменяет изображение до допустимого формата.
                Если False, оставляет как есть.
        use_min: Если True - использует минимально отличающийся формат,
                если False - использует максимально отличающийся формат

    Returns:
        URL загруженного изображения или None при ошибке
    """
    if not os.path.exists('download'):
        os.mkdir('download')

    temp_path = f"download/temp_{image.file_unique_id}.jpg"
    processed_path = f"download/processed_{image.file_unique_id}.jpg"

    try:
        # Скачиваем изображение
        await bot.download(file=image.file_id, destination=temp_path)
        logger.info('success download image')

        # Открываем и проверяем изображение
        with Image.open(temp_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            if resize:
                # Находим допустимое соотношение сторон (ближайшее или наиболее отдаленное)
                target_ratio = _find_closest_aspect_ratio(img.width, img.height, use_min=use_min)
                current_ratio = img.width / img.height

                logger.info(
                    f'Resizing image (use_min={use_min}): {img.width}x{img.height}, '
                    f'current ratio: {current_ratio:.3f}, target ratio: {target_ratio}')

                processed_img = _resize_to_target_aspect(img, target_ratio)
                processed_img.save(processed_path, 'JPEG', quality=95, optimize=True)

                logger.info(
                    f'Resized to: {processed_img.width}x{processed_img.height}, '
                    f'new ratio: {processed_img.width / processed_img.height:.3f}')
            else:
                # Если resize=False, используем оригинал
                logger.info(f'Using original image: {img.width}x{img.height}, ratio: {img.width / img.height:.3f}')
                img.save(processed_path, 'JPEG', quality=95, optimize=True)

        # Загружаем обработанное изображение
        url = 'https://files.storagecdn.online/upload'

        with open(processed_path, 'rb') as file:
            data = aiohttp.FormData()
            data.add_field('file',
                           file,
                           filename=Path(processed_path).name,
                           content_type='image/jpeg')

            headers = {
                'Authorization': f'Bearer {config.unifically.api_token}'
            }

            logger.info(f'Start image to url: {processed_path}')

            async with aiohttp.ClientSession() as session:
                async with session.put(url, data=data, headers=headers, ssl=False) as response:
                    logger.info('success put image')
                    if response.status not in [200, 201]:
                        logger.error(f'Image to url error response: {await response.text()}')
                        return None
                    response_data = await response.json()
                    logger.info(f'get image json data: {response_data}')
                    if response_data.get('success') != True:
                        logger.error(f'Image to url output: {response_data.get("message", "Unknown error")}')
                        return None

        return response_data['file_url']

    except Exception as e:
        logger.error(f'Error processing image: {e}')
        return None

    finally:
        # Удаляем временные файлы
        for file_path in [temp_path, processed_path]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.debug(f'Error removing temp file {file_path}: {e}')


async def _polling_restore_image(task_id: str) -> list[str] | dict:
    url = f'https://api.unifically.com/v1/tasks/{task_id}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.unifically.api_token}'
    }
    async with aiohttp.ClientSession() as client:
        while True:
            async with client.get(url, headers=headers, ssl=False) as response:
                if response.status not in [200, 201]:
                    data = await response.json()
                    return {'error': f"{data['data'].get('code')}: {data['data'].get('message')}"}
                data = await response.json()
                logger.info(f'get polling data: {data}')
            if data['data']['status'] == 'failed':
                return {'error': f"{data['data'].get('code')}: {data['data'].get('message')}"}
            if data['data']['status'] == 'completed':
                return data['data']['output']['image_url']
            await asyncio.sleep(6)


async def restore_image(image: PhotoSize, bot: Bot, resize: bool = False, attempt: int = 0):
    """
    Восстанавливает изображение с попытками:
    1. Без ресайза (если это первая попытка)
    2. С ресайзом до ближайшего формата (минимальное отклонение)
    3. С ресайзом до наиболее отдаленного формата (максимальное отклонение)
    """
    logger.info(f'start restore image, attempt: {attempt}')

    # Определяем параметры для текущей попытки
    if attempt == 0:
        # Первая попытка: оригинальное изображение
        current_resize = False
        use_min = True  # не используется при resize=False
    elif attempt == 1:
        # Вторая попытка: ресайз до ближайшего формата
        current_resize = True
        use_min = True
    elif attempt == 2:
        # Третья попытка: ресайз до наиболее отдаленного формата
        current_resize = True
        use_min = False
    else:
        # Больше попыток нет
        return {'error': 'Max attempts exceeded (3 attempts)'}

    image_url = await _image_to_url(image, bot, resize=current_resize, use_min=use_min)
    if not image_url:
        return {'error': 'Failed to upload image'}

    logger.info(f'get image url: {image_url}')
    url = 'https://api.unifically.com/v1/tasks'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.unifically.api_token}'
    }
    data = {
        "model": "black-forest-labs/flux.2-pro",
        "input": {
            "prompt": "extremely high detail professional photo restoration and colorization, remove all scratches, dust, "
                      "stains, noise, and damage, enhance facial features and textures, realistic skin tones, natural "
                      "color palette, sharp focus on eyes, improve resolution and clarity, cinematic lighting, 8k, "
                      "masterpiece, photorealistic",
            "image_urls": [image_url],
            "aspect_ratio": "auto",
            "resolution": "2k"
        }
    }

    async with aiohttp.ClientSession() as client:
        async with client.post(url, headers=headers, json=data, ssl=False) as response:
            logger.info(f'response status: {response.status}')
            if response.status not in [200, 201]:
                error_data = await response.json()
                code = error_data['data'].get('code')
                message = error_data['data'].get('message')
                print(f"Attempt {attempt + 1} failed: {code}, {message}")

                # Если это validation_error и есть еще попытки
                if code == 'validation_error' and attempt < 2:
                    logger.info(f'Retrying with different aspect ratio, attempt: {attempt + 1}')
                    return await restore_image(image, bot, True, attempt + 1)

                return {'error': f"{code}: {message}"}

            data = await response.json()
            logger.info(f'post output data: {data}')

        if data['code'] != 200:
            return {'error': f"{data['data'].get('code')}: {data['data'].get('message')}"}

        if data['data'].get('output'):
            return data['data']['output']['image_url']

        task_id = data['data'].get('task_id')
        logger.info('success post image')

    return await _polling_restore_image(task_id)


async def _polling_revive_image(task_id: str):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.unifically.api_token}'
    }
    url = f'https://api.unifically.com/v1/tasks/{task_id}'

    async with aiohttp.ClientSession() as client:
        while True:
            async with client.get(url, headers=headers) as response:
                if response.status != 200:
                    return {'error': await response.text()}
                data = await response.json()
                print(data)
                if data['data']['status'] == 'failed':
                    return {"error": f"{data['data']['error']['code']}: {data['data']['error']['message']}"}
                if data['data']['status'] == 'completed':
                    return data['data']['output']['video_url']
                await asyncio.sleep(14)


async def revive_image(prompt: str, image: PhotoSize, bot: Bot, motion_id: str = 'd2389a9a-91c2-4276-bc9c-c9e35e8fb85a'):
    image = await _image_to_url(image, bot)
    url = 'https://api.unifically.com/v1/tasks'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.unifically.api_token}'
    }
    data = {
        "model": "bytedance/seedance-1.5-pro",
        "input": {
            "prompt": prompt,
            "start_image_url": image,
            #"motion_id": motion_id
            "resolution": "1080p",
            "duration": 4
            #"start_image_url": image,
        }
    }
    async with aiohttp.ClientSession() as client:
        async with client.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                return {'error': await response.text()}
            data = await response.json()
            if data['code'] != 200:
                error = f"{data['code']}: {data['data']['error']['message']}"
                return {'error': error}
            task_id = data['data']['task_id']
    return await _polling_revive_image(task_id)


async def test_func(motion_id: str = 'd2389a9a-91c2-4276-bc9c-c9e35e8fb85a'):
    #image = await _image_to_url(image, bot)
    prompt = ("cinematic short film, professional color grading, person making gentle hugging gesture with arms, "
              "affectionate expression, warm smile, subtle arm movement as if embracing someone, "
              "emotional connection visible in eyes, soft natural lighting, realistic skin textures, "
              "film grain, 24fps, 4k, photorealistic, masterpiece, modest clothing, family moment")
    url = 'https://api.unifically.com/v1/tasks'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.unifically.api_token}'
    }
    data = {
        "model": "higgsfield-ai/standard",
        "input": {
            "prompt": prompt,
            "start_image_url": "https://i.pinimg.com/736x/12/9e/43/129e43d6cf96d9d5e9fe95b387b561fd.jpg",
            "motion_id": motion_id
            #"duration": 4
            #"start_image_url": image,
        }
    }
    async with aiohttp.ClientSession() as client:
        async with client.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                return {'error': await response.text()}
            data = await response.json()
            if data['code'] != 200:
                error = f"{data['code']}: {data['data']['error']['message']}"
                return {'error': error}
            task_id = data['data']['task_id']
    return await _polling_revive_image(task_id)


#print(asyncio.run(test_func()))

