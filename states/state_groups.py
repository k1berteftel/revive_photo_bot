from aiogram.fsm.state import State, StatesGroup

# Обычная группа состояний


class startSG(StatesGroup):
    start = State()

    get_restore_photo = State()

    get_revive_photo = State()
    revive_action_menu = State()
    get_revive_prompt = State()

    manual = State()

    profile = State()
    ref_menu = State()

    enough_balance = State()


class PaymentSG(StatesGroup):
    choose_rate_type = State()
    choose_rate = State()
    choose_payment = State()
    process_payment = State()


class adminSG(StatesGroup):
    start = State()

    get_mail = State()
    get_time = State()
    get_keyboard = State()
    confirm_mail = State()

    deeplinks_menu = State()
    get_deeplink_name = State()
    deeplink_menu = State()

    rate_menu = State()
    choose_rate_type = State()
    get_rate_cost = State()
    get_rate_amount = State()
    get_rate_text = State()
    del_rate = State()

    admin_menu = State()
    admin_del = State()
    admin_add = State()
