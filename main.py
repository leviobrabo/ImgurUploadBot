import telebot
import pyimgur
import logging
import os
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberUpdated


from pymongo import MongoClient

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TELEGRAM_BOT_TOKEN = '7856110659:AAGlLzlZEzq1CRMfN0gSA6c1RBhiwWZOuP4'
IMGUR_CLIENT_IDS = [
    '52ba35ee0e3c4ad',  # Primeiro CLIENT_ID
    '1cc96860f56a466',  # Segundo CLIENT_ID
    '3d160bdbec22287',  # Terceiro CLIENT_ID
    '17009f6715a5b76',
    '41400761c15a7b5'
]

MONGO_CON = 'mongodb+srv://starvoisx:levi123@cluster0.tec213s.mongodb.net/?retryWrites=true&w=majority'
CHANNEL = '@lbrabo' 
GROUP_LOG = '-1001962261893'
BOT_OWNER_ID = '5307669416'



current_client_id_index = 0



# banco de dados

# Função para verificar se o usuário está no canal
def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Erro ao verificar membro no canal: {e}")
        return False
    
client = MongoClient(MONGO_CON)
db = client['imgur_bot']


def search_user(user_id):
    return db.users.find_one({'user_id': user_id})

def get_all_users(query=None):
        """
        Retorna todos os usuários do banco de dados.
        Se query for fornecida, será usada para filtrar os resultados.
        """
        return list(db.users.find({}))

def add_user_db(message):
    first_name = message.from_user.first_name
    last_name = str(message.from_user.last_name).replace('None', '')
    username = str(message.from_user.username).replace("None", "")
    
    db.users.insert_one(
        {
            'user_id': message.from_user.id,
            'name': f'{first_name} {last_name}',
            'username': username,
            'banned': 'false',
            'channel_part': 'false',
            'sudo': 'false',
            'lang': 'en-us',
        }
    )

def search_group(chat_id):
        return db.chats.find_one({'chat_id': chat_id})

def add_chat_db(chat_id, chat_name):
        return db.chats.insert_one({
            'chat_id': chat_id,
            'chat_name': chat_name,
            'blocked': 'false',
            'thread_id': '',
            'lang': 'en-us',
        })

def get_all_chats(query=None):
        if query:
            return db.chats.find(query)
        else:
            return db.chats.find({})
        
def remove_chat_db(chat_id):
    db.chats.delete_one({"chat_id": chat_id})

# Função para buscar o idioma do chat
def get_group_lang(chat_id):
    user = db.chats.find_one({'chat_id': chat_id})
    return user['lang'] if user else 'en-us'

def set_group_language(chat_id, lang):
    db.chats.update_one({'chat_id': chat_id}, {'$set': {'lang': lang}})

def update_group_lang(chat_id, lang):
    db.users.update_one({'chat_id': chat_id}, {'$set': {'lang': lang}})

# Função para buscar o idioma do usuário
def get_user_lang(user_id):
    user = db.users.find_one({'user_id': user_id})
    return user['lang'] if user else 'en-us'

def update_user_lang(user_id, lang):
    db.users.update_one({'user_id': user_id}, {'$set': {'lang': lang}})

# Função para definir o idioma no banco
def set_user_language(user_id, lang):
    db.users.update_one({'user_id': user_id}, {'$set': {'lang': lang}})

def get_next_client_id():
    global current_client_id_index
    client_id = IMGUR_CLIENT_IDS[current_client_id_index]
    current_client_id_index = (current_client_id_index + 1) % len(IMGUR_CLIENT_IDS)
    return client_id

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client_id = get_next_client_id()
im = pyimgur.Imgur(client_id)

def send_new_group_message(chat):
    try:
        chatusername = f"@{chat.username}" if chat.username else "Private Group"
        bot.send_message(
            GROUP_LOG,
            text=f"#{bot.get_me().username} #New_Group\n"
            f"<b>Chat:</b> {chat.title}\n"
            f"<b>ID:</b> <code>{chat.id}</code>\n"
            f"<b>Link:</b> {chatusername}",
            parse_mode="html",
            disable_web_page_preview=True,
            message_thread_id=45925,
        )
    except Exception as e:
        logging.error(f"Erro ao adicionador grupo no banco de dados: {e}")

@bot.my_chat_member_handler()
def send_group_greeting(message: ChatMemberUpdated):
    try:
        old_member = message.old_chat_member
        new_member = message.new_chat_member
        if message.chat.type != "private" and new_member.status in [
            "member",
            "administrator",
        ]:
            chat_id = message.chat.id
            chat_name = message.chat.title

            if chat_id in [CHANNEL, GROUP_LOG]:
                logging.warning(
                    f"Ignorando armazenamento de chat com ID {chat_id}, pois corresponde a um ID configurado."
                )
                return

            existing_chat = search_group(chat_id)
            if existing_chat:
                logging.warning(
                    f"O bate-papo com ID {chat_id} já existe no banco de dados."
                )
                return

            add_chat_db(chat_id, chat_name)
            logging.info(
                f"⭐️ O bot foi adicionado no grupo {chat_name} - ({chat_id})"
            )

            send_new_group_message(message.chat)

            try:
                chat_member = bot.get_chat_member(chat_id, bot.get_me().id)

                if message.chat.type in ["group", "supergroup", "channel"]:
                        lang = get_group_lang(message.chat.id)
                        if lang == 'en-us':
                            text_chat = f"Hello! Thanks for adding me to your group.\n\nI will send you an Imgur link every time you send me an image."
                            text_chat_btn_1 = 'Official Channel'
                            text_chat_btn_2 = 'Report bugs'
                        if lang == 'pt-br':
                            text_chat = f"Olá! Obrigado por me adicionar em seu grupo.\n\nEu enviarei link do Imgur toda vez que você me enviar uma imagem"
                            text_chat_btn_1 = 'Canal Oficial'
                            text_chat_btn_2 = 'Relatar bugs'
                        markup = InlineKeyboardMarkup()
                        channel_ofc = InlineKeyboardButton(
                            text_chat_btn_1, url="https://t.me/lbrabo"
                        )
                        report_bugs = InlineKeyboardButton(
                            text_chat_btn_2, url="https://t.me/kylorensbot"
                        )
                        markup.add(channel_ofc, report_bugs)


                        bot.send_message(
                            chat_id,
                            text_chat,
                            reply_markup=markup,
                            parse_mode="HTML",
                            message_thread_id=message.message_thread_id
                        )

                
            except Exception as e:
                logging.error(f"Erro ao lidar com saudação de grupo: {e}")

    except Exception as e:
        logging.error(f"Erro ao envias boas vindas no grupo: {e}")

@bot.message_handler(content_types=["left_chat_member"])
def on_left_chat_member(message):
    try:
        if message.left_chat_member.id == bot.get_me().id:
            chat_id = message.chat.id
            chat_name = message.chat.title
            remove_chat_db(chat_id)
            logging.info(f"O bot foi removido do grupo {chat_name} - ({chat_id})")
    except Exception as e:
        logging.error(f"Erro ao remover grupo do banco de dados: {e}")

# Mensagem inicial explicativa sobre o bot
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_chat_action(message.chat.id, 'typing')
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    user = search_user(user_id)

    if not user:
        add_user_db(message)
        user = search_user(user_id)
        user_info = (
                f"<b>#{bot.get_me().username} #New_User</b>\n"
                f"<b>User:</b> {user['name']}\n"
                f"<b>ID:</b> <code>{user['user_id']}</code>\n"
                f"<b>Username:</b> @{user.get('username', 'Sem Username')}"
            )
        bot.send_message(GROUP_LOG, user_info, message_thread_id=45925)
        logging.info(f'Novo usuário ID: {user["user_id"]} foi criado no banco de dados')
    else:
        pass

    if message.chat.type == "private":
        lang = get_user_lang(message.from_user.id)
    else:
        lang = get_group_lang(message.chat.id)

    text = f"👋 Hello, {first_name}! I'm a bot that helps upload images to Imgur. Send me a photo, and I'll provide you a link to access it."
    if lang == 'pt-br':
        text = f"👋 Olá, {first_name}! Eu sou um bot que ajuda a fazer upload de imagens para o Imgur. Envie uma foto, e eu retornarei um link direto para acessá-la."
    bot.send_message(message.chat.id, text, message_thread_id=message.message_thread_id)

# Detecta qualquer foto enviada pelo usuário e faz o upload automaticamente
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if message.chat.type == "private":
        user_lang = get_user_lang(message.from_user.id)
    else:
        user_lang = get_group_lang(message.chat.id)
    
    if not is_user_in_channel(message.from_user.id):
        # Envia mensagem com botão para o canal
        if user_lang == 'pt-br':
            text = "⚠️ Você não está no canal! Por favor, entre no canal para continuar."
        else:
            text = "⚠️ You are not in the channel! Please join the channel to continue."
        
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{CHANNEL[1:]}")
        keyboard.add(button)
        bot.send_message(message.chat.id, text, reply_markup=keyboard, message_thread_id=message.message_thread_id)
        return

    try:
        # Envia uma mensagem de status inicial
        if user_lang == 'pt-br':
            text_1 = "🔄 Recebendo imagem do usuário..."
        else:
            text_1 = "🔄 Receiving image from user..."
        status_message = bot.send_message(message.chat.id, text_1, message_thread_id=message.message_thread_id)

        # Baixa a imagem do usuário
        logging.info("Recebendo imagem do usuário...")
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Define o caminho para salvar a imagem temporariamente
        image_path = os.path.join(os.getcwd(), f"{file_info.file_id}.jpg")
        logging.info(f"Salvando imagem temporariamente em {image_path}")

        # Salva a imagem temporariamente
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Atualiza a mensagem de status
        if user_lang == 'pt-br':
            text_2 = "⏳ Fazendo upload da imagem para o Imgur, um momento..."
        else:
            text_2 = "⏳ Uploading the image to Imgur, one moment..."

        bot.edit_message_text(chat_id=message.chat.id, message_id=status_message.message_id, text=text_2)

        # Faz o upload para o Imgur
        logging.info("Fazendo upload da imagem para o Imgur...")
        uploaded_image = im.upload_image(image_path, title=f"Uploaded by {message.from_user.username}")

        # Atualiza a mensagem com o link da imagem

        if user_lang == 'pt-br':
            text_3 = ( f"✅ Imagem enviada com sucesso!\n\n<code>{uploaded_image.link}</code>\n\n"
                 f"Caso queira acessar, clique aqui: <a href='{uploaded_image.link}'>Clique aqui</a>", )
        else:
            text_3 = (f"✅ Image sent successfully!\n\n<code>{uploaded_image.link}</code>\n\n"
                    f"If you want to access, click here: <a href='{uploaded_image.link}'>Click here</a>",)

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message.message_id,
            text=text_3,
            parse_mode='HTML'  # Necessário para que o HTML seja renderizado corretamente
        )

        logging.info(f"Imagem enviada com sucesso! Link: {uploaded_image.link}")

        # Remove a imagem temporária
        if os.path.exists(image_path):
            os.remove(image_path)
            logging.info(f"Imagem temporária removida: {image_path}")

    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}")
        if user_lang == 'pt-br':
            text_4 = "❌ Houve um erro ao processar sua imagem. Tente novamente."
        else:
            text_4 = "❌ There was an error processing your image. Please try again."
        bot.reply_to(message, text_4, message_thread_id=message.message_thread_id)

# Comando para alterar o idioma
@bot.message_handler(commands=['lang'])
def change_language(message):
    user_id = message.from_user.id
    if message.chat.type == "private":
        lang = get_user_lang(message.from_user.id)
        
        if lang == 'pt-br':
            lang = 'en-us'
        else:
            lang = 'pt-br'

        set_user_language(message.from_user.id, lang)

    # Verifica se o comando foi enviado por um admin em grupo
    else:
        chat_id = message.chat.id
        chat_true = search_group(chat_id)
        if chat_true:
            lang = get_group_lang(chat_id)
            chat_member = bot.get_chat_member(chat_id, user_id)
            if chat_member.status not in ("administrator", "creator"):
                if lang == 'pt-br':
                    text_adm = "❌ Você não tem permissão para alterar o idioma!"
                else:
                    text_adm = "❌ You do not have permission to change the language!"
                bot.send_message(message.chat.id, text_adm, message_thread_id=message.message_thread_id)
                return
            
            if lang == 'pt-br':
                lang = 'en-us'
            else:
                lang = 'pt-br'

            set_group_language(message.chat.id, lang)

    # Envia confirmação
    if lang == 'pt-br':
        text_lang = "🌍 Idioma alterado para Português (Brasil)."
    else:
        text_lang = "🌍 Language changed to English (US)."
    
    bot.send_message(message.chat.id, text_lang, message_thread_id=message.message_thread_id)

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
        try:
            if message.from_user.id == BOT_OWNER_ID:
                count_users = len(list(get_all_users()))
                count_groups = len(list(get_all_chats()))
                user_stats = f' ☆ {count_users} usuários\n ☆ {count_groups} Grupos'
                bot.reply_to(message, f'\n──❑ 「 Bot Stats 」 ❑──\n\n{user_stats}')
        except Exception as e:
            logging.error(f'Erro ao enviar o stats do bot: {e}')
# Inicia o bot
logging.info("Iniciando o bot...")
bot.infinity_polling()