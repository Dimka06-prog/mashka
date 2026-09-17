"""Обработчики сообщений бота."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import EXERCISES, KEYBOARDS
from user_manager import user_manager

logger = logging.getLogger(__name__)


class MessageHandlers:
    """Класс обработчиков сообщений."""
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start."""
        user_id = update.effective_user.id if update.effective_user else update.message.chat_id
        user_manager.reset_user(user_id)
        
        await update.message.reply_text(
            "Formly — ИИ-тренер для домашних тренировок.\n\n"
            "Тренируйся дома. Техника — как с тренером.\n\n"
            "MVP: 4 упражнения, подсказки голосом и разбор фото.\n"
            "Поставь телефон на стул и выбери действие ниже.",
            reply_markup=KEYBOARDS["menu"]
        )
        logger.info(f"User {user_id} started the bot")
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help."""
        await update.message.reply_text(
            "Как пользоваться:\n"
            "1) Тренировка — подсказки во время подхода\n"
            "2) Разбор фото — пришли кадр упражнения\n"
            "3) Отчёт — прогресс за неделю\n"
            "4) Тариф — 7 дней бесплатно, дальше 590 ₽/мес\n\n"
            "Это учебный MVP. Камера в боте имитирует разбор техники.",
            reply_markup=KEYBOARDS["menu"]
        )
    
    @staticmethod
    async def tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик информации о тарифе."""
        await update.message.reply_text(
            "Подписка Formly: 590 ₽ / мес\n"
            "7 дней бесплатно.\n\n"
            "Входит: разбор техники 4 упражнений и голосовые подсказки.\n"
            "Не входит: зал, питание, 200 упражнений.",
            reply_markup=KEYBOARDS["menu"]
        )
    
    @staticmethod
    async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик отчёта за неделю."""
        await update.message.reply_text(
            "Отчёт за неделю\n\n"
            "Тренировки: 3\n"
            "Средняя оценка техники: 78/100\n"
            "Лучше стало: глубина приседа\n"
            "Риск: колени иногда заваливаются внутрь\n\n"
            "Следующая цель: 3 тренировки без округления спины.",
            reply_markup=KEYBOARDS["menu"]
        )
    
    @staticmethod
    async def workout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик выбора тренировки."""
        user_id = update.effective_user.id if update.effective_user else update.message.chat_id
        user_manager.set_user_field(user_id, "state", "pick_workout")
        
        await update.message.reply_text(
            "Какое упражнение разбираем?",
            reply_markup=KEYBOARDS["exercises"]
        )
    
    @staticmethod
    async def photo_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик разбора фото."""
        user_id = update.effective_user.id if update.effective_user else update.message.chat_id
        user_manager.set_user_field(user_id, "state", "pick_photo")
        
        await update.message.reply_text(
            "Выбери упражнение, затем пришли фото сбоку.",
            reply_markup=KEYBOARDS["exercises"]
        )
    
    @staticmethod
    async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик возврата в меню."""
        user_id = update.effective_user.id if update.effective_user else update.message.chat_id
        user_manager.reset_user(user_id)
        
        await update.message.reply_text(
            "Formly — ИИ-тренер для домашних тренировок.\n\n"
            "Тренируйся дома. Техника — как с тренером.\n\n"
            "MVP: 4 упражнения, подсказки голосом и разбор фото.\n"
            "Поставь телефон на стул и выбери действие ниже.",
            reply_markup=KEYBOARDS["menu"]
        )
    
    @staticmethod
    def find_exercise(text: str) -> str:
        """Найти упражнение по тексту."""
        text_lower = (text or "").lower().strip()
        for exercise_key in EXERCISES:
            if exercise_key in text_lower:
                return exercise_key
        return None
    
    @staticmethod
    async def handle_exercise_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик выбора упражнения."""
        user_id = update.effective_user.id if update.effective_user else update.message.chat_id
        text = update.message.text if update.message else ""
        
        exercise_key = MessageHandlers.find_exercise(text)
        if not exercise_key:
            return
        
        state = user_manager.get_user_field(user_id, "state")
        
        if state == "pick_workout":
            user_manager.set_user_field(user_id, "state", "workout")
            user_manager.set_user_field(user_id, "exercise", exercise_key)
            user_manager.set_user_field(user_id, "reps", 0)
            
            exercise = EXERCISES[exercise_key]
            await update.message.reply_text(
                f"{exercise['title']}\n\n{exercise['setup']}\n\n"
                "Сделай повтор и нажми «Сделал повтор». Я дам подсказку, как голос тренера.",
                reply_markup=KEYBOARDS["workout"]
            )
        
        elif state == "pick_photo":
            user_manager.set_user_field(user_id, "state", "wait_photo")
            user_manager.set_user_field(user_id, "exercise", exercise_key)
            
            await update.message.reply_text(
                f"Ок, ждём фото: {EXERCISES[exercise_key]['title']}. Снимай сбоку, в кадре весь корпус."
            )
    
    @staticmethod
    async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик получения фото."""
        user_id = update.effective_user.id if update.effective_user else update.message.chat_id
        
        exercise_key = user_manager.get_user_field(user_id, "exercise", "приседания")
        user_manager.reset_user(user_id)
        
        await update.message.reply_text(
            EXERCISES[exercise_key]["photo"],
            reply_markup=KEYBOARDS["menu"]
        )
    
    @staticmethod
    async def handle_workout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик тренировки."""
        user_id = update.effective_user.id if update.effective_user else update.message.chat_id
        text = update.message.text if update.message else ""
        text_lower = text.lower()
        
        state = user_manager.get_user_field(user_id, "state")
        
        if state != "workout":
            return
        
        if "сделал" in text_lower or "повтор" in text_lower:
            exercise_key = user_manager.get_user_field(user_id, "exercise", "приседания")
            reps = int(user_manager.get_user_field(user_id, "reps", 0)) + 1
            user_manager.set_user_field(user_id, "reps", reps)
            
            exercise = EXERCISES[exercise_key]
            cue = exercise["cues"][(reps - 1) % 4]
            
            await update.message.reply_text(
                f"Повтор {reps}/8\n{cue}",
                reply_markup=KEYBOARDS["workout"]
            )
            
            if reps >= 8:
                user_manager.reset_user(user_id)
                await update.message.reply_text(
                    "Подход закончен.\nОценка техники: 78/100 · риск коленей: средний.\n"
                    "Не заваливай корпус вперёд на следующих 8 повторах.",
                    reply_markup=KEYBOARDS["menu"]
                )
        
        elif "закончить" in text_lower:
            reps = user_manager.get_user_field(user_id, "reps", 0)
            user_manager.reset_user(user_id)
            
            await update.message.reply_text(
                f"Подход закрыт. Повторов: {reps}.\nЧтобы техника росла — 3 таких подхода через день.",
                reply_markup=KEYBOARDS["menu"]
            )
    
    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Главный обработчик текстовых сообщений."""
        text = update.message.text if update.message else ""
        text_lower = text.lower()
        
        # Обработка основных команд
        if text.startswith("/start") or text_lower in {"в меню", "/menu", "меню"}:
            await MessageHandlers.menu(update, context)
        elif text_lower in {"помощь", "/help"}:
            await MessageHandlers.help_command(update, context)
        elif "тариф" in text_lower:
            await MessageHandlers.tariff(update, context)
        elif "отчёт" in text_lower or "отчет" in text_lower:
            await MessageHandlers.report(update, context)
        elif "тренировка" in text_lower:
            await MessageHandlers.workout(update, context)
        elif "разбор" in text_lower or text_lower == "фото":
            await MessageHandlers.photo_analysis(update, context)
        else:
            # Обработка выбора упражнения и тренировки
            await MessageHandlers.handle_exercise_selection(update, context)
            await MessageHandlers.handle_workout(update, context)
            
            # Если ни один обработчик не сработал
            if update.message:
                await update.message.reply_text(
                    "Нажми кнопку меню: тренировка, разбор фото, отчёт или тариф.",
                    reply_markup=KEYBOARDS["menu"]
                )
