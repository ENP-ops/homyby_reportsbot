import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# ================= CONFIG =================
BOT_TOKEN = "7688447373:AAGzewb-O3z5Xv6lNPoYf6BZ6EJ66h4sXAQ"

bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=MemoryStorage())

CHAT_INSTALL_REPORT = -1003650441871   # Отчеты по монтажу
CHAT_RECLAMATIONS = -5232810928   # Рекламации
CHAT_PAYMENTS = -1003681663061         # Оплаты, рассрочки




# ================= FSM =================
class ReportFSM(StatesGroup):
    installer = State()
    order_number = State()
    client_lastname = State()
    order_name = State()

    install_photos = State()
    install_status = State()

    # BR (Продолжается)
    br_required = State()
    br_photos = State()
    br_comment = State()
    glue = State()

    # RPZ (Завершен)
    rpz_required = State()
    rpz_photos = State()
    rpz_comment = State()

    # Act + payment
    act_filled = State()
    act_reason = State()

    total_sum = State()
    prepayment = State()
    after_install = State()
    balance = State()
    payment_comment = State()

    review_requested = State()
    review_reason = State()

    tomorrow_agreed = State()
    tomorrow_reason = State()

    final_info = State()

    confirm_report = State()



# ================= HELPERS =================
def kb(*buttons):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=b, callback_data=b)] for b in buttons]
    )

# Клавиатура с одной кнопкой
new_report_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Новый отчет")]
    ],
    resize_keyboard=True,  # подстраиваем под экран
    one_time_keyboard=False  # клавиатура остаётся видимой после нажатия
)
@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Нажмите кнопку «Новый отчет», чтобы начать.",
        reply_markup=new_report_kb
    )

# ================= START =================
@dp.message(F.text == "📝 Новый отчет")
async def start(msg: Message):
    await msg.answer("Нажмите кнопку для создания отчета", reply_markup=kb("Создать отчет"))


@dp.callback_query(F.data == "Создать отчет")
async def new_report(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("Введите <b>Имя монтажника</b>")
    await state.set_state(ReportFSM.installer)


# ================= BASE DATA =================
@dp.message(ReportFSM.installer)
async def installer(msg: Message, state: FSMContext):
    await state.update_data(installer=msg.text)
    await msg.answer("Введите <b>Номер заказа</b>")
    await state.set_state(ReportFSM.order_number)


@dp.message(ReportFSM.order_number)
async def order_number(msg: Message, state: FSMContext):
    await state.update_data(order_number=msg.text)
    await msg.answer("Введите <b>Фамилию заказчика</b>")
    await state.set_state(ReportFSM.client_lastname)


@dp.message(ReportFSM.client_lastname)
async def client_lastname(msg: Message, state: FSMContext):
    await state.update_data(client_lastname=msg.text)
    await msg.answer("Введите <b>Наименование заказа</b>")
    await state.set_state(ReportFSM.order_name)


@dp.message(ReportFSM.order_name)
async def order_name(msg: Message, state: FSMContext):
    await state.update_data(order_name=msg.text, install_photos=[])
    await msg.answer("📸 <b>Фото с монтажа</b>\nОтправьте одно или несколько фото")
    await state.set_state(ReportFSM.install_photos)


# ================= INSTALL PHOTOS =================

@dp.message(ReportFSM.install_photos, F.photo, ~F.media_group_id)
async def install_single_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("install_photos", [])

    photos.append(msg.photo[-1].file_id)
    await state.update_data(install_photos=photos)

    if not data.get("status_sent"):
        await msg.answer(
            "Выберите статус монтажа:",
            reply_markup=kb("Продолжается", "Завершен")
        )
        await state.update_data(status_sent=True)

# Временное хранилище для накопления фото по пользователю
temp_photos = {}
processed_groups = set()

@dp.message(ReportFSM.install_photos, F.media_group_id)
async def install_photos_group(msg: Message, state: FSMContext):
    media_group_id = msg.media_group_id

    # если альбом уже обработан — выходим
    if media_group_id in processed_groups:
        return

    # собираем фото
    photos_group = temp_photos.get(media_group_id, [])

    if msg.photo:
        photos_group.append(msg.photo[-1].file_id)
        temp_photos[media_group_id] = photos_group

    # ⏳ ждём, пока Telegram пришлёт весь альбом
    await asyncio.sleep(1.2)

    # повторная проверка (важно!)
    if media_group_id in processed_groups:
        return

    processed_groups.add(media_group_id)

    # 🔹 сохраняем фото в FSM ОДИН РАЗ
    data = await state.get_data()
    existing_photos = data.get("install_photos", [])

    for photo in temp_photos.get(media_group_id, []):
        if photo not in existing_photos:
            existing_photos.append(photo)

    await state.update_data(install_photos=existing_photos)

    # 🔹 отправляем кнопки статуса монтажа ОДИН РАЗ
    if not data.get("status_sent"):
        await msg.answer(
            "Выберите статус монтажа:",
            reply_markup=kb("Продолжается", "Завершен")
        )
        await state.update_data(status_sent=True)

    # 🧹 чистим временные данные
    temp_photos.pop(media_group_id, None)

# ================= STATUS =================
@dp.callback_query(F.data.in_(["Продолжается", "Завершен"]))
async def install_status(cb: CallbackQuery, state: FSMContext):
    await state.update_data(install_status=cb.data)

    if cb.data == "Продолжается":
        await cb.message.answer("Заполнен <b>БР</b>?", reply_markup=kb("Да", "Не требуется"))
        await state.set_state(ReportFSM.br_required)
    else:
        await cb.message.answer("Заполнен <b>РПЗ</b>?", reply_markup=kb("Да", "Не требуется"))
        await state.set_state(ReportFSM.rpz_required)


# ================= BR FLOW =================
@dp.callback_query(ReportFSM.br_required)
async def br_required(cb: CallbackQuery, state: FSMContext):
    await state.update_data(br_required=cb.data)

    if cb.data == "Да":
        await cb.message.answer("📸 Прикрепите <b>фото БР</b>")
        await state.update_data(br_photos=[])
        await state.set_state(ReportFSM.br_photos)
    else:
        await state.set_state(ReportFSM.final_info)
        await cb.message.answer("Введите <b>Дополнительную информацию по монтажу</b>")

@dp.message(ReportFSM.br_photos, F.photo, ~F.media_group_id)
async def br_single_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("br_photos", [])

    photos.append(msg.photo[-1].file_id)
    await state.update_data(br_photos=photos)

    # ❗ переход к следующему шагу
    await msg.answer("Введите <b>Комментарий по БР</b>")
    await state.set_state(ReportFSM.br_comment)

temp_photos = {}  # ключ: media_group_id, значение: список file_id
processed_groups = set()

@dp.message(ReportFSM.br_photos, F.media_group_id)
async def br_photos_group(msg: Message, state: FSMContext):
    media_group_id = msg.media_group_id

    if media_group_id in processed_groups:
        return

    photos_group = temp_photos.get(media_group_id, [])

    if msg.photo:
        photos_group.append(msg.photo[-1].file_id)
        temp_photos[media_group_id] = photos_group

    # ⏳ ждём, пока прилетят все фото альбома
    await asyncio.sleep(1.2)

    # повторно проверяем — вдруг другой хендлер уже обработал
    if media_group_id in processed_groups:
        return

    processed_groups.add(media_group_id)

    data = await state.get_data()
    existing_photos = data.get("br_photos", [])

    for photo in temp_photos.get(media_group_id, []):
        if photo not in existing_photos:
            existing_photos.append(photo)

    await state.update_data(br_photos=existing_photos)

    # ❗ отправляем сообщение ОДИН раз
    await msg.answer("Введите <b>Комментарий по БР</b>")
    await state.set_state(ReportFSM.br_comment)

    # чистим временные данные
    temp_photos.pop(media_group_id, None)
 
    
@dp.message(ReportFSM.br_comment)
async def br_comment(msg: Message, state: FSMContext):
    await state.update_data(br_comment=msg.text)
    await msg.answer("Какой <b>клей нужен утром</b>?", reply_markup=kb("Белый", "Прозрачный", "Не нужен"))
    await state.set_state(ReportFSM.glue)


@dp.callback_query(ReportFSM.glue)
async def glue(cb: CallbackQuery, state: FSMContext):
    await state.update_data(glue=cb.data)
    await cb.message.answer("Введите <b>Дополнительную информацию по монтажу</b>")
    await state.set_state(ReportFSM.final_info)


# ================= RPZ FLOW =================
@dp.callback_query(ReportFSM.rpz_required)
async def rpz_required(cb: CallbackQuery, state: FSMContext):
    await state.update_data(rpz_required=cb.data)

    if cb.data == "Да":
        await cb.message.answer("📸 Прикрепите <b>фото РПЗ</b>")
        await state.update_data(rpz_photos=[])
        await state.set_state(ReportFSM.rpz_photos)
    else:
        await state.set_state(ReportFSM.act_filled)
        await cb.message.answer("Заполнен <b>Акт</b>?", reply_markup=kb("Да", "Нет"))

@dp.message(ReportFSM.rpz_photos, F.photo, ~F.media_group_id)
async def rpz_single_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("rpz_photos", [])

    photos.append(msg.photo[-1].file_id)
    await state.update_data(rpz_photos=photos)

    # 🔹 переход к комментарию ОДИН РАЗ
    await msg.answer("Введите <b>Комментарий по РПЗ</b>")
    await state.set_state(ReportFSM.rpz_comment)

temp_photos = {}          # media_group_id -> list[file_id]
processed_groups = set()  # защита от повторной обработки

@dp.message(ReportFSM.rpz_photos, F.media_group_id)
async def rpz_photos_group(msg: Message, state: FSMContext):
    media_group_id = msg.media_group_id

    # ⛔ если альбом уже обработан — выходим
    if media_group_id in processed_groups:
        return

    # собираем фото альбома
    photos_group = temp_photos.get(media_group_id, [])

    if msg.photo:
        photos_group.append(msg.photo[-1].file_id)
        temp_photos[media_group_id] = photos_group

    # ⏳ ждём все фото от Telegram
    await asyncio.sleep(1.2)

    # повторная защита
    if media_group_id in processed_groups:
        return

    processed_groups.add(media_group_id)

    # 🔹 сохраняем в FSM ОДИН РАЗ
    data = await state.get_data()
    existing_photos = data.get("rpz_photos", [])

    for photo in temp_photos.get(media_group_id, []):
        if photo not in existing_photos:
            existing_photos.append(photo)

    await state.update_data(rpz_photos=existing_photos)

    # 🔹 открываем комментарий ОДИН РАЗ
    await msg.answer("Введите <b>Комментарий по РПЗ</b>")
    await state.set_state(ReportFSM.rpz_comment)

    # 🧹 очищаем временные данные
    temp_photos.pop(media_group_id, None)  


@dp.message(ReportFSM.rpz_comment)
async def rpz_comment(msg: Message, state: FSMContext):
    await state.update_data(rpz_comment=msg.text)
    await msg.answer("Заполнен <b>Акт</b>?", reply_markup=kb("Да", "Нет"))
    await state.set_state(ReportFSM.act_filled)


# ================= ACT =================
@dp.callback_query(ReportFSM.act_filled)
async def act_filled(cb: CallbackQuery, state: FSMContext):
    await state.update_data(act_filled=cb.data)

    if cb.data == "Нет":
        await cb.message.answer("Укажи причину (акт)")
        await state.set_state(ReportFSM.act_reason)
    else:
        await start_payment(cb.message, state)


@dp.message(ReportFSM.act_reason)
async def act_reason(msg: Message, state: FSMContext):
    await state.update_data(act_reason=msg.text)
    await start_payment(msg, state)


# ================= PAYMENT =================
async def start_payment(msg: Message, state: FSMContext):
    await msg.answer("Введите <b>Сумму заказа (укажи валюту)</b>")
    await state.set_state(ReportFSM.total_sum)


@dp.message(ReportFSM.total_sum)
async def total_sum(msg: Message, state: FSMContext):
    await state.update_data(total_sum=msg.text)
    await msg.answer("Введите <b>Предоплату</b>")
    await state.set_state(ReportFSM.prepayment)


@dp.message(ReportFSM.prepayment)
async def prepayment(msg: Message, state: FSMContext):
    await state.update_data(prepayment=msg.text)
    await msg.answer("Введите <b>Оплату после монтажа</b>")
    await state.set_state(ReportFSM.after_install)


@dp.message(ReportFSM.after_install)
async def after_install(msg: Message, state: FSMContext):
    await state.update_data(after_install=msg.text)
    await msg.answer("Введите <b>Остаток</b>")
    await state.set_state(ReportFSM.balance)


@dp.message(ReportFSM.balance)
async def balance(msg: Message, state: FSMContext):
    await state.update_data(balance=msg.text)
    await msg.answer("Введите <b>Комментарий по оплате</b>")
    await state.set_state(ReportFSM.payment_comment)


@dp.message(ReportFSM.payment_comment)
async def payment_comment(msg: Message, state: FSMContext):
    await state.update_data(payment_comment=msg.text)
    await msg.answer("Отзыв запрошен?", reply_markup=kb("Да", "Нет"))
    await state.set_state(ReportFSM.review_requested)

# ================= Сводка на проверку =================

async def build_report_summary(state: FSMContext) -> str:
    d = await state.get_data()

    text = (
        "<b>📋 Сводка отчёта</b>\n\n"
        f"<b>Монтажник:</b> {d.get('installer', '-')}\n"
        f"<b>Номер заказа:</b> {d.get('order_number', '-')}\n"
        f"<b>Фамилия заказчика:</b> {d.get('client_lastname', '-')}\n"
        f"<b>Наименование заказа:</b> {d.get('order_name', '-')}\n"
        f"<b>Статус монтажа:</b> {d.get('install_status', '-')}\n\n"
        f"<b>Фото монтажа:</b> {len(d.get('install_photos', []))} шт.\n"
    )

    if d.get("install_status") == "Продолжается":
        text += (
            f"<b>БР:</b> {d.get('br_required', '-')}\n"
            f"<b>Фото БР:</b> {len(d.get('br_photos', []))} шт.\n"
            f"<b>Комментарий БР:</b> {d.get('br_comment', '-')}\n"
        )
    else:
        text += (
            f"<b>РПЗ:</b> {d.get('rpz_required', '-')}\n"
            f"<b>Фото РПЗ:</b> {len(d.get('rpz_photos', []))} шт.\n"
            f"<b>Комментарий РПЗ:</b> {d.get('rpz_comment', '-')}\n"
        )

    text += (
        "\n<b>Оплата:</b>\n"
        f"Сумма заказа: {d.get('total_sum', '-')}\n"
        f"Предоплата: {d.get('prepayment', '-')}\n"
        f"После монтажа: {d.get('after_install', '-')}\n"
        f"Остаток: {d.get('balance', '-')}\n\n"
        f"<b>Комментарий по оплате:</b> {d.get('payment_comment', '-')}\n\n"
        f"<b>Доп. информация:</b> {d.get('final_info', '-')}\n\n"
        "Проверьте данные перед отправкой."
    )

    return text

# ================= FINAL =================

@dp.callback_query(ReportFSM.review_requested)
async def review_requested(cb: CallbackQuery, state: FSMContext):
    await state.update_data(review_requested=cb.data)

    if cb.data == "Нет":
        await cb.message.answer("Укажи причину (отзыв)")
        await state.set_state(ReportFSM.review_reason)
    else:
        await ask_tomorrow(cb.message, state)


@dp.message(ReportFSM.review_reason)
async def review_reason(msg: Message, state: FSMContext):
    await state.update_data(review_reason=msg.text)
    await ask_tomorrow(msg, state)


async def ask_tomorrow(msg: Message, state: FSMContext):
    await msg.answer("На завтра договорился?", reply_markup=kb("Да", "Нет"))
    await state.set_state(ReportFSM.tomorrow_agreed)


@dp.callback_query(ReportFSM.tomorrow_agreed)
async def tomorrow_agreed(cb: CallbackQuery, state: FSMContext):
    await state.update_data(tomorrow_agreed=cb.data)

    if cb.data == "Нет":
        await cb.message.answer("Укажи причину (завтра)")
        await state.set_state(ReportFSM.tomorrow_reason)
    else:
        await finish(cb.message, state)


@dp.message(ReportFSM.tomorrow_reason)
async def tomorrow_reason(msg: Message, state: FSMContext):
    await state.update_data(tomorrow_reason=msg.text)
    await finish(msg, state)


async def finish(msg: Message, state: FSMContext):
    await msg.answer("Введите <b>Дополнительную информацию</b>")
    await state.set_state(ReportFSM.final_info)


@dp.message(ReportFSM.final_info)
async def final_info(msg: Message, state: FSMContext):
    await state.update_data(final_info=msg.text)

    summary = await build_report_summary(state)

    await msg.answer(
        summary,
        reply_markup=kb("✅ Отправить отчет", "🔄 Начать заново")
    )
    await state.set_state(ReportFSM.confirm_report)

@dp.callback_query(ReportFSM.confirm_report, F.data == "✅ Отправить отчет")
async def confirm_send(cb: CallbackQuery, state: FSMContext):
    await send_install_report(state)
    await send_reclamations_report(state)
    await send_payment_report(state)

    await state.clear()
    await cb.message.answer("✅ Отчет успешно отправлен")

@dp.callback_query(ReportFSM.confirm_report, F.data == "🔄 Начать заново")
async def restart_report(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer(
        "Отчёт сброшен. Нажмите «Новый отчет», чтобы начать заново.",
        reply_markup=new_report_kb
    )

async def send_install_report(state: FSMContext):
    d = await state.get_data()
    status = d["install_status"]

    if status == "Продолжается":
        text = (
            "<b>Отчет по монтажу</b>\n\n"
            f"<b>Имя монтажника:</b> {d['installer']}\n"
            f"<b>Номер заказа:</b> {d['order_number']}\n"
            f"<b>Фамилия заказчика:</b> {d['client_lastname']}\n"
            f"<b>Наименование заказа:</b> {d['order_name']}\n"
            f"<b>Статус монтажа:</b> {status}\n"
            f"<b>Заполнен БР?:</b> {d.get('br_required')}\n"
            f"<b>Доп. информация:</b> {d.get('final_info', '-')}"
        )
    else:
        text = (
            "<b>Отчет по монтажу</b>\n\n"
            f"<b>Имя монтажника:</b> {d['installer']}\n"
            f"<b>Номер заказа:</b> {d['order_number']}\n"
            f"<b>Фамилия заказчика:</b> {d['client_lastname']}\n"
            f"<b>Наименование заказа:</b> {d['order_name']}\n"
            f"<b>Статус монтажа:</b> {status}\n"
            f"<b>Заполнен РПЗ?:</b> {d.get('rpz_required')}\n"
            f"<b>Заполнен Акт?:</b> {d.get('act_filled')}\n"
            f"<b>Причина (акт):</b> {d.get('act_reason', '-')}\n"
            f"<b>Отзыв запрошен?:</b> {d.get('review_requested')}\n"
            f"<b>Причина (отзыв):</b> {d.get('review_reason', '-')}\n"
            f"<b>На завтра договорился?:</b> {d.get('tomorrow_agreed')}\n"
            f"<b>Причина (завтра):</b> {d.get('tomorrow_reason', '-')}\n"
            f"<b>Доп. информация:</b> {d.get('final_info', '-')}"
        )

    media = [
        InputMediaPhoto(media=pid, caption=text if i == 0 else "")
        for i, pid in enumerate(d["install_photos"])
    ]
    await bot.send_media_group(CHAT_INSTALL_REPORT, media)


async def send_reclamations_report(state: FSMContext):
    d = await state.get_data()
    status = d["install_status"]

    if status == "Продолжается" and d.get("br_required") == "Да":
        photos = d["br_photos"]
        text = (
            "<b>Рекламации (БР)</b>\n\n"
            f"<b>Комментарий:</b> {d['br_comment']}\n"
            f"<b>Клей:</b> {d['glue']}"
        )

    elif status == "Завершен" and d.get("rpz_required") == "Да":
        photos = d["rpz_photos"]
        text = (
            "<b>Рекламации (РПЗ)</b>\n\n"
            f"<b>Комментарий:</b> {d['rpz_comment']}"
        )
    else:
        return

    media = [
        InputMediaPhoto(media=pid, caption=text if i == 0 else "")
        for i, pid in enumerate(photos)
    ]
    await bot.send_media_group(CHAT_RECLAMATIONS, media)


async def send_payment_report(state: FSMContext):
    d = await state.get_data()

    payment_fields = [
        d.get("total_sum"),
        d.get("prepayment"),
        d.get("after_install"),
        d.get("balance"),
        d.get("payment_comment"),
    ]

    # 🔴 Если все поля пустые — отчет НЕ отправляем
    if not any(payment_fields):
        return

    text = (
        "<b>Отчет об оплате</b>\n\n"
        f"<b>Имя монтажника:</b> {d.get('installer')}\n"
        f"<b>Номер заказа:</b> {d.get('order_number')}\n"
        f"<b>Фамилия заказчика:</b> {d.get('client_lastname')}\n"
        f"<b>Наименование заказа:</b> {d.get('order_name')}\n"
        f"<b>Статус монтажа:</b> {d.get('install_status')}\n\n"
        f"<b>Сумма заказа:</b> {d.get('total_sum', '-')}\n"
        f"<b>Предоплата:</b> {d.get('prepayment', '-')}\n"
        f"<b>Оплата после монтажа:</b> {d.get('after_install', '-')}\n"
        f"<b>Остаток:</b> {d.get('balance', '-')}\n"
        f"<b>Комментарий по оплате:</b> {d.get('payment_comment', '-')}"
    )

    await bot.send_message(CHAT_PAYMENTS, text)


# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




