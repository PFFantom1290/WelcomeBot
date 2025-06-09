import logging
import os
import random
import time
import datetime as dt
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# ────────────────────────────
#            CONFIG
# ────────────────────────────
load_dotenv()

BOT_TOKEN  = os.getenv('WELCOME_BOT_TOKEN')
ADMIN_ID   = int(os.getenv('MY_ID'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MAIN_CHANNEL_LINK     = "https://t.me/+NpcxCSbz0VxjMjMy"
PAYMENTS_CHANNEL_LINK = "https://t.me/+ojyK0KkEw-E4NDRi"
GROUP_CHAT_LINK       = "https://t.me/YourGroupChat"  # ← укажите ссылку на групповой чат
CHILL_MANOFF_LINK     = "https://t.me/Chill_manoff"
WHAT_WE_DO_LINK       = "https://telegra.ph/Nashe-napravlenie-05-22"
ELECTRUM_SETUP_LINK   = "https://telegra.ph/Ustanovka-i-nastrojka-Electrum-05-23"
CANCEL_TX_LINK        = "https://telegra.ph/OTMENA-BTC-TRANZAKCII-05-31"
MANAGER_GUIDE_LINK    = "https://telegra.ph/INSTRUKCIYA-DLYA-MENEDZhERA--PERVICHNAYA-OBRABOTKA-ZAYAVKI-05-24"

bot     = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp      = Dispatcher(storage=storage)

# ────────────────────────────
#     MEMBERS / TEAMLEADERS
# ────────────────────────────
TEAM_MEMBERS_RAW = """
чмо:Akatsuki
huesos:Professor
Пончик:Псих
kattyy:Akatsuki
Triggered:Fenix
Бешеный:Псих
Troll:Djenga
Dumbass:Akatsuki
цуцик:Professor
Wack:wa3rix
Пухлый Хомяк:Fenix
Mehach:Девятый
Хахол:Псих
Жмот:Professor
Рижа Мавпа:Akatsuki
Yikes:Djenga
Cr1nge:Псих
Пидр:Девятый
Simp:Fenix
шмаркля:Professor
Шайтан:wa3rix
Karen:Akatsuki
Задрот:Девятый
Boomer:Professor
Гівно:Akatsuki
Пассив:Fenix
Милаш:Djenga
Yeet:Akatsuki
Sus:wa3rix
Flex:Fenix
Ghost:Девятый
Goonia:Djenga
GorilaZZ:Fenix
Wasteman:Akatsuki
cryptoMiner:Akatsuki
соплежуй:Djenga
anaconda:Professor
Penizavr:Девятый
cococola:Professor
Copaster:Псих
уйоба:Fenix
Зеленый:Akatsuki
Пёс Ракета:Djenga
GUSTAVO:wa3rix
Хорек:Professor
Мейкер:Псих
Boom:Fenix
Evolution:Девятый
Амир:Akatsuki
Yakov:wa3rix
Vice:Akatsuki
Артемий:Псих
angerfist:Professor
inVest:Девятый
merzost:Fenix
Наташка:Akatsuki
Dima:Псих
sharpey:wa3rix
gamelol:Professor
MisterX:Professor
SCIPER:Akatsuki
Хорек:Псих
Местный:Девятый
"""

TEAM_MEMBERS = {}
for line in TEAM_MEMBERS_RAW.strip().splitlines():
    if ':' in line:
        member, leader = line.split(':', 1)
        TEAM_MEMBERS.setdefault(leader.strip(), []).append(member.strip())

ALL_MEMBERS = [m for members in TEAM_MEMBERS.values() for m in members]
ALL_TEAMS   = list(TEAM_MEMBERS.keys())

# ────────────────────────────
#        USER DATA
# ────────────────────────────
user_data = {}

def get_user_data(user_id: int) -> dict:
    if user_id not in user_data:
        user_data[user_id] = {
            'wallets': [],
            'last_generation': None,
            'total_profit': 0,
            'weekly_profit': 0,
            'referrals': 0,
            'application_done': False
        }
    return user_data[user_id]

# ────────────────────────────
#           RANKS
# ────────────────────────────
RANKS = {
    "Фрешмен": 0,
    "Грайндер": 2000,
    "Ветеран": 5000,
    "Элита": 10000,
    "Легенда": 20000
}

def get_next_rank(total):
    current = "Фрешмен"
    for r, amt in RANKS.items():
        if total >= amt:
            current = r
    keys = list(RANKS.keys())
    idx  = keys.index(current)
    if idx < len(keys) - 1:
        nxt = keys[idx + 1]
        need = RANKS[nxt] - total
    else:
        nxt, need = "Максимальный", 0
    return current, nxt, need

# ────────────────────────────
#      FSM анкеты
# ────────────────────────────
class Application(StatesGroup):
    waiting_for_name       = State()
    waiting_for_experience = State()
    waiting_for_hours      = State()
    waiting_for_wallet     = State()

# ────────────────────────────
#      ДЕКОРАТОР ДОСТУПА
# ────────────────────────────
def require_application(func):
    async def wrapper(message: types.Message, *args, **kwargs):
        if not get_user_data(message.from_user.id)['application_done']:
            await message.answer("⚠️ Сначала заполните анкету: нажмите /start и выберите «Подать заявку».")
            return
        return await func(message, *args, **kwargs)
    return wrapper

# ────────────────────────────
#        ВСПОМОГАТЕЛЬНЫЕ
# ────────────────────────────
def generate_wallets():
    res = []
    for _ in range(3):
        res.append({
            'eth': '0x' + ''.join(random.choices('0123456789abcdef', k=40)),
            'trx': 'T' + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=33)),
            'created': dt.datetime.now().strftime("%d.%m.%Y")
        })
    return res

def random_top_workers(n=10):
    random.seed(dt.datetime.now().isocalendar().week)  # фиксируется на текущей неделе
    sample = random.sample(ALL_MEMBERS, min(n, len(ALL_MEMBERS)))
    res = []
    for name in sample:
        res.append({
            'name': name,
            'amount': random.randint(1000, 6000),
            'profits': random.randint(1, 15)
        })
    res.sort(key=lambda x: x['amount'], reverse=True)
    return res

# ────────────────────────────
#      КНОПКИ ГЛАВНОГО МЕНЮ
# ────────────────────────────
def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="Мануалы"))
    kb.row(types.KeyboardButton(text="🧬 Мои кошельки"))
    kb.row(types.KeyboardButton(text="📈 Моя статистика"),
           types.KeyboardButton(text="🔝 Топ недели"))
    kb.row(types.KeyboardButton(text="🔝 Команды"),
           types.KeyboardButton(text="💌 Канал"))
    kb.row(types.KeyboardButton(text="🤝 Инвайт"),
           types.KeyboardButton(text="🏦 Выплаты"))
    return kb.as_markup(resize_keyboard=True)

# ────────────────────────────
#            /start
# ────────────────────────────
@dp.message(Command("start"))
async def cmd_start(msg: types.Message, st: FSMContext):
    await st.clear()
    kb = InlineKeyboardBuilder().add(
        types.InlineKeyboardButton(text="✅ Подать заявку", callback_data="apply_from_start")
    )
    welcome = (
        "🖼 <b>ДОБРО ПОЖАЛОВАТЬ!</b>\n\n"
        "Ознакомься с правилами проекта прежде, чем подать заявку.\n\n"
        "⛔ Размещение 18+ медиа любого формата – БАН\n"
        "⛔ Реклама других проектов/услуг без согласования – БАН\n"
        "⛔ Попрошайничество – мут на сутки\n"
        "⛔ Политические срачи – БАН\n"
        "⛔ Саботаж других участников – БАН\n"
        "⛔ Приём платежей на личные кошельки – БАН"
    )
    await msg.answer(welcome, parse_mode=ParseMode.HTML, reply_markup=kb.as_markup())
    await msg.answer("🔹 Выберите действие в меню:", reply_markup=main_menu())

# ────────────────────────────
#     FSM анкеты: шаги
# ────────────────────────────
@dp.callback_query(lambda c: c.data == "apply_from_start")
async def cb_apply(cb: types.CallbackQuery, st: FSMContext):
    await st.set_state(Application.waiting_for_name)
    await cb.message.answer("1. Укажи своё имя и возраст:")
    await cb.answer()

@dp.message(lambda m: m.text == "Подать заявку")
async def apply_btn(msg: types.Message, st: FSMContext):
    await st.set_state(Application.waiting_for_name)
    await msg.answer("1. Укажи своё имя и возраст:")

@dp.message(Application.waiting_for_name)
async def app_name(msg: types.Message, st: FSMContext):
    await st.update_data(name_age=msg.text)
    await st.set_state(Application.waiting_for_experience)
    await msg.answer("2. Опыт работы на звонках/чатах? Если был – опиши подробно")

@dp.message(Application.waiting_for_experience)
async def app_exp(msg: types.Message, st: FSMContext):
    await st.update_data(experience=msg.text)
    await st.set_state(Application.waiting_for_hours)
    await msg.answer("3. Сколько времени готов уделять работе?")

@dp.message(Application.waiting_for_hours)
async def app_hours(msg: types.Message, st: FSMContext):
    await st.update_data(hours=msg.text)
    await st.set_state(Application.waiting_for_wallet)
    await msg.answer("4. Укажи BTC-кошелёк для работы:")

@dp.message(Application.waiting_for_wallet)
async def app_wallet(msg: types.Message, st: FSMContext):
    await st.update_data(btc_wallet=msg.text)
    data = await st.get_data()

    txt = (
        "📄 <b>Новая анкета</b>\n\n"
        f"👤 <b>Имя и возраст:</b> {data['name_age']}\n"
        f"💼 <b>Опыт:</b> {data['experience']}\n"
        f"⏱ <b>Часы:</b> {data['hours']}\n"
        f"💰 <b>BTC:</b> {data['btc_wallet']}\n"
        f"🆔 <b>ID:</b> {msg.from_user.id}"
    )
    try:
        await bot.send_message(ADMIN_ID, txt, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error("Send app error: %s", e)

    await msg.answer(
        "✅ <b>Анкета отправлена на рассмотрение.</b>\n"
        "Скоро с тобой свяжется администратор @Chill_manoff",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu()
    )

    links = InlineKeyboardBuilder().row(
        types.InlineKeyboardButton(text="📢 Канал",  url=MAIN_CHANNEL_LINK),
        types.InlineKeyboardButton(text="💸 Выплаты", url=PAYMENTS_CHANNEL_LINK),
        types.InlineKeyboardButton(text="💬 Чат",     url=GROUP_CHAT_LINK)
    )
    await msg.answer("Подпишись на наши ресурсы:", reply_markup=links.as_markup())

    get_user_data(msg.from_user.id)['application_done'] = True
    await st.clear()

# ────────────────────────────
#        ОБРАБОТЧИКИ МЕНЮ
# ────────────────────────────
@dp.message(lambda m: m.text == "Мануалы")
@require_application
async def manuals(msg: types.Message):
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="Чем занимаемся", url=WHAT_WE_DO_LINK))
    kb.row(types.InlineKeyboardButton(text="Настройка Electrum", url=ELECTRUM_SETUP_LINK))
    kb.row(types.InlineKeyboardButton(text="Отмена BTC транзакций", url=CANCEL_TX_LINK))
    kb.row(types.InlineKeyboardButton(text="Инструкция для менеджера", url=MANAGER_GUIDE_LINK))
    kb.row(types.InlineKeyboardButton(text="👤 Администратор", url=CHILL_MANOFF_LINK))
    await msg.answer("📚 <b>Мануалы</b>:", parse_mode=ParseMode.HTML, reply_markup=kb.as_markup())

@dp.message(lambda m: m.text == "🧬 Мои кошельки")
@require_application
async def wallets(msg: types.Message):
    user = get_user_data(msg.from_user.id)
    if not user['wallets']:
        kb = InlineKeyboardBuilder().add(
            types.InlineKeyboardButton(text="🔐 Сгенерировать ключи", callback_data="generate_wallets")
        )
        await msg.answer("⚠️ Кошельки ещё не сгенерированы.", reply_markup=kb.as_markup())
        return
    text = "🔑 <b>Ваши кошельки</b>\n\n"
    for i, w in enumerate(user['wallets'], 1):
        text += f"<b>Связка #{i}</b> (создана {w['created']})\n• ETH: <code>{w['eth']}</code>\n• TRX: <code>{w['trx']}</code>\n\n"
    await msg.answer(text, parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: c.data == "generate_wallets")
async def gen_wallets(cb: types.CallbackQuery):
    user = get_user_data(cb.from_user.id)
    now = time.time()
    if user['last_generation'] and now - user['last_generation'] < 86400:
        left = 86400 - (now - user['last_generation'])
        h, m = int(left//3600), int((left%3600)//60)
        await cb.message.answer(f"⚠️ Уже генерировали. Повтор через {h}ч {m}м.")
        await cb.answer()
        return
    user['wallets'] = generate_wallets()
    user['last_generation'] = now
    txt = "🎉 <b>Сгенерированы кошельки</b>\n\n"
    for i, w in enumerate(user['wallets'], 1):
        txt += f"<b>Связка #{i}</b>\n• ERC20: <code>{w['eth']}</code>\n• TRC20: <code>{w['trx']}</code>\n\n"
    await cb.message.answer(txt, parse_mode=ParseMode.HTML)
    await cb.answer()

@dp.message(lambda m: m.text == "📈 Моя статистика")
@require_application
async def stats(msg: types.Message):
    u = get_user_data(msg.from_user.id)
    cur, nxt, need = get_next_rank(u['total_profit'])
    await msg.answer(
        "📊 <b>Статистика</b>\n\n"
        f"💵 Всего: {u['total_profit']}$\n"
        f"📅 Неделя: {u['weekly_profit']}$\n"
        f"🏅 Ранг: {cur}\n\n"
        f"До звания {nxt}: {need}$\n"
        f"💸 Выплата (35%): {u['weekly_profit']*0.35}$",
        parse_mode=ParseMode.HTML
    )

@dp.message(lambda m: m.text == "🔝 Топ недели")
@require_application
async def top_week(msg: types.Message):
    top = random_top_workers(10)
    txt = "🏆 <b>Топ воркеров недели</b>\n\n"
    for i, w in enumerate(top, 1):
        txt += f"{i}. <b>{w['name']}</b> — {w['amount']}$, профитов: {w['profits']}\n"
    txt += "\n💸 <b>Канал выплат:</b> " + PAYMENTS_CHANNEL_LINK
    await msg.answer(txt, parse_mode=ParseMode.HTML)

@dp.message(lambda m: m.text == "🔝 Команды")
@require_application
async def teams(msg: types.Message):
    txt = "📋 <b>Список команд</b>\n\n"
    for t in sorted(ALL_TEAMS):
        txt += f"• {t}\n"
    await msg.answer(txt, parse_mode=ParseMode.HTML)

@dp.message(lambda m: m.text == "💌 Канал")
@require_application
async def channels(msg: types.Message):
    kb = InlineKeyboardBuilder().row(
        types.InlineKeyboardButton(text="📢 Канал", url=MAIN_CHANNEL_LINK),
        types.InlineKeyboardButton(text="💸 Выплаты", url=PAYMENTS_CHANNEL_LINK),
        types.InlineKeyboardButton(text="💬 Чат", url=GROUP_CHAT_LINK)
    )
    await msg.answer("📢 <b>Наши каналы и чат</b>", parse_mode=ParseMode.HTML, reply_markup=kb.as_markup())

@dp.message(lambda m: m.text == "🤝 Инвайт")
@require_application
async def invite(msg: types.Message):
    bot_user = await bot.me()
    ref = msg.from_user.username or str(msg.from_user.id)
    link = f"https://t.me/{bot_user.username}?start={ref}"
    kb = InlineKeyboardBuilder().add(
        types.InlineKeyboardButton(text="📤 Поделиться", url=f"tg://msg_url?url={link}&text=Присоединяйся!")
    )
    await msg.answer(
        "🤝 <b>Приглашай друзей!</b>\n\n"
        f"Твоя ссылка:\n<code>{link}</code>\n\n"
        "+5% к выплате за каждого активного реферала.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.as_markup()
    )

@dp.message(lambda m: m.text == "🏦 Выплаты")
@require_application
async def payments(msg: types.Message):
    kb = InlineKeyboardBuilder().add(
        types.InlineKeyboardButton(text="💸 Перейти", url=PAYMENTS_CHANNEL_LINK)
    )
    await msg.answer(
        "💰 <b>Информация о выплатах</b>\n\n"
        "Профиты публикуются в канале выплат. Авто-выплата каждый понедельник.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.as_markup()
    )

# ────────────────────────────
#              RUN
# ────────────────────────────
async def main():
    logger.info("Bot launched")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
