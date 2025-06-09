"""
WelcomeBot.py  —  полный, проверенный файл
Dependencies:
    pip install aiogram~=3.4 apscheduler python-dotenv
"""

import asyncio
import datetime as dt
import logging
import os
import random
import time
from typing import Dict, List

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# ─────────────────── ENV / CONFIG ───────────────────
load_dotenv()

BOT_TOKEN = os.getenv("WELCOME_BOT_TOKEN", "")
ADMIN_ID  = int(os.getenv("MY_ID", "0"))

if not BOT_TOKEN or not ADMIN_ID:
    raise RuntimeError("Переменные WELCOME_BOT_TOKEN и/или MY_ID не заданы!")

MAIN_CHANNEL_LINK     = "https://t.me/+NpcxCSbz0VxjMjMy"
PAYMENTS_CHANNEL_LINK = "https://t.me/+ojyK0KkEw-E4NDRi"
CHILL_MANOFF_LINK     = "https://t.me/Chill_manoff"
WHAT_WE_DO_LINK       = "https://telegra.ph/Nashe-napravlenie-05-22"
ELECTRUM_SETUP_LINK   = "https://telegra.ph/Ustanovka-i-nastrojka-Electrum-05-23"
CANCEL_TX_LINK        = "https://telegra.ph/OTMENA-BTC-TRANZAKCII-05-31"
MANAGER_GUIDE_LINK    = "https://telegra.ph/INSTRUKCIYA-DLYA-MENEDZHERA--PERVICHNAYA-OBRABOTKA-ZAYAVKI-05-24"

# ─────────────────── LOGGING ────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────── BOT & SCHEDULER ───────────────
bot      = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
storage  = MemoryStorage()
dp       = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler(timezone="UTC")  # глобальный

# ─────────────────── DATA STORAGE ────────────────
user_data: Dict[int, Dict] = {}
weekly_top = {"teams": [], "workers": []}

# ─────────────────── HELPERS ───────────────────────
def get_user(uid: int) -> Dict:
    if uid not in user_data:
        user_data[uid] = {
            "wallets": [],
            "last_generation": None,
            "total_profit": 0,
            "weekly_profit": 0,
            "referrals": 0,
        }
    return user_data[uid]

def generate_wallets() -> List[Dict]:
    out = []
    for _ in range(3):
        out.append(
            {
                "eth": "0x" + "".join(random.choices("0123456789abcdef", k=40)),
                "trx": "T"  + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=33)),
                "created": dt.datetime.now().strftime("%d.%m.%Y"),
            }
        )
    return out

def random_top_teams(n: int) -> List[Dict]:
    names = ["Fenix", "Professor", "Djenga", "Девятый", "Akatsuki", "Medici", "wa3rix"]
    teams = [
        {
            "name": random.choice(names),
            "amount": random.randint(1_000, 10_000),
            "profits": random.randint(1, 20),
        }
        for _ in range(n)
    ]
    teams.sort(key=lambda x: x["amount"], reverse=True)
    return teams

def random_top_workers(n: int) -> List[Dict]:
    names = ["Наташка", "angerfist", "Хорек", "Шарк", "CARAVEL", "Холодрыга", "Не торт"]
    workers = [
        {
            "name": random.choice(names),
            "amount": random.randint(500, 5_000),
            "profits": random.randint(1, 10),
        }
        for _ in range(n)
    ]
    workers.sort(key=lambda x: x["amount"], reverse=True)
    return workers

def update_weekly_lists() -> None:
    weekly_top["teams"]   = random_top_teams(7)
    weekly_top["workers"] = random_top_workers(10)
    logger.info("Weekly TOP lists regenerated")

# ─────────────────── RANKS ─────────────────────────
RANKS = {
    "Фрешмен": 0,
    "Грайндер": 2_000,
    "Ветеран": 5_000,
    "Элита": 10_000,
    "Легенда": 20_000,
}

def next_rank(amount: int) -> tuple[str, str, int]:
    current = "Фрешмен"
    for rank, border in RANKS.items():
        if amount >= border:
            current = rank

    keys = list(RANKS)
    idx  = keys.index(current)
    if idx < len(keys) - 1:
        nxt = keys[idx + 1]
        need = RANKS[nxt] - amount
    else:
        nxt, need = "Максимум", 0
    return current, nxt, need

# ─────────────────── FSM STATES ────────────────────
class Application(StatesGroup):
    waiting_for_name       = State()
    waiting_for_experience = State()
    waiting_for_hours      = State()
    waiting_for_wallet     = State()

# ─────────────────── KEYBOARDS ─────────────────────
def main_menu() -> types.ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="Мануалы"))
    kb.row(types.KeyboardButton(text="🧬 Мои кошельки"))
    kb.row(
        types.KeyboardButton(text="📈 Моя статистика"),
        types.KeyboardButton(text="🔝 Топ недели"),
    )
    kb.row(
        types.KeyboardButton(text="🔝 Команды"),
        types.KeyboardButton(text="💌 Канал"),
    )
    kb.row(
        types.KeyboardButton(text="🤝 Инвайт"),
        types.KeyboardButton(text="🏦 Выплаты"),
    )
    return kb.as_markup(resize_keyboard=True)

# ─────────────────── AUTO-CONFIRM ──────────────────
async def auto_confirm(user_id: int) -> None:
    leaders = ["Fenix", "Professor", "Djenga", "Девятый", "Akatsuki", "Medici", "wa3rix"]
    chosen  = random.choice(leaders)

    text = (
        f"✅ <b>Ваша заявка подтверждена!</b>\n"
        f"Ваш тимлид – <b>{chosen}</b>.\n\n"
        f"📢 <a href='{MAIN_CHANNEL_LINK}'>Основной канал</a>\n"
        f"💸 <a href='{PAYMENTS_CHANNEL_LINK}'>Канал выплат</a>\n"
        f"👥 <a href='{CHILL_MANOFF_LINK}'>Чат команды</a>"
    )
    await bot.send_message(user_id, text, disable_web_page_preview=True)

# ─────────────────── HANDLERS ──────────────────────
@dp.message(Command("start"))
async def cmd_start(msg: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="✅ Подать заявку", callback_data="apply"))
    await msg.answer(
        "🖼 <b>ДОБРО ПОЖАЛОВАТЬ!</b>\n\n"
        "Ты находишься в нужном месте и в нужное время. Ознакомься с правилами проекта прежде, чем подать заявку.",
        "⛔ Размещение 18+ медиа любого формата – БАН.",
        "⛔ Реклама других проектов/услуг без согласования с администрацией – БАН.",
        "⛔ Попрошайничество – мут на сутки.",
        "⛔ Срачи на политические темы – БАН моментально.",
        "⛔ Саботировать/подставлять/провоцировать других участников – БАН.",
        "⛔ Прием платежей на свои кошельки – БАН.",
        ""
        "Нажимая 'Подать заявку' ты подтверждаешь своё согласие с правилами. ✍️"
        reply_markup=kb.as_markup(),
    )

# ── Заявка шаги
@dp.callback_query(lambda c: c.data == "apply")
async def apply_step_1(cb: types.CallbackQuery, state: FSMContext):
    await state.set_state(Application.waiting_for_name)
    await cb.message.answer("1. Укажи своё имя и возраст:")
    await cb.answer()

@dp.message(Application.waiting_for_name)
async def apply_step_2(msg: types.Message, state: FSMContext):
    await state.update_data(name_age=msg.text)
    await state.set_state(Application.waiting_for_experience)
    await msg.answer("2. Был ли опыт работы на звонках/чатах?")

@dp.message(Application.waiting_for_experience)
async def apply_step_3(msg: types.Message, state: FSMContext):
    await state.update_data(experience=msg.text)
    await state.set_state(Application.waiting_for_hours)
    await msg.answer("3. Сколько часов готовы уделять работе?")

@dp.message(Application.waiting_for_hours)
async def apply_step_4(msg: types.Message, state: FSMContext):
    await state.update_data(hours=msg.text)
    await state.set_state(Application.waiting_for_wallet)
    await msg.answer("4. Адрес BTC-кошелька:")

@dp.message(Application.waiting_for_wallet)
async def apply_finish(msg: types.Message, state: FSMContext):
    await state.update_data(btc_wallet=msg.text)
    data = await state.get_data()

    # админу
    txt = (
        "📄 <b>Новая анкета</b>\n\n"
        f"👤 <b>Имя/возраст:</b> {data['name_age']}\n"
        f"💼 <b>Опыт:</b> {data['experience']}\n"
        f"⏱ <b>Часы:</b> {data['hours']}\n"
        f"💰 <b>BTC:</b> {data['btc_wallet']}\n"
        f"🆔 <b>ID:</b> {msg.from_user.id}"
    )
    await bot.send_message(ADMIN_ID, txt)

    # авто-подтверждение
    delay = random.randint(10, 20)
    scheduler.add_job(
        auto_confirm,
        "date",
        run_date=dt.datetime.utcnow() + dt.timedelta(minutes=delay),
        kwargs={"user_id": msg.from_user.id},
    )

    await msg.answer("✅ Анкета отправлена!", reply_markup=main_menu())
    await state.clear()

# ── Мануалы
@dp.message(lambda m: m.text == "Мануалы")
async def manuals(msg: types.Message):
    kb = InlineKeyboardBuilder()
    for title, link in [
        ("Чем занимаемся", WHAT_WE_DO_LINK),
        ("Настройка Electrum", ELECTRUM_SETUP_LINK),
        ("Отмена транзакций", CANCEL_TX_LINK),
        ("Инструкция менеджера", MANAGER_GUIDE_LINK),
    ]:
        kb.row(types.InlineKeyboardButton(text=title, url=link))
    await msg.answer("📚 Мануалы:", reply_markup=kb.as_markup())

# ── Кошельки
@dp.callback_query(lambda c: c.data == "generate_wallets")
async def wallets_generate(cb: types.CallbackQuery):
    user = get_user(cb.from_user.id)
    now  = time.time()

    if user["last_generation"] and now - user["last_generation"] < 24 * 3600:
        remain = 24 * 3600 - (now - user["last_generation"])
        h, m = divmod(int(remain // 60), 60)
        await cb.message.answer(f"Повторная генерация через {h}ч {m}м.")
        await cb.answer()
        return

    user["wallets"] = generate_wallets()
    user["last_generation"] = now

    txt = "🎉 <b>Новые кошельки сгенерированы!</b>\n\n"
    for i, w in enumerate(user["wallets"], 1):
        txt += (
            f"<b>#{i}</b>\n"
            f"• ERC20: <code>{w['eth']}</code>\n"
            f"• TRC20: <code>{w['trx']}</code>\n\n"
        )
    await cb.message.answer(txt)
    await cb.answer()

@dp.message(lambda m: m.text == "🧬 Мои кошельки")
async def wallets_show(msg: types.Message):
    user = get_user(msg.from_user.id)
    if not user["wallets"]:
        kb = InlineKeyboardBuilder()
        kb.add(types.InlineKeyboardButton(text="🔐 Сгенерировать ключи", callback_data="generate_wallets"))
        await msg.answer("Кошельки ещё не созданы.", reply_markup=kb.as_markup())
        return

    txt = "🔑 <b>Ваши кошельки</b>\n\n"
    for i, w in enumerate(user["wallets"], 1):
        txt += (
            f"<b>#{i}</b> (от {w['created']})\n"
            f"• ETH: <code>{w['eth']}</code>\n"
            f"• TRX: <code>{w['trx']}</code>\n\n"
        )
    await msg.answer(txt)

# ── Статистика
@dp.message(lambda m: m.text == "📈 Моя статистика")
async def my_stats(msg: types.Message):
    user = get_user(msg.from_user.id)
    cur, nxt, need = next_rank(user["total_profit"])
    await msg.answer(
        "📊 <b>Статистика</b>\n\n"
        f"💵 Всего: <b>{user['total_profit']}$</b>\n"
        f"📅 Неделя: <b>{user['weekly_profit']}$</b>\n"
        f"🏅 Ранг: <b>{cur}</b>\n"
        f"➡️ До <b>{nxt}</b>: <b>{need}$</b>"
    )

# ── ТОПы
@dp.message(lambda m: m.text == "🔝 Команды")
async def top_teams(msg: types.Message):
    txt = "🏆 <b>Топ команд за неделю</b>\n\n"
    for i, t in enumerate(weekly_top["teams"], 1):
        txt += f"{i}. <b>{t['name']}</b> — {t['amount']}$ | профитов: {t['profits']}\n"
    await msg.answer(txt)

@dp.message(lambda m: m.text == "🔝 Топ недели")
async def top_workers(msg: types.Message):
    txt = "🏆 <b>Топ воркеров недели</b>\n\n"
    for i, w in enumerate(weekly_top["workers"], 1):
        txt += f"{i}. <b>{w['name']}</b> — {w['amount']}$ | профитов: {w['profits']}\n"
    txt += f"\n💸 <b>Канал выплат:</b> {PAYMENTS_CHANNEL_LINK}"
    await msg.answer(txt)

# ── Каналы
@dp.message(lambda m: m.text == "💌 Канал")
async def channels(msg: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="📢 Основной канал", url=MAIN_CHANNEL_LINK),
        types.InlineKeyboardButton(text="💸 Канал выплат", url=PAYMENTS_CHANNEL_LINK),
    )
    await msg.answer("Подпишись, чтобы не пропустить новости:", reply_markup=kb.as_markup())

# ── Инвайт
@dp.message(lambda m: m.text == "🤝 Инвайт")
async def invite(msg: types.Message):
    bot_username = (await bot.get_me()).username
    ref_code = msg.from_user.username or str(msg.from_user.id)
    link = f"https://t.me/{bot_username}?start={ref_code}"

    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(
        text="📤 Поделиться ссылкой",
        url=f"tg://msg_url?url={link}&text=Присоединяйся%20к%20нам!",
    ))
    await msg.answer(
        "💌 Приглашай друзей и получай +5 % к недельной выплате!\n\n"
        f"<code>{link}</code>",
        reply_markup=kb.as_markup(),
    )

# ── Выплаты / TopWeek команды
@dp.message(lambda m: m.text == "🏦 Выплаты")
async def payments_info(msg: types.Message):
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="💸 Перейти в канал выплат", url=PAYMENTS_CHANNEL_LINK))
    await msg.answer(
        "💰 Вся статистика и выплаты публикуются в канале:",
        reply_markup=kb.as_markup(),
    )

# ─────────────────── SCHEDULER JOBS ───────────
scheduler.add_job(update_weekly_lists, CronTrigger(day_of_week="mon", hour=0, minute=0))
update_weekly_lists()   # первичная генерация

# ─────────────────── MAIN ─────────────────────
async def main() -> None:
    logger.info("Starting bot…")
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
