"""Module that implements a price bot that reports the exchange rates of different currencies"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import filters, MessageHandler, ApplicationBuilder, \
ContextTypes, CommandHandler, InlineQueryHandler

from fiat import CurrencyRates

load_dotenv()

c = CurrencyRates()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    print(update)

    intro_text = """I'm a price bot. You can ask me for the exchange rate of a currency
    (e.g. /price USD) or a currency pair (e.g. /pair TWD USD)"""

    await context.bot.send_message(chat_id=update.effective_chat.id, \
                                   text=intro_text)

async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE):

    base_cur = context.args[0]
    dest_cur = context.args[1]

    rate = c.get_rate(base_cur, dest_cur)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{base_cur}/{dest_cur}: {rate}")

async def base(update: Update, context: ContextTypes.DEFAULT_TYPE):

    base_cur = context.args[0]

    rates = c.get_rates(base_cur)

    selected_symbols = ['TWD', 'CNY', 'EUR', 'USD', 'JPY', 'GBP', 'KRW']

    response = f"Exchange Rates for {base_cur}\n----------------\n"

    for symbol, rate in rates.items():
        if symbol in selected_symbols:
            response += f"{symbol}: {rate}\n"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

if __name__ == '__main__':

    TOKEN = os.getenv('TOKEN')
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    pair_handler = CommandHandler('pair', pair)
    base_handler = CommandHandler('base', base)

    application.add_handler(start_handler)
    application.add_handler(pair_handler)
    application.add_handler(base_handler)

    application.run_polling()
