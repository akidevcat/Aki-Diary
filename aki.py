import logging
import accounts
import diary

from datetime import datetime, timedelta

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

COMMON, SCHOOL, LOGIN = range(3)
KREPLY = ['Marks', 'Homework', 'Timetable', 'Choose School']

def start(update, context):
    reply_keyboard = [KREPLY]
    uid = update.message.from_user

    update.message.reply_text(
        'こんにちは! 私はAkiです。'
        '''Do I know you? Let's see...''')
    if uid in accounts.accounts:
    	update.message.reply_text('Come back ^_^', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))
    	return COMMON
    else:
    	update.message.reply_text('Wait, who are you? Please tell me. Type your login and psw like this: Kuristina 1234')
    	return LOGIN


def action_common(update, context):
	if update.message.text == KREPLY[0]:
		return marks(update, context)
	if update.message.text == KREPLY[1]:
		return homework(update, context)
	if update.message.text == KREPLY[2]:
		return timetable(update, context)
	if update.message.text == KREPLY[3]:
		update.message.reply_text('Okay, so now just type the name of your school. Currently I know only 1 school: ',
								  'Lyceum of Kirovo-Chepetsk' + '\n\n',
								  'Type /cancel if you want to leave everything as it is now.')
		return SCHOOL


def action_login(update, context):
	uid = update.message.from_user
	msg = update.message.text.split(' ')
	if len(msg) == 2:
		update.message.reply_text('Got it! Trying to authenticate you, please wait...')
		status, user_full_name, data = diary.login_account(msg[0], msg[1])
		if status:
			accounts.accounts[uid] = data
			update.message.reply_text('Awesome! Now you can ask me anything you want!')
			return COMMON
		else:
			update.message.reply_text('Nah, it doesn\'t work. Please, try again.')
			return LOGIN
	else:
		update.message.reply_text('Wrong format, I need only 2 words: your login and password')
		return LOGIN


def marks(update, context):
	uid = update.message.from_user
	if uid in accounts.accounts:
		status, data = diary.get_student_journal(accounts.accounts[uid])
		if status:
			update.message.reply_text('Here you go:\n' + data)
		else:
			update.message.reply_text('Whoops, something went wrong, try to log in again, I suppose.')
		return COMMON
	else:
		update.message.reply_text('Something went wrong, I can\'t recognise you :( Please, log in again.')
		return LOGIN


def homework(update, context):
	uid = update.message.from_user
	if uid in accounts.accounts:
		now = datetime.today()
		date = now
		day_count = 7
		status, data = diary.get_student_homework(accounts.accounts[uid], day_count, date)
		if status:
			update.message.reply_text('Here you go:\n' + data)
		else:
			update.message.reply_text('Whoops, something went wrong, try to log in again, I suppose')
		return COMMON
	else:
		update.message.reply_text('Something went wrong, I can\'t recognise you :( Please, log in again.')
		return LOGIN


def timetable(update, context):
	print('c')


def action_school(update, context):
	print('d')


def cancel(update, context):
    user = update.message.from_user
    update.message.reply_text('Bye!',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def back(update, context):
	return COMMON


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
	TOKEN = open("token.txt", "r").read()

	updater = Updater(TOKEN, use_context=True)
	dp = updater.dispatcher

	conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            COMMON: [MessageHandler(Filters.text, action_common)],

            SCHOOL: [MessageHandler(Filters.text, action_school), 
            		 CommandHandler('cancel', back)],

            LOGIN: [MessageHandler(Filters.text, action_login)]
        },

        fallbacks=[CommandHandler('bye', cancel)]
    )

	dp.add_handler(conv_handler)
	dp.add_error_handler(error)
	updater.start_polling()
	updater.idle()



if __name__ == '__main__':
    main()