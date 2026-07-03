# حالات الأدمن

class AdminState:
    NONE = "none"

    ADD_ITEM = "add_item"
    ADD_FILE = "add_file"

    EDIT_ITEM = "edit_item"
    DELETE_ITEM = "delete_item"

    DELETE_FILE = "delete_file"

    BROADCAST = "broadcast"

    SETTINGS = "settings"


# تخزين الحالة الحالية لكل أدمن
admin_states = {}


def set_state(user_id, state, data=None):
    admin_states[user_id] = {
        "state": state,
        "data": data or {}
    }


def get_state(user_id):
    return admin_states.get(user_id)


def clear_state(user_id):
    admin_states.pop(user_id, None)
