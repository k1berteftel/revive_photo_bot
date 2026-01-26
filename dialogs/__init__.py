from dialogs.user_dialog.dialog import user_dialog
from dialogs.payment_dialog.dialog import payment_dialog
from dialogs.admin_dialog.dialog import admin_dialog


def get_dialogs():
    return [user_dialog, payment_dialog, admin_dialog]