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

# Load environment variables основной канал
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('WELCOME_BOT_TOKEN')
ADMIN_ID = int(os.getenv('MY_ID'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Important links
MAIN_CHANNEL_LINK = "https://t.me/CryptoBusinessTeamChannel"
PAYMENTS_CHANNEL_LINK = "https://t.me/CryptoBusinessPayments"
CHILL_MANOFF_LINK = "https://t.me/Chill_manoff"
WHAT_WE_DO_LINK = "https://telegra.ph/Nashe-napravlenie-05-22"
ELECTRUM_SETUP_LINK = "https://telegra.ph/Ustanovka-i-nastrojka-Electrum-05-23"
CANCEL_TX_LINK = "https://telegra.ph/OTMENA-BTC-TRANZAKCII-05-31"
MANAGER_GUIDE_LINK = "https://telegra.ph/INSTRUKCIYA-DLYA-MENEDZHERA--PERVICHNAYA-OBRABOTKA-ZAYAVKI-05-24"

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# User data storage
user_data = {}


# Define states for application process
class Application(StatesGroup):
    waiting_for_name = State()
    waiting_for_experience = State()
    waiting_for_hours = State()
    waiting_for_wallet = State()


# Define ranks and progression
RANKS = {
    "Фрешмен": 0,
    "Грайндер": 2000,
    "Ветеран": 5000,
    "Элита": 10000,
    "Легенда": 20000
}

# Sample data for leaderboards
TEAM_LEADERS = ["Девятый", "wa3rix", "Professor", "Djenga", "Псих", "Fenix", "Akatsuki"]

TOP_TEAMS = [
    {"name": "Fenix", "amount": 5383, "profits": 11},
    {"name": "Professor", "amount": 5287, "profits": 8},
    {"name": "Djenga", "amount": 4460, "profits": 9},
    {"name": "Девятый", "amount": 3940, "profits": 9},
]

TOP_WORKERS = [
    {"name": "Наташка", "amount": 1700, "profits": 3},
    {"name": "angerfist", "amount": 1601, "profits": 2},
    {"name": "Хорек", "amount": 1494, "profits": 3},
]


# Helper functions
def get_user_data(user_id):
    """Initialize or retrieve user data"""
    if user_id not in user_data:
        user_data[user_id] = {
            'wallets': [],
            'last_generation': None,
            'total_profit': 0,
            'weekly_profit': 0,
            'referrals': 0
        }
    return user_data[user_id]


def generate_wallets():
    """Generate new wallet addresses"""
    wallets = []
    for i in range(3):
        eth_address = '0x' + ''.join(random.choices('0123456789abcdef', k=40))
        trx_address = 'T' + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=33))
        wallets.append({
            'eth': eth_address,
            'trx': trx_address,
            'created': dt.datetime.now().strftime("%d.%m.%Y")
        })
    return wallets


def get_next_rank(current_amount):
    """Determine user's rank and progress"""
    current_rank = "Фрешмен"
    next_rank = "Грайндер"
    needed = RANKS["Грайндер"]

    for rank, amount in RANKS.items():
        if current_amount >= amount:
            current_rank = rank

    # Find next rank
    ranks = list(RANKS.keys())
    try:
        current_index = ranks.index(current_rank)
        if current_index < len(ranks) - 1:
            next_rank = ranks[current_index + 1]
            needed = RANKS[next_rank] - current_amount
    except ValueError:
        pass

    return current_rank, next_rank, needed


# Create main menu keyboard
def get_main_menu_kb():
    builder = ReplyKeyboardBuilder()

    # First row
    builder.row(
        types.KeyboardButton(text="Мануалы")
    )


    # Third row
    builder.row(
        types.KeyboardButton(text="🧬 Мои кошельки"),
    )

    # Fourth row
    builder.row(
        types.KeyboardButton(text="📈 Моя статистика"),
        types.KeyboardButton(text="🔝 Топ недели")
    )

    # Fifth row
    builder.row(
        types.KeyboardButton(text="🔝 Команды"),
        types.KeyboardButton(text="💌 Канал")
    )

    # Sixth row
    builder.row(
        types.KeyboardButton(text="🤝 Инвайт"),
        types.KeyboardButton(text="🏦 Выплаты")
    )

    return builder.as_markup(resize_keyboard=True)


# Command handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    # Create inline keyboard with application button
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="✅ Подать заявку",
        callback_data="apply_from_start"
    ))

    welcome_text = (
        "🖼 <b>ДОБРО ПОЖАЛОВАТЬ!</b>\n\n"
        "Ты находишься в нужном месте и в нужное время. Ознакомься с правилами проекта прежде, чем подать заявку.\n\n"
        "⛔ Размещение 18+ медиа любого формата – БАН\n"
        "⛔ Реклама других проектов/услуг без согласования с администрацией – БАН\n"
        "⛔ Попрошайничество – мут на сутки\n"
        "⛔ Срачи на политические темы – БАН моментально\n"
        "⛔ Саботировать/подставлять/провоцировать других участников – БАН\n"
        "⛔ Прием платежей на свои кошельки – БАН\n\n"
        "Подтверждая заявку, ты соглашаешься с правилами ✍️"
    )

    await message.answer(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )
    await message.answer(
        "🔹 Выберите действие в меню:",
        reply_markup=get_main_menu_kb()
    )


# Application button handler from start message
@dp.callback_query(lambda c: c.data == "apply_from_start")
async def apply_from_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Application.waiting_for_name)
    await callback.message.answer("1. Укажи свое имя и возраст:")
    await callback.answer()


# Application process handlers
@dp.message(lambda message: message.text == "Подать заявку")
async def process_application_start(message: types.Message, state: FSMContext):
    await state.set_state(Application.waiting_for_name)
    await message.answer("1. Укажи свое имя и возраст:")


@dp.message(Application.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name_age=message.text)
    await state.set_state(Application.waiting_for_experience)
    await message.answer("2. Был ли опыт работы на звонках/чатах? (Если был, подробно опишите)")


@dp.message(Application.waiting_for_experience)
async def process_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await state.set_state(Application.waiting_for_hours)
    await message.answer("3. Сколько времени готовы уделять работе?")


@dp.message(Application.waiting_for_hours)
async def process_hours(message: types.Message, state: FSMContext):
    await state.update_data(hours=message.text)
    await state.set_state(Application.waiting_for_wallet)
    await message.answer("4. Адрес кошелька с BTC для работы:")


@dp.message(Application.waiting_for_wallet)
async def process_wallet(message: types.Message, state: FSMContext):
    await state.update_data(btc_wallet=message.text)
    data = await state.get_data()

    application_text = (
        "📄 <b>Новая анкета</b>\n\n"
        f"👤 <b>Имя и возраст:</b> {data['name_age']}\n"
        f"💼 <b>Опыт работы:</b> {data['experience']}\n"
        f"⏱ <b>Часы работы:</b> {data['hours']}\n"
        f"💰 <b>BTC кошелёк:</b> {data['btc_wallet']}\n"
        f"🆔 <b>ID пользователя:</b> {message.from_user.id}"
    )
    try:
        await bot.send_message(ADMIN_ID, application_text, parse_mode=ParseMode.HTML)
        logger.info("Application sent to admin from user %s", message.from_user.id)
    except Exception as e:
        logger.error("Error sending application: %s", e)

    # ✅ підтвердження для користувача
    await message.answer(
        "✅ <b>Твоя анкета отправлена на рассмотрение.</b>\n"
        "Скоро с тобой свяжется администратор @Chill_manoff",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_kb()
    )

    # 📢 посилання на канали
    links = InlineKeyboardBuilder()
    links.row(
        types.InlineKeyboardButton(text="📢 Основной канал", url=MAIN_CHANNEL_LINK),
        types.InlineKeyboardButton(text="💸 Канал выплат",  url=PAYMENTS_CHANNEL_LINK)
    )
    await message.answer(
        "Чтобы не пропустить новости и выплаты, подпишись на наши каналы:",
        reply_markup=links.as_markup()
    )

    await state.clear()



# Menu option handlers чем занимаемся
@dp.message(lambda message: message.text == "Мануалы")
async def show_manuals(message: types.Message):
    manuals_text = (
        "📚 <b>Основные мануалы проекта</b>\n\n"
        "Выберите нужный мануал из списка ниже:"
    )

    # Create inline keyboard with manual links
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="Чем занимаемся",
            url=WHAT_WE_DO_LINK
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Настройка Electrum",
            url=ELECTRUM_SETUP_LINK
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Отмена BTC транзакций",
            url=CANCEL_TX_LINK
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Инструкция для менеджера",
            url=MANAGER_GUIDE_LINK
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="👤 Личка администратора",
            url=CHILL_MANOFF_LINK
        )
    )

    await message.answer(
        manuals_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text == "Статистика TL")
async def show_tl_stats(message: types.Message):
    user = get_user_data(message.from_user.id)

    # Check if user is a team leader
    if message.from_user.username in TEAM_LEADERS or user.get('is_team_leader', False):
        stats_text = (
            "📊 <b>Ваша статистика как Team Leader</b>\n\n"
            f"👥 Участников в команде: 12\n"
            f"💸 Общий профит команды: 3940$\n"
            f"🏆 Ваша доля: 394$\n"
            f"⭐️ Рейтинг команды: 4 место"
        )
    else:
        stats_text = (
            "📈 <b>Статистика TL</b>\n"
            "Вы не являетесь тимлидером ни одной команды.\n\n"
            "Чтобы стать тимлидером, проявите активность и обратитесь к @Chill_manoff"
        )

    await message.answer(stats_text, parse_mode=ParseMode.HTML)

    work_text = (
        "🔹 <b>Основные направления деятельности</b>\n\n"
        "• Настройка Electrum для безопасных транзакций\n"
        "• Отмена BTC транзакций с использованием RBF\n"
        "• Обучение менеджеров для работы с клиентами\n\n"
        "Для получения подробной информации нажмите кнопку ниже:"
    )

    await message.answer(
        work_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text == "🧬 Мои кошельки")
async def show_my_wallets(message: types.Message):
    user = get_user_data(message.from_user.id)

    if not user['wallets']:
        # Create inline button to generate wallets
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="🔐 Сгенерировать ключи",
            callback_data="generate_wallets"
        ))

        await message.answer(
            "⚠️ У вас пока нет сгенерированных кошельков.",
            reply_markup=builder.as_markup()
        )
        return

    wallets_text = "🔑 <b>Ваши кошельки для пополнений</b>\n\n"

    for i, wallet in enumerate(user['wallets'], 1):
        wallets_text += (
            f"<b>Связка #{i}</b> (создана {wallet['created']})\n"
            f"• ETH: <code>{wallet['eth']}</code>\n"
            f"• TRX: <code>{wallet['trx']}</code>\n\n"
        )

    wallets_text += (
        "ℹ️ <i>Ethereum адреса работают для всех EVM-сетей "
        "(Ethereum, BSC, Polygon, Avalanche, Arbitrum, Optimism)</i>"
    )

    await message.answer(wallets_text, parse_mode=ParseMode.HTML)


# Wallet generation handler
@dp.callback_query(lambda c: c.data == "generate_wallets")
async def generate_keys_callback(callback: types.CallbackQuery):
    user = get_user_data(callback.from_user.id)
    current_time = time.time()

    # Check if user can generate new wallets
    if user['last_generation'] and (current_time - user['last_generation']) < 24 * 3600:
        remaining = 24 * 3600 - (current_time - user['last_generation'])
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await callback.message.answer(
            f"⚠️ Вы уже генерировали ключи сегодня.\n"
            f"Следующая генерация будет доступна через {hours}ч {minutes}м."
        )
        await callback.answer()
        return

    # Generate new wallets
    user['wallets'] = generate_wallets()
    user['last_generation'] = current_time

    wallets_text = "🎉 <b>Новые кошельки сгенерированы!</b>\n\n"

    for i, wallet in enumerate(user['wallets'], 1):
        wallets_text += (
            f"<b>Связка #{i}</b>\n"
            f"• ERC20: <code>{wallet['eth']}</code>\n"
            f"• TRC20: <code>{wallet['trx']}</code>\n\n"
        )

    wallets_text += (
        "‼️ <b>ВАЖНО:</b>\n"
        "Используйте только эти адреса для получения платежей в нашей команде."
    )

    await callback.message.answer(wallets_text, parse_mode=ParseMode.HTML)
    await callback.answer()


@dp.message(lambda message: message.text == "📈 Моя статистика")
async def show_my_stats(message: types.Message):
    user = get_user_data(message.from_user.id)
    current_rank, next_rank, needed = get_next_rank(user['total_profit'])

    stats_text = (
        "📊 <b>Ваша статистика</b>\n\n"
        f"💵 Профит за все время: <b>{user['total_profit']}$</b>\n"
        f"📅 Профит за неделю: <b>{user['weekly_profit']}$</b>\n"
        f"🏅 Текущий ранг: <b>{current_rank}</b>\n\n"
        f"📈 До звания <b>{next_rank}</b> осталось: <b>{needed}$</b>\n"
        f"💸 Недельная выплата: <b>{user['weekly_profit'] * 0.35}$</b>"
    )

    await message.answer(stats_text, parse_mode=ParseMode.HTML)


@dp.message(lambda message: message.text == "🔝 Топ недели")
async def show_top_week(message: types.Message):
    top_text = "🏆 <b>Топ воркеров недели:</b>\n\n"

    for i, worker in enumerate(TOP_WORKERS, 1):
        top_text += (
            f"{i}. <b>{worker['name']}</b>, Total: {worker['amount']}$ | "
            f"профитов: {worker['profits']}\n"
        )

    top_text += "\n🔹 <b>История выплат:</b> " + PAYMENTS_CHANNEL_LINK

    await message.answer(top_text, parse_mode=ParseMode.HTML)


@dp.message(lambda message: message.text == "🔝 Команды")
async def show_top_teams(message: types.Message):
    teams_text = "🏆 <b>Топ команд за неделю:</b>\n\n"

    for i, team in enumerate(TOP_TEAMS, 1):
        teams_text += (
            f"{i}. <b>{team['name']}</b> - {team['amount']}$ "
            f"(профитов: {team['profits']})\n"
        )

    teams_text += "\n🔹 <b>Основной канал:</b> " + MAIN_CHANNEL_LINK

    await message.answer(teams_text, parse_mode=ParseMode.HTML)


@dp.message(lambda message: message.text == "💌 Канал")
async def show_channel_info(message: types.Message):
    # Create inline buttons for channels
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="📢 Основной канал",
            url=MAIN_CHANNEL_LINK
        ),
        types.InlineKeyboardButton(
            text="💸 Канал выплат",
            url=PAYMENTS_CHANNEL_LINK
        )
    )

    channel_text = (
        "📢 <b>Наши официальные каналы</b>\n\n"
        "Подпишитесь, чтобы быть в курсе всех обновлений и новостей проекта.\n\n"
        "На случай удаления основного канала, резервным будет канал выплат."
    )

    await message.answer(
        channel_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text == "🤝 Инвайт")
async def generate_invite(message: types.Message):
    bot_username = (await bot.me()).username
    ref_code = message.from_user.username or str(message.from_user.id)
    invite_link = f"https://t.me/{bot_username}?start={ref_code}"

    invite_text = (
        "🤝 <b>Пригласите друзей и получайте бонусы!</b>\n\n"
        f"Ваша реферальная ссылка:\n<code>{invite_link}</code>\n\n"
        "За каждого активного реферала вы получаете +5% к недельной выплате!"
    )

    # Create inline button for quick sharing
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="📤 Поделиться ссылкой",
        url=f"tg://msg_url?url={invite_link}&text=Присоединяйся%20к%20нашей%20команде!"
    ))

    await message.answer(
        invite_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text == "🏦 Выплаты")
async def show_payments_info(message: types.Message):
    # Create inline button for payments channel
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="💸 Перейти в канал выплат",
        url=PAYMENTS_CHANNEL_LINK
    ))

    payments_text = (
        "💰 <b>Информация о выплатах</b>\n\n"
        "Все профиты публикуются в нашем канале выплат.\n\n"
        "<b>Статистика за неделю:</b>\n"
        "• Топ воркеров: /topweek\n"
        "• Топ команд: /topweekteam\n\n"
        "Выплаты происходят каждый понедельник автоматически на ваши кошельки."
    )

    await message.answer(
        payments_text,
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )


# Main function
async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
