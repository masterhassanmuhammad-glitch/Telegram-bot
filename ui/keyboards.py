from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_keyboard(buttons, columns=2):
    rows = []
    row = []

    for button in buttons:
        text = f"{button['emoji'] or ''} {button['text']}".strip()

        row.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"btn:{button['id']}"
            )
        )

        if len(row) == columns:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return InlineKeyboardMarkup(rows)
