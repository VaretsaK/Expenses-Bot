import logging
import pickle

from telegram_token import api_token
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# Setup basic logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
    )

# Global constants and variables
API_TOKEN = api_token
user_data = dict()
file_name: str = 'user_data.pkl'

# States to handle user input
AWAITING_USER_INPUT_INCOME = "Income"
AWAITING_USER_INPUT_EXPENSE = "Expense"
AWAITING_USER_DELETE_RECORD = 1
AWAITING_USER_STAT_PERIOD = 2
AWAITING_USER_REC_PERIOD = 3

# Categories
CAT_1: str = "Car"
CAT_2: str = "Food"
CAT_3: str = "Internet"
CAT_4: str = "Flat"


def open_file() -> None:
    """Open and load the user data file if it exists, or log that it does not."""
    global user_data
    try:
        with open(file_name, 'rb') as file:
            user_data = pickle.load(file)
    except FileNotFoundError:
        logging.info("No file to load data from.")


def save_file() -> None:
    """Save the current state of user data to a file."""
    with open(file_name, 'wb') as file:
        pickle.dump(user_data, file)


class Record:
    """A class representing a financial record."""
    def __init__(self, value: int, category: str, title: str) -> None:
        """Initialize the Record with value, category, title, and timestamp."""
        self.value = value
        self.title = title
        self.category = category
        self.datetime = datetime.now()

    def __str__(self) -> str:
        """Return string representation of the Record."""
        return f"{self.title} | {self.datetime.strftime("%Y-%m-%d %H:%M:%S")} | {self.category} : {self.value}"


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a menu of inline buttons for the user to interact with."""
    logging.info("Command menu was triggered.")

    keyboard = [
        [InlineKeyboardButton("Add income", callback_data="add_income")],
        [InlineKeyboardButton("Add expense", callback_data="add_expense")],
        [InlineKeyboardButton("List records", callback_data="list_records")],
        [InlineKeyboardButton("Delete record", callback_data="delete_record")],
        [InlineKeyboardButton("Statistics", callback_data="statistics")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please choose:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses from the inline keyboard."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data

    # Display options for listing records
    if callback_data == "list_records":
        # When "List records" is pressed, offer additional options
        keyboard = [
            [InlineKeyboardButton("All time", callback_data="all_time_rec")],
            [InlineKeyboardButton("Category", callback_data="category_rec")],
            [InlineKeyboardButton("Period", callback_data="period_rec_input")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Choose an option for records:", reply_markup=reply_markup)

    # Show all records unconditionally
    elif callback_data == "all_time_rec":
        # When "All time" under "List records" is pressed, display all records
        if not user_data.get(user_id):
            await query.edit_message_text("You don't have any records.")
        else:
            result = "\n".join([f"{i + 1}. {record}" for i, record in enumerate(user_data[user_id])])
            await query.edit_message_text(f"Your records:\n{result}")

    # Show records by category
    elif callback_data == "category_rec":
        # When "Category" under "List records" is pressed, display category options
        keyboard = [
            [InlineKeyboardButton(f"{CAT_1}", callback_data=f"cat_rec:{CAT_1}")],
            [InlineKeyboardButton(f"{CAT_4}", callback_data=f"cat_rec:{CAT_4}")],
            [InlineKeyboardButton(f"{CAT_3}", callback_data=f"cat_rec:{CAT_3}")],
            [InlineKeyboardButton(f"{CAT_2}", callback_data=f"cat_rec:{CAT_2}")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Choose a category:", reply_markup=reply_markup)

    # Show statistics
    elif callback_data == "statistics":
        # When "Statistics" is pressed, offer additional options
        keyboard = [
            [InlineKeyboardButton("All time", callback_data="all_time_stat")],
            [InlineKeyboardButton("Category", callback_data="category_stat")],
            [InlineKeyboardButton("Period", callback_data="period_stat_input")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Choose an option for statistics:", reply_markup=reply_markup)

    # Show all-time statistics
    elif callback_data == "all_time_stat":
        # When "All time" under "Statistics" is pressed, calculate and show statistics
        if not user_data.get(user_id):
            await query.edit_message_text("You don't have any records.")
        else:
            income = sum([record.value for record in user_data[user_id] if record.title == "Income"])
            expenses = sum([record.value for record in user_data[user_id] if record.title == "Expense"])
            await query.edit_message_text(f"Your all time income: {income} \nYour all time expenses: {expenses}")

    # Show category-specific statistics
    elif callback_data == "category_stat":
        # When a specific category under "Statistics" is pressed, show statistics for that category
        keyboard = [
            [InlineKeyboardButton(f"{CAT_1}", callback_data=f"cat_stat:{CAT_1}")],
            [InlineKeyboardButton(f"{CAT_4}", callback_data=f"cat_stat:{CAT_4}")],
            [InlineKeyboardButton(f"{CAT_3}", callback_data=f"cat_stat:{CAT_3}")],
            [InlineKeyboardButton(f"{CAT_2}", callback_data=f"cat_stat:{CAT_2}")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Choose a category:", reply_markup=reply_markup)

    elif "cat_rec" in callback_data:
        # When chosen to list records of a specific category.
        category = query.data.replace('cat_rec:', '')

        if not user_data.get(user_id):
            await query.edit_message_text("You don't have any records.")
        else:
            result = "\n".join([f"{record}" for record in user_data[user_id]
                                if record.category == category])
            await query.edit_message_text(f"Your records in {category} category:\n{result}")

    elif "cat_stat" in callback_data:
        # When chosen to view statistics for a specific category.
        category = query.data.replace('cat_stat:', '')

        if not user_data.get(user_id):
            await query.edit_message_text("You don't have any records.")
        else:
            expenses = sum([record.value for record in user_data[user_id] if record.category == category])
            await query.edit_message_text(f"Your all time expenses in {category} category: {expenses}")

    # Input for records over a period
    elif callback_data == "period_rec_input":
        # When "Period" under "List records" is pressed, prompt for input
        await query.edit_message_text(text="Please enter amount of days:")
        context.user_data['state'] = AWAITING_USER_REC_PERIOD

    # Input for statistics over a period
    elif callback_data == "period_stat_input":
        # When "Period" under "Statistics" is pressed, prompt for input
        await query.edit_message_text(text="Please enter amount of days:")
        context.user_data['state'] = AWAITING_USER_STAT_PERIOD

    # Delete a record
    elif callback_data == "delete_record":
        # When "Delete record" is pressed, show records to choose which to delete
        if not user_data.get(user_id):
            await query.edit_message_text("You don't have any records.")
        else:
            result = "\n".join([f"{i + 1}. {record}" for i, record in enumerate(user_data[user_id])])
            await query.edit_message_text(f"Type record number to delete:\n{result}")
            context.user_data['state'] = AWAITING_USER_DELETE_RECORD

    # Add an income record
    elif callback_data == "add_income":
        # When "Add income" is pressed, offer category options
        keyboard = [
            [InlineKeyboardButton("Office work", callback_data="input_income:Office work")],
            [InlineKeyboardButton("Side hustle", callback_data="input_income:Side hustle")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Choose a category:", reply_markup=reply_markup)

    # Add an expense record
    elif callback_data == "add_expense":
        # When "Add expense" is pressed, offer category options
        keyboard = [
            [InlineKeyboardButton(f"{CAT_1}", callback_data=f"input_expense:{CAT_1}")],
            [InlineKeyboardButton(f"{CAT_4}", callback_data=f"input_expense:{CAT_4}")],
            [InlineKeyboardButton(f"{CAT_3}", callback_data=f"input_expense:{CAT_3}")],
            [InlineKeyboardButton(f"{CAT_2}", callback_data=f"input_expense:{CAT_2}")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Choose a category:", reply_markup=reply_markup)

    elif "input_income" in callback_data:
        # When chosen to add an income record and needs to input the value.
        # Prompt the user to enter their income amount.
        await query.edit_message_text(text="Please enter your income:")
        context.user_data['awaiting_input_for'] = query.data
        context.user_data['state'] = AWAITING_USER_INPUT_INCOME

    elif "input_expense" in callback_data:
        # When chosen to add an expense record and needs to input the value.
        # Prompt the user to enter their expense amount.
        await query.edit_message_text(text="Please enter your expense:")
        context.user_data['awaiting_input_for'] = query.data
        context.user_data['state'] = AWAITING_USER_INPUT_EXPENSE

    # Return to main menu
    elif callback_data == "back_to_main":
        # When "Back to Main Menu" is pressed, display the main menu
        keyboard = [
            [InlineKeyboardButton("Add income", callback_data="add_income")],
            [InlineKeyboardButton("Add expense", callback_data="add_expense")],
            [InlineKeyboardButton("List records", callback_data="list_records")],
            [InlineKeyboardButton("Delete record", callback_data="delete_record")],
            [InlineKeyboardButton("Statistics", callback_data="statistics")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text="Please choose:", reply_markup=reply_markup)


async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle additional user input after button presses requiring it."""
    user_id = update.message.from_user.id
    user_state = context.user_data.get('state')
    current_date = datetime.now()

    # Validate and convert user input to integer
    try:
        user_input = int(update.message.text)
    except ValueError:
        await update.message.reply_text(f"Incorrect input. Try again.")
        return

    # If awaiting income, process and store it
    if user_state == AWAITING_USER_INPUT_INCOME:
        # When in state AWAITING_USER_INPUT_INCOME, process income
        if not user_data.get(user_id):
            user_data[user_id] = []

        category = context.user_data.get('awaiting_input_for').replace('input_income:', '')

        record = Record(user_input, category, user_state)
        user_data[user_id].append(record)

        await update.message.reply_text(f"Received your income in category '{category}': {user_input}")

        context.user_data['state'] = None
        context.user_data.pop('awaiting_input_for', None)

    # If awaiting expense, validate against balance, process, and store it
    elif user_state == AWAITING_USER_INPUT_EXPENSE:
        # When in state AWAITING_USER_INPUT_EXPENSE, check balance and process expense
        income = sum([record.value for record in user_data[user_id] if record.title == "Income"])
        expenses = sum([record.value for record in user_data[user_id] if record.title == "Expense"])

        if user_input > (income - expenses):
            await update.message.reply_text(f"Not enough money. Cut your expenses.")
            return

        category = context.user_data.get('awaiting_input_for').replace('input_expense:', '')

        record = Record(user_input, category, user_state)
        user_data[user_id].append(record)

        await update.message.reply_text(f"Received your expense in '{category}': {user_input}")

        context.user_data['state'] = None
        context.user_data.pop('awaiting_input_for', None)

    # If awaiting to delete a record, process deletion
    elif user_state == AWAITING_USER_DELETE_RECORD:
        # When in state AWAITING_USER_DELETE_RECORD, process record deletion
        deleted_record = user_data[user_id].pop(user_input - 1)

        await update.message.reply_text(f"Record: {deleted_record}\nWas deleted.")

        context.user_data['state'] = None

    # If awaiting statistics for a specific period, process and display it
    elif user_state == AWAITING_USER_STAT_PERIOD:
        # When in state AWAITING_USER_STAT_PERIOD, calculate and show statistics for the period
        income = sum([record.value for record in user_data[user_id] if record.title == "Income"
                      and record.datetime >= (current_date - timedelta(days=user_input))])
        expenses = sum([record.value for record in user_data[user_id] if record.title == "Expense"
                        and record.datetime >= (current_date - timedelta(days=user_input))])

        await update.message.reply_text(f"Your income for the last {user_input} day(s): {income} "
                                        f"\nYour expenses for the last {user_input} day(s):  {expenses}")

        context.user_data['state'] = None

    # If awaiting records for a specific period, process and display it
    elif user_state == AWAITING_USER_REC_PERIOD:
        # When in state AWAITING_USER_REC_PERIOD, show records for the period
        result = "\n".join([f"{record}" for record in user_data[user_id]
                            if record.datetime >= (current_date - timedelta(days=user_input))])
        await update.message.reply_text(f"Your records for the last {user_input} day(s):\n{result}")

        context.user_data['state'] = None

    # After processing, always save the updated user data
    save_file()


def main() -> None:
    """Main function to set up and run the Telegram bot."""
    # Load user data from file on startup
    open_file()

    # Create the Application with the bot token
    application = Application.builder().token(API_TOKEN).build()

    # Register command and message handlers
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    # Start polling for updates
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
