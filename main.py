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

CHAT_INSTALL_REPORT = -1003650441871    # Отчеты по монтажу
CHAT_RECLAMATIONS =  -1003622957990    # Рекламации
CHAT_PAYMENTS = -1003681663061         # Оплаты, рассрочки
CHAT_SUPPLY = -1002365281216 #Чат снабжения




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

    payment_needed = State()

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

class BRFSM(StatesGroup):
    installer = State()
    order = State()
    order_number = State()
    client_lastname = State()
    order_name = State()
    photos = State()
    comment = State()
    confirm = State()


class RPZFSM(StatesGroup):

    installer = State()
    client_lastname = State()
    order = State()
    photos = State()
    comment = State()
    confirm = State()


class PaymentFSM(StatesGroup):
    installer = State()
    order_number = State()
    client_lastname = State()
    order_name = State()
    total_sum = State()
    prepayment = State()
    after_install = State()
    balance = State()
    payment_comment = State()
    confirm = State()
    confirm_report = State()


class SupplyFSM(StatesGroup):
    installer = State()
    order_number = State()
    client_lastname = State()
    order_name = State()
    text = State()
    delivery = State()
    pickup = State()
    photos_supply = State()
    photos_prompt = State()
    sp_photo = State()
    confirm = State()


class ReclamationFSM(StatesGroup):
    installer = State()
    order_number = State()
    client_lastname = State()
    order_name = State()
    rk_name = State()
    text = State()
    ask_photos = State()
    photos = State()
    confirm = State()


class OtherFSM(StatesGroup):
    installer = State()
    work_name = State()
    text = State()
    ask_photos = State()
    photos = State()
    confirm = State()


# ================= HELPERS =================
def kb(*buttons):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=b, callback_data=b)] for b in buttons]
    )

def ikb(*buttons):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=b, callback_data=b)] for b in buttons]
    )

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Новый отчет")],
        [KeyboardButton(text="Отправить БР")], 
        [KeyboardButton(text="Отправить РПЗ")],
        [KeyboardButton(text="Отправить оплату")],
        [KeyboardButton(text="Заказ комплектующих")],
        [KeyboardButton(text="Отчет о рекламации")],
        [KeyboardButton(text="Отчет прочее")]
    ],
    resize_keyboard=True
)


@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите действие:", reply_markup=main_kb)

# ================= START =================
@dp.message(F.text == "Новый отчет")
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
        await cb.message.answer("Заполнен <b>БР</b>?", reply_markup=kb("Да", "Не требуется", "Отправлен ранее"))
        await state.set_state(ReportFSM.br_required)
    else:
        await cb.message.answer("Заполнен <b>РПЗ</b>?", reply_markup=kb("Да", "Не требуется", "Отправлен ранее"))
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
    await msg.answer("Какой <b>клей нужен утром</b>?", reply_markup=kb("Белый", "Прозрачный", "Любой", "Не нужен"))
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
        await ask_payment_needed(cb.message, state)

@dp.message(ReportFSM.act_reason)
async def act_reason(msg: Message, state: FSMContext):
    await state.update_data(act_reason=msg.text)
    await ask_payment_needed(msg, state)


# ================= PAYMENT =================

async def ask_payment_needed(msg: Message, state: FSMContext):
    await msg.answer(
        "Внести информацию об оплате?",
        reply_markup=kb("Да", "Внесена ранее")
    )
    await state.set_state(ReportFSM.payment_needed)

@dp.callback_query(ReportFSM.payment_needed)
async def payment_needed(cb: CallbackQuery, state: FSMContext):
    await cb.answer()

    if cb.data == "Да":
        await start_payment(cb.message, state)

    elif cb.data == "Внесена ранее":
        await cb.message.answer(
            "Отзыв запрошен?",
            reply_markup=kb("Да", "Нет")
        )
        await state.set_state(ReportFSM.review_requested)

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
        reply_markup=kb
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
            f"<b>Монтажник:</b> {d.get('installer', '-')}\n"
            f"<b>Номер заказа:</b> {d.get('order_number', '-')}\n"
            f"<b>Фамилия заказчика:</b> {d.get('client_lastname', '-')}\n"
            f"<b>Наименование заказа:</b> {d.get('order_name', '-')}\n"
            f"<b>Комментарий:</b> {d['br_comment']}\n"
            f"<b>Клей:</b> {d['glue']}"
        )

    elif status == "Завершен" and d.get("rpz_required") == "Да":
        photos = d["rpz_photos"]
        text = (
            "<b>Рекламации (РПЗ)</b>\n\n"
            f"<b>Монтажник:</b> {d.get('installer', '-')}\n"
            f"<b>Номер заказа:</b> {d.get('order_number', '-')}\n"
            f"<b>Фамилия заказчика:</b> {d.get('client_lastname', '-')}\n"
            f"<b>Наименование заказа:</b> {d.get('order_name', '-')}\n"
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

# ================= ОТДЕЛЬНО БР =================

@dp.message(F.text == "Отправить БР")
async def br_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Введите имя монтажника")
    await state.set_state(BRFSM.installer)

@dp.message(BRFSM.installer)
async def br_installer(msg: Message, state: FSMContext):
    await state.update_data(installer=msg.text, photos=[])
    await msg.answer("Фамилия заказчика")
    await state.set_state(BRFSM.client_lastname)


@dp.message(BRFSM.client_lastname)
async def client_lastname(msg: Message, state: FSMContext):
    await state.update_data(client_lastname=msg.text, photos=[])
    await msg.answer("Введите номер заказа")
    await state.set_state(BRFSM.order)


@dp.message(BRFSM.order)
async def br_order(msg: Message, state: FSMContext):
    await state.update_data(order=msg.text)
    await msg.answer("📸 Прикрепите фото БР")
    await state.set_state(BRFSM.photos)


@dp.message(BRFSM.photos, F.photo)
async def br_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    data["photos"].append(msg.photo[-1].file_id)
    await state.update_data(photos=data["photos"])

    await msg.answer("Введите комментарий по БР")
    await state.set_state(BRFSM.comment)


@dp.message(BRFSM.comment)
async def br_comment(msg: Message, state: FSMContext):
    await state.update_data(comment=msg.text)
    d = await state.get_data()

    text = (
        "<b>🧾 БР</b>\n\n"
        f"<b>Монтажник</b>: {d['installer']}\n"
        f"<b>Фамилия заказчика</b>: {d['client_lastname']}\n"
        f"<b>Номер заказа</b>: {d['order']}\n"
        f"<b>Комментарий</b>: {d['comment']}"
    )

    await msg.answer(text, reply_markup=kb("✅ Отправить", "🔄 Отмена"))
    await state.set_state(BRFSM.confirm)


@dp.callback_query(BRFSM.confirm)
async def br_confirm(cb: CallbackQuery, state: FSMContext):
    if cb.data == "🔄 Отмена":
        await state.clear()
        await cb.message.answer("Отменено", reply_markup=kb)
        return

    d = await state.get_data()
    media = [
        InputMediaPhoto(media=p, caption=cb.message.html_text if i == 0 else "")
        for i, p in enumerate(d["photos"])
    ]
    await bot.send_media_group(CHAT_RECLAMATIONS, media)

    await state.clear()
    await cb.message.answer("✅ БР отправлен", reply_markup=kb())

# ================= ОТДЕЛЬНО РПЗ =================

@dp.message(F.text == "Отправить РПЗ")
async def rpz_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Введите имя монтажника")
    await state.set_state(RPZFSM.installer)


@dp.message(RPZFSM.installer)
async def rpz_installer(msg: Message, state: FSMContext):
    await state.update_data(installer=msg.text, photos=[])
    await msg.answer("Фамилия заказчика")
    await state.set_state(RPZFSM.client_lastname)

@dp.message(RPZFSM.client_lastname)
async def client_lastname(msg: Message, state: FSMContext):
    await state.update_data(client_lastname=msg.text, photos=[])
    await msg.answer("Введите номер заказа")
    await state.set_state(RPZFSM.order)

@dp.message(RPZFSM.order)
async def rpz_order(msg: Message, state: FSMContext):
    await state.update_data(order=msg.text)
    await msg.answer("📸 Прикрепите фото РПЗ")
    await state.set_state(RPZFSM.photos)


@dp.message(RPZFSM.photos, F.photo)
async def rpz_photo(msg: Message, state: FSMContext):
    d = await state.get_data()
    d["photos"].append(msg.photo[-1].file_id)
    await state.update_data(photos=d["photos"])

    await msg.answer("Введите комментарий по РПЗ")
    await state.set_state(RPZFSM.comment)


@dp.message(RPZFSM.comment)
async def rpz_comment_only(msg: Message, state: FSMContext):
    await state.update_data(comment=msg.text)
    d = await state.get_data()

    text = (
        "<b>📄 РПЗ</b>\n\n"
        f"<b>Монтажник</b>: {d['installer']}\n"
        f"<b>Заказчик</b>: {d['client_lastname']}\n"
        f"<b>Номер заказа</b>: {d['order']}\n"
        f"<b>Комментарий</b>: {d['comment']}"
    )

    await msg.answer(text, reply_markup=kb("✅ Отправить", "🔄 Отмена"))
    await state.set_state(RPZFSM.confirm)


@dp.callback_query(RPZFSM.confirm)
async def rpz_confirm(cb: CallbackQuery, state: FSMContext):
    if cb.data == "🔄 Отмена":
        await state.clear()
        await cb.message.answer("Отменено", reply_markup=kb)
        return

    d = await state.get_data()
    media = [
        InputMediaPhoto(media=p, caption=cb.message.html_text if i == 0 else "")
        for i, p in enumerate(d["photos"])
    ]
    await bot.send_media_group(CHAT_RECLAMATIONS, media)

    await state.clear()
    await cb.message.answer("✅ РПЗ отправлен", reply_markup=kb())

# ================= ОТДЕЛЬНО ОПЛАТА =================
@dp.message(F.text == "Отправить оплату")
async def start_only_payment(msg: Message, state: FSMContext):
    await msg.answer("Введите <b>Имя монтажника</b>")
    await state.set_state(PaymentFSM.installer)

@dp.message(PaymentFSM.installer)
async def payment_installer(msg: Message, state: FSMContext):
    await state.update_data(installer=msg.text)
    await msg.answer("Введите <b>Номер заказа</b>")
    await state.set_state(PaymentFSM.order_number)


@dp.message(PaymentFSM.order_number)
async def order_number(msg: Message, state: FSMContext):
    await state.update_data(order_number=msg.text)
    await msg.answer("Введите <b>Фамилию заказчика</b>")
    await state.set_state(PaymentFSM.client_lastname)

@dp.message(PaymentFSM.client_lastname)
async def client_lastname(msg: Message, state: FSMContext):
    await state.update_data(client_lastname=msg.text)
    await msg.answer("Введите <b>Наименование заказа</b>")
    await state.set_state(PaymentFSM.order_name)

@dp.message(PaymentFSM.order_name)
async def order_name(msg: Message, state: FSMContext):
    await state.update_data(order_name=msg.text)
    await msg.answer("Введите <b>Сумму заказа (укажи валюту)</b>")
    await state.set_state(PaymentFSM.total_sum)

@dp.message(PaymentFSM.total_sum)
async def total_sum(msg: Message, state: FSMContext):
    await state.update_data(total_sum=msg.text)
    await msg.answer("Введите <b>Предоплату</b>")
    await state.set_state(PaymentFSM.prepayment)


@dp.message(PaymentFSM.prepayment)
async def prepayment(msg: Message, state: FSMContext):
    await state.update_data(prepayment=msg.text)
    await msg.answer("Введите <b>Оплату после монтажа</b>")
    await state.set_state(PaymentFSM.after_install)


@dp.message(PaymentFSM.after_install)
async def after_install(msg: Message, state: FSMContext):
    await state.update_data(after_install=msg.text)
    await msg.answer("Введите <b>Остаток</b>")
    await state.set_state(PaymentFSM.balance)


@dp.message(PaymentFSM.balance)
async def balance(msg: Message, state: FSMContext):
    await state.update_data(balance=msg.text)
    await msg.answer("Введите <b>Комментарий по оплате</b>")
    await state.set_state(PaymentFSM.payment_comment)


@dp.message(PaymentFSM.payment_comment)
async def payment_comment(msg: Message, state: FSMContext):
    await state.update_data(payment_comment=msg.text)

    summary = await build_report_only_summary(state)

    await msg.answer(
        summary,
        reply_markup=payment_confirm_kb()
    )

    await state.set_state(PaymentFSM.confirm_report)

async def build_report_only_summary(state: FSMContext) -> str:
    d = await state.get_data()

    return (
        "<b>🧾 Проверка оплаты</b>\n\n"
        f"<b>Монтажник</b>: {d.get('installer', '-')}\n"
        f"<b>Клиент</b>: {d.get('client_lastname', '-')}\n"
        f"<b>Заказ</b>: {d.get('order_name', '-')}\n"
        f"<b>Сумма</b>: {d.get('total_sum', '-')}\n"
        f"<b>Предоплата</b>: {d.get('prepayment', '-')}\n"
        f"<b>После монтажа</b>: {d.get('after_install', '-')}\n"
        f"<b>Остаток</b>: {d.get('balance', '-')}\n\n"
        "Проверьте данные перед отправкой ⬇️"
    )

def payment_confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отправить отчет",
                    callback_data="payment_send"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Начать заново",
                    callback_data="payment_restart"
                )
            ]
        ]
    )

async def build_payment_only_report(state: FSMContext) -> str:
    d = await state.get_data()

    return (
        "<b>💰 Отчет об оплате</b>\n\n"
        f"<b>Монтажник:</b> {d.get('installer', '-')}\n"
        f"<b>Номер заказа:</b> {d.get('order_number', '-')}\n"
        f"<b>Клиент:</b> {d.get('client_lastname', '-')}\n"
        f"<b>Наименование:</b> {d.get('order_name', '-')}\n\n"
        f"<b>Сумма:</b> {d.get('total_sum', '-')}\n"
        f"<b>Предоплата:</b> {d.get('prepayment', '-')}\n"
        f"<b>После монтажа:</b> {d.get('after_install', '-')}\n"
        f"<b>Остаток:</b> {d.get('balance', '-')}\n\n"
        f"<b>Комментарий:</b> {d.get('payment_comment', '-')}"
    )

@dp.callback_query(PaymentFSM.confirm_report, F.data == "payment_send")
async def payment_send(cb: CallbackQuery, state: FSMContext):
    await send_payment_report(state)

    await state.clear()
    await cb.message.edit_reply_markup()
    await cb.message.answer("✅ Отчет об оплате отправлен")

@dp.callback_query(PaymentFSM.confirm_report, F.data == "payment_restart")
async def payment_restart(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_reply_markup()
    await cb.message.answer("Отчёт сброшен. Нажмите «Отправить оплату», чтобы начать заново.")

# ================= ЗАКАЗ КОМПЛЕКТУЮЩИХ С ПОДТВЕРЖДЕНИЕМ =================

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram import F

# ----------------- Клавиатура Да/Нет -----------------
def yes_no_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="Да"),
                InlineKeyboardButton(text="Нет", callback_data="Нет")
            ]
        ]
    )

YES_NO_MAP = {
    "yes": "Да",
    "no": "Нет"
}
# ----------------- Клавиатура Подтверждения -----------------
def confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="send"),
                InlineKeyboardButton(text="🔄 Отменить", callback_data="cancel")
            ]
        ]
    )

# ----------------- Старт FSM -----------------
@dp.message(F.text == "Заказ комплектующих")
async def supply_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Имя монтажника")
    await state.set_state(SupplyFSM.installer)

@dp.message(SupplyFSM.installer)
async def installer(msg: Message, state: FSMContext):
    await state.update_data(installer=msg.text)
    await msg.answer("Номер заказа")
    await state.set_state(SupplyFSM.order_number)

@dp.message(SupplyFSM.order_number)
async def order_number(msg: Message, state: FSMContext):
    await state.update_data(order_number=msg.text)
    await msg.answer("Фамилия заказчика")
    await state.set_state(SupplyFSM.client_lastname)

@dp.message(SupplyFSM.client_lastname)
async def client_lastname(msg: Message, state: FSMContext):
    await state.update_data(client_lastname=msg.text)
    await msg.answer("Что нужно заказать")
    await state.set_state(SupplyFSM.text)

@dp.message(SupplyFSM.text)
async def text(msg: Message, state: FSMContext):
    await state.update_data(text=msg.text)
    await msg.answer("Срочно?", reply_markup=yes_no_kb())
    await state.set_state(SupplyFSM.delivery)

@dp.callback_query(SupplyFSM.delivery)
async def delivery(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await state.update_data(delivery=cb.data)
    await state.update_data(delivery=YES_NO_MAP.get(cb.data, cb.data))
    await cb.message.answer("Заберешь сам?", reply_markup=yes_no_kb())
    await state.set_state(SupplyFSM.pickup)

@dp.callback_query(SupplyFSM.pickup)
async def pickup(cb: CallbackQuery, state: FSMContext):
    await state.update_data(pickup=cb.data)
    await state.update_data(pickup=YES_NO_MAP.get(cb.data, cb.data))
    await cb.message.answer("Хочешь добавить фото?", reply_markup=yes_no_kb())
    await state.set_state(SupplyFSM.photos_prompt)


@dp.callback_query(SupplyFSM.photos_prompt)
async def photos_prompt(cb: CallbackQuery, state: FSMContext):
    if cb.data == "yes":
        await state.update_data(photos_prompt=cb.data)
        await cb.message.answer("📸 Прикрепите фото")
        await state.update_data(photos_supply=[])
        await state.set_state(SupplyFSM.sp_photo)

    else:
        await cb.message.answer(
            await build_supply_summary(state),
            reply_markup=confirm_kb()
        )
        await state.set_state(SupplyFSM.confirm)

@dp.message(SupplyFSM.sp_photo, F.photo)
async def sp_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos_supply", [])
    photos.append(msg.photo[-1].file_id)
    await state.update_data(photos_supply=photos)

    await msg.answer(
        "Фото добавлено. Проверьте сводку перед отправкой:\n\n"
        + await build_supply_summary(state),
        reply_markup=confirm_kb()
    )

    await state.set_state(SupplyFSM.confirm)


# ================= СВОДКА =================

async def build_supply_summary(state: FSMContext) -> str:
    data = await state.get_data()
    return (
        "<b>🧩 Заказ комплектующих</b>\n\n"
        f"<b>Монтажник:</b> {data.get('installer')}\n"
        f"<b>Номер заказа:</b> {data.get('order_number')}\n"
        f"<b>Фамилия клиента:</b> {data.get('client_lastname')}\n"
        f"<b>Что нужно заказать:</b> {data.get('text')}\n"
        f"<b>Срочно?:</b> {data.get('delivery')}\n"
        f"<b>Заберешь сам?:</b> {data.get('pickup')}\n"
    )


# ================= ПОДТВЕРЖДЕНИЕ =================

@dp.callback_query(SupplyFSM.confirm)
async def confirm_supply(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()

    if cb.data == "send":
        text = await build_supply_summary(state)
        photos = data.get("photos_supply", [])

        if photos:
            media = [
                InputMediaPhoto(media=p, caption=text if i == 0 else "")
                for i, p in enumerate(photos)
            ]
            await bot.send_media_group(CHAT_SUPPLY, media)
        else:
            await bot.send_message(CHAT_SUPPLY, text)

        await state.clear()
        await cb.message.answer("✅ Заказ отправлен", reply_markup=None)

    elif cb.data == "cancel":
        await state.clear()
        await cb.message.answer("❌ Заказ отменен", reply_markup=None)


# ================= ОТЧЕТ РЕКЛАМАЦИИ =================

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

# ------------------- Клавиатуры -------------------

def yes_no_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="yes")],
            [InlineKeyboardButton(text="Нет", callback_data="no")],
        ]
    )

def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить", callback_data="send")],
            [InlineKeyboardButton(text="🔄 Заново", callback_data="restart")],
        ]
    )



@dp.message(F.text == "Отчет о рекламации")
async def reclamation_only_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Имя монтажника")
    await state.set_state(ReclamationFSM.installer)

@dp.message(ReclamationFSM.installer)
async def installer(msg: Message, state: FSMContext):
    await state.update_data(installer=msg.text, photos=[])
    await msg.answer("Наименование рекламации")
    await state.set_state(ReclamationFSM.rk_name)

@dp.message(ReclamationFSM.rk_name)
async def rk_name(msg: Message, state: FSMContext):
    await state.update_data(rk_name=msg.text)
    await msg.answer("Отчет о выполненной работы")
    await state.set_state(ReclamationFSM.text)

@dp.message(ReclamationFSM.text)
async def text(msg: Message, state: FSMContext):
    await state.update_data(text=msg.text)
    await msg.answer("Хочешь прикрепить фото?", reply_markup=yes_no_kb())
    await state.set_state(ReclamationFSM.ask_photos)

@dp.callback_query(ReclamationFSM.ask_photos)
async def ask_photos(cb: CallbackQuery, state: FSMContext):
    if cb.data == "yes":
        await cb.message.answer("📸 Прикрепите фото рекламации")
        await state.update_data(photos=[])
        await state.set_state(ReclamationFSM.photos)
    else:
        await cb.message.answer(
            "Проверьте сводку отчета перед отправкой:\n\n"
            "<b>Имя монтажника:</b> {installer}\n"
            "<b>Наименование:</b> {rk_name}\n"
            "<b>Описание:</b> {text}".format(**await state.get_data()),
            reply_markup=confirm_kb()
        )
        await state.set_state(ReclamationFSM.confirm)

@dp.message(ReclamationFSM.photos, F.photo)
async def reclamation_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(msg.photo[-1].file_id)
    await state.update_data(photos=photos)

    # После прикрепления фото предлагаем подтверждение
    await msg.answer(
        "Фото добавлено. Проверьте сводку перед отправкой:\n\n"
        "<b>Имя монтажника:</b> {installer}\n"
        "<b>Наименование:</b> {rk_name}\n"
        "<b>Описание:</b> {text}".format(**await state.get_data()),
        reply_markup=confirm_kb()
    )
    await state.set_state(ReclamationFSM.confirm)

@dp.callback_query(ReclamationFSM.confirm)
async def reclamation_confirm(cb: CallbackQuery, state: FSMContext):
    if cb.data == "restart":
        await state.clear()
        await cb.message.answer("Начнем заново", reply_markup=None)
        return

    data = await state.get_data()
    photos = data.get("photos", [])

    if photos:
        media = [
            InputMediaPhoto(media=p, caption=data["text"] if i == 0 else "")
            for i, p in enumerate(photos)
        ]
        await bot.send_media_group(CHAT_RECLAMATIONS, media)
    else:
        await bot.send_message(
            CHAT_RECLAMATIONS,
            "<b>📝 Рекламация</b>\n\n"
            f"Имя монтажника: {data['installer']}\n"
            f"Наименование: {data['rk_name']}\n"
            f"Описание: {data['text']}"
        )

    await state.clear()
    await cb.message.answer("✅ Рекламация отправлена", reply_markup=None)


# ================= ОТЧЕТ ПРОЧЕЕ =================

@dp.message(F.text == "Отчет прочее")
async def other_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Имя монтажника")
    await state.set_state(OtherFSM.installer)

@dp.message(OtherFSM.installer)
async def other_installer(msg: Message, state: FSMContext):
    await state.update_data(installer=msg.text, photos=[])
    await msg.answer("Наименование работ")
    await state.set_state(OtherFSM.work_name)

@dp.message(OtherFSM.work_name)
async def other_work_name(msg: Message, state: FSMContext):
    await state.update_data(work_name=msg.text)
    await msg.answer("Отчет о выполнении")
    await state.set_state(OtherFSM.text)

@dp.message(OtherFSM.text)
async def other_text(msg: Message, state: FSMContext):
    await state.update_data(text=msg.text)
    await msg.answer("Хочешь прикрепить фото?", reply_markup=yes_no_kb())
    await state.set_state(OtherFSM.ask_photos)

@dp.callback_query(OtherFSM.ask_photos)
async def other_ask_photos(cb: CallbackQuery, state: FSMContext):
    if cb.data == "yes":
        await cb.message.answer("📸 Прикрепите фото")
        await state.update_data(photos=[])
        await state.set_state(OtherFSM.photos)
    else:
        await cb.message.answer(
            "Проверьте сводку отчета перед отправкой:\n\n"
            "<b>Имя монтажника:</b> {installer}\n"
            "<b>Наименование работ:</b> {work_name}\n"
            "<b>Отчет:</b> {text}".format(**await state.get_data()),
            reply_markup=confirm_kb()
        )
        await state.set_state(OtherFSM.confirm)

@dp.message(OtherFSM.photos, F.photo)
async def other_photos(msg: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(msg.photo[-1].file_id)
    await state.update_data(photos=photos)

    await msg.answer(
        "Фото добавлено. Проверьте сводку отчета перед отправкой:\n\n"
        "<b>Имя монтажника:</b> {installer}\n"
        "<b>Наименование работ:</b> {work_name}\n"
        "<b>Отчет:</b> {text}".format(**await state.get_data()),
        reply_markup=confirm_kb()
    )
    await state.set_state(OtherFSM.confirm)

@dp.callback_query(OtherFSM.confirm)
async def other_confirm(cb: CallbackQuery, state: FSMContext):
    if cb.data == "restart":
        await state.clear()
        await cb.message.answer("Начнем заново", reply_markup=None)
        return

    data = await state.get_data()
    photos = data.get("photos", [])

    if photos:
        media = [
            InputMediaPhoto(media=p, caption=data["text"] if i == 0 else "")
            for i, p in enumerate(photos)
        ]
        await bot.send_media_group(CHAT_INSTALL_REPORT, media)
    else:
        await bot.send_message(
            CHAT_INSTALL_REPORT,
            "<b>📌 Прочее</b>\n\n"
            f"Имя монтажника: {data['installer']}\n"
            f"Наименование работ: {data['work_name']}\n"
            f"Отчет: {data['text']}"
        )

    await state.clear()
    await cb.message.answer("✅ Отправлено", reply_markup=None)


# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

