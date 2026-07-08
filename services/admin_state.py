states = {}


def set(user_id, action, data=None):
    states[user_id] = {
        "action": action,
        "data": data or {}
    }


def get(user_id):
    return states.get(user_id)


def clear(user_id):
    states.pop(user_id, None)
