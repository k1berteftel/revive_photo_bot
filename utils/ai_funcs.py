import os
import logging
import asyncio
from pathlib import Path
import aiohttp
import base64
from aiohttp import ClientTimeout

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


async def _image_to_url(image: PhotoSize, bot: Bot) -> str | None:
    if not os.path.exists('download'):
        os.mkdir('download')
    image_path = f"download/temp_{image.file_unique_id}.jpg"

    try:
        await bot.download(file=image.file_id, destination=image_path)
    except Exception:
        return None
    logger.info('success add image')
    url = 'https://files.storagecdn.online/upload'

    data = aiohttp.FormData()
    data.add_field('file',
                   open(image_path, 'rb'),
                   filename=Path(image_path).name,
                   content_type='application/octet-stream')

    headers = {
        'Authorization': f'Bearer {config.unifically.api_token}'
    }

    logger.info(f'Start image to url: {image_path}')

    async with aiohttp.ClientSession() as session:
        async with session.put(url, data=data, headers=headers, ssl=False) as response:
            logger.info('success put image')
            if response.status not in [200, 201]:
                logger.info(f'Image to url error response: {await response.text()}')
                return None
            data = await response.json()
            logger.info(f'get image json data: {data}')
            if data['success'] != True:
                logger.info(f'Image to url output: {data["message"]}')
                return None
    try:
        os.remove(image_path)
    except Exception:
        ...
    return data['file_url']


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


async def restore_image(image: PhotoSize, bot: Bot):
    logger.info('start restore image')
    image = await _image_to_url(image, bot)
    logger.info(f'get image url: {image}')
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
            "image_urls": [image],
            "quality": "2K"
        }
    }
    async with aiohttp.ClientSession() as client:
        async with client.post(url, headers=headers, json=data, ssl=False) as response:
            logger.info(f'response status: {response.status}')
            #print(await response.text())
            if response.status not in [200, 201]:
                data = await response.json()
                return {'error': f"{data['data'].get('code')}: {data['data'].get('message')}"}
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
        "model": "higgsfield-ai/standard",
        "input": {
            "prompt": prompt,
            "start_image_url": image,
            "motion_id": motion_id
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


async def test_func():
    url = 'https://api.unifically.com/higgsfield/motions'

    headers = {
        'Authorization': f'Bearer {config.unifically.api_token}'
    }

    data = {
        'size': 60,
        'preset_family': 'higgsfield'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=data, headers=headers, ssl=False) as response:
            if response.status not in [200, 201]:
                logger.info(f'Error: {await response.json()}')
                return None
            data = await response.json()
            print(data)

#asyncio.run(test_func())

