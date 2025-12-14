import asyncio
import random
import os
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError

# ===== CONFIGURATION =====
API_ID = 39496551  # यहाँ अपना API ID डालें
API_HASH = "36495414098630fed4555734bcc9748b"  # यहाँ अपना API HASH डालें
SESSION_NAME = "raid_bot_session"
ADMIN_ID = 8556525515  # यहाँ अपना Telegram User ID डालें

# स्पीड सेटिंग्स (सेकंड में डिले)
SPEED_PROFILES = {
    "slow": {"min": 10.0, "max": 15.0},
    "medium": {"min": 5.0, "max": 8.0},
    "fast": {"min": 2.0, "max": 4.0},
    "ultra": {"min": 0.5, "max": 1.5},
    "instant": {"min": 0.1, "max": 0.3}
}

# ===== RAID SYSTEM =====
class RaidSystem:
    def __init__(self):
        self.active_raids = {}  # user_id: task
        self.message_packs = {}  # pack_name: [messages]
        self.default_messages = []
        self.load_messages()
        self.load_packs()
    
    def load_messages(self, filename="messages.txt"):
        """डिफॉल्ट मैसेज TXT फाइल से लोड करें"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    self.default_messages = [line.strip() for line in f if line.strip()]
            else:
                self.default_messages = [
                    "नमस्ते! यह ऑटो मैसेज है।",
                    "टेस्ट मैसेज 1",
                    "टेस्ट मैसेज 2"
                ]
                self.save_messages(filename)
        except Exception as e:
            print(f"Error loading messages: {e}")
            self.default_messages = ["Error loading messages!"]
    
    def save_messages(self, filename="messages.txt"):
        """मैसेज TXT फाइल में सेव करें"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for msg in self.default_messages:
                    f.write(msg + "\n")
        except Exception as e:
            print(f"Error saving messages: {e}")
    
    def load_packs(self, folder="message_packs"):
        """सभी मैसेज पैक्स लोड करें"""
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
                return
            
            for filename in os.listdir(folder):
                if filename.endswith('.txt'):
                    pack_name = filename[:-4]  # .txt हटाएं
                    filepath = os.path.join(folder, filename)
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        messages = [line.strip() for line in f if line.strip()]
                        self.message_packs[pack_name] = messages
                        
        except Exception as e:
            print(f"Error loading packs: {e}")
    
    def get_pack_names(self):
        """सभी पैक के नाम लौटाएं"""
        return list(self.message_packs.keys())

# Initialize raid system
raid_system = RaidSystem()

# ===== TELEGRAM CLIENT =====
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ===== RAID FUNCTION =====
async def start_raid(target_user, message_source, speed_profile="medium", count=None):
    """
    रेड शुरू करें
    
    Parameters:
    - target_user: User ID या username
    - message_source: 'default' या pack name
    - speed_profile: 'slow', 'medium', 'fast', 'ultra', 'instant'
    - count: कितने मैसेज भेजने हैं (None = unlimited)
    """
    
    # मैसेज सोर्स चुनें
    if message_source == "default":
        messages = raid_system.default_messages
    elif message_source in raid_system.message_packs:
        messages = raid_system.message_packs[message_source]
    else:
        messages = raid_system.default_messages
    
    if not messages:
        return "❌ कोई मैसेज नहीं मिले!"
    
    # स्पीड प्रोफाइल सेट करें
    if speed_profile not in SPEED_PROFILES:
        speed_profile = "medium"
    
    speed_config = SPEED_PROFILES[speed_profile]
    
    # रेड टास्क
    async def raid_task():
        sent_count = 0
        
        try:
            # अनलिमिटेड रेड
            if count is None:
                while True:
                    # रैंडम मैसेज चुनें
                    message = random.choice(messages)
                    
                    # मैसेज भेजें
                    try:
                        await client.send_message(target_user, message)
                        sent_count += 1
                        
                        # डिले
                        delay = random.uniform(speed_config["min"], speed_config["max"])
                        await asyncio.sleep(delay)
                        
                    except FloodWaitError as e:
                        print(f"Flood wait: {e.seconds} seconds")
                        await asyncio.sleep(e.seconds + 5)
                    
                    except UserPrivacyRestrictedError:
                        print("User has privacy restrictions")
                        break
                    
                    except Exception as e:
                        print(f"Error sending message: {e}")
                        await asyncio.sleep(5)
            
            # लिमिटेड रेड
            else:
                for i in range(min(count, len(messages) * 3)):
                    message = random.choice(messages)
                    
                    try:
                        await client.send_message(target_user, message)
                        sent_count += 1
                        
                        if i < count - 1:
                            delay = random.uniform(speed_config["min"], speed_config["max"])
                            await asyncio.sleep(delay)
                            
                    except FloodWaitError as e:
                        print(f"Flood wait: {e.seconds} seconds")
                        await asyncio.sleep(e.seconds + 5)
                    
                    except UserPrivacyRestrictedError:
                        print("User has privacy restrictions")
                        break
                    
                    except Exception as e:
                        print(f"Error sending message: {e}")
                        await asyncio.sleep(5)
        
        except asyncio.CancelledError:
            print(f"Raid cancelled for {target_user}")
        
        finally:
            # Clean up
            if target_user in raid_system.active_raids:
                del raid_system.active_raids[target_user]
    
    # टास्क स्टार्ट करें
    task = asyncio.create_task(raid_task())
    raid_system.active_raids[target_user] = task
    
    return f"🔥 रेड शुरू!\nTarget: {target_user}\nSpeed: {speed_profile}\nMessages: {len(messages)}"

# ===== COMMAND HANDLERS =====
@client.on(events.NewMessage(pattern=r'\.raid'))
async def raid_command_handler(event):
    """रेड कमांड हैंडलर"""
    if event.sender_id != ADMIN_ID:
        await event.reply("🚫 केवल एडमिन!")
        return
    
    # कमांड पार्स करें
    args = event.message.text.split()
    
    if len(args) < 2:
        help_text = """
<b>🔥 RAID COMMAND HELP</b>

<u>Basic Usage:</u>
<code>.raid @username</code> - Default messages, medium speed
<code>.raid 123456789</code> - User ID से रेड

<u>With Speed:</u>
<code>.raid @username fast</code>
<code>.raid @username ultra</code>
<code>.raid @username instant</code>

<u>With Message Pack:</u>
<code>.raid @username pack:packname</code>
<code>.raid @username fast pack:packname</code>

<u>With Count:</u>
<code>.raid @username count:50</code>
<code>.raid @username fast count:100 pack:packname</code>

<u>Speed Options:</u>
slow (10-15s), medium (5-8s), fast (2-4s), ultra (0.5-1.5s), instant (0.1-0.3s)

<u>Other Commands:</u>
<code>.stopraid @username</code> - रेड रोकें
<code>.stopall</code> - सभी रेड रोकें
<code>.listraids</code> - एक्टिव रेड लिस्ट
<code>.packs</code> - मैसेज पैक्स दिखाएं
<code>.stats</code> - स्टेटस दिखाएं
<code>.addmsg [text]</code> - नया मैसेज जोड़ें
        """
        await event.reply(help_text, parse_mode='html')
        return
    
    # पैरामीटर्स पार्स करें
    target = args[1]
    speed = "medium"
    pack = "default"
    count = None
    
    for arg in args[2:]:
        if arg in SPEED_PROFILES:
            speed = arg
        elif arg.startswith("pack:"):
            pack = arg[5:]
        elif arg.startswith("count:"):
            try:
                count = int(arg[6:])
            except:
                count = None
    
    # टार्गेट पार्स करें
    try:
        if target.isdigit():
            target_user = int(target)
        elif target.startswith('@'):
            # Username से user ID निकालें
            try:
                user = await client.get_entity(target)
                target_user = user.id
            except:
                await event.reply(f"❌ User नहीं मिला: {target}")
                return
        else:
            await event.reply("❌ अमान्य target!")
            return
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
        return
    
    # रेड शुरू करें
    result = await start_raid(target_user, pack, speed, count)
    await event.reply(result)

@client.on(events.NewMessage(pattern=r'\.stopraid'))
async def stop_raid_handler(event):
    """किसी एक रेड को रोकें"""
    if event.sender_id != ADMIN_ID:
        return
    
    args = event.message.text.split()
    if len(args) < 2:
        await event.reply("Usage: .stopraid @username")
        return
    
    target = args[1]
    
    # टार्गेट ढूंढें
    target_user = None
    for user_id in raid_system.active_raids:
        if str(user_id) == target or (target.startswith('@') and str(user_id) == target[1:]):
            target_user = user_id
            break
    
    if target_user and target_user in raid_system.active_raids:
        raid_system.active_raids[target_user].cancel()
        del raid_system.active_raids[target_user]
        await event.reply(f"⏹️ रेड रोका गया: {target}")
    else:
        await event.reply(f"❌ कोई एक्टिव रेड नहीं मिला: {target}")

@client.on(events.NewMessage(pattern=r'\.stopall'))
async def stop_all_handler(event):
    """सभी रेड रोकें"""
    if event.sender_id != ADMIN_ID:
        return
    
    if not raid_system.active_raids:
        await event.reply("ℹ️ कोई एक्टिव रेड नहीं चल रहे।")
        return
    
    count = len(raid_system.active_raids)
    for task in raid_system.active_raids.values():
        task.cancel()
    
    raid_system.active_raids.clear()
    await event.reply(f"🛑 सभी {count} रेड रोके गए!")

@client.on(events.NewMessage(pattern=r'\.listraids'))
async def list_raids_handler(event):
    """एक्टिव रेड लिस्ट"""
    if event.sender_id != ADMIN_ID:
        return
    
    if not raid_system.active_raids:
        await event.reply("📭 कोई एक्टिव रेड नहीं चल रहे।")
        return
    
    raids_list = []
    for user_id in raid_system.active_raids.keys():
        raids_list.append(f"• User ID: {user_id}")
    
    response = f"<b>🔥 एक्टिव रेड ({len(raids_list)}):</b>\n\n" + "\n".join(raids_list)
    await event.reply(response, parse_mode='html')

@client.on(events.NewMessage(pattern=r'\.packs'))
async def list_packs_handler(event):
    """मैसेज पैक्स दिखाएं"""
    if event.sender_id != ADMIN_ID:
        return
    
    packs = raid_system.get_pack_names()
    
    if not packs:
        await event.reply("📭 कोई मैसेज पैक नहीं मिले।")
        return
    
    packs_list = []
    for i, pack_name in enumerate(packs, 1):
        msg_count = len(raid_system.message_packs[pack_name])
        packs_list.append(f"{i}. {pack_name} ({msg_count} messages)")
    
    response = f"<b>📦 मैसेज पैक्स ({len(packs)}):</b>\n\n" + "\n".join(packs_list)
    await event.reply(response, parse_mode='html')

@client.on(events.NewMessage(pattern=r'\.addmsg'))
async def add_message_handler(event):
    """नया मैसेज जोड़ें"""
    if event.sender_id != ADMIN_ID:
        return
    
    message_text = event.message.text.replace('.addmsg ', '', 1).strip()
    
    if message_text:
        raid_system.default_messages.append(message_text)
        raid_system.save_messages()
        await event.reply(f"✅ मैसेज जोड़ा!\nकुल: {len(raid_system.default_messages)}")
    else:
        await event.reply("Usage: .addmsg [message text]")

@client.on(events.NewMessage(pattern=r'\.stats'))
async def stats_handler(event):
    """स्टेटस दिखाएं"""
    if event.sender_id != ADMIN_ID:
        return
    
    stats_text = f"""
<b>📊 RAID BOT STATS</b>

<u>System:</u>
• Active Raids: {len(raid_system.active_raids)}
• Default Messages: {len(raid_system.default_messages)}
• Message Packs: {len(raid_system.message_packs)}

<u>Speed Profiles:</u>
• Slow: {SPEED_PROFILES['slow']['min']}-{SPEED_PROFILES['slow']['max']}s
• Medium: {SPEED_PROFILES['medium']['min']}-{SPEED_PROFILES['medium']['max']}s
• Fast: {SPEED_PROFILES['fast']['min']}-{SPEED_PROFILES['fast']['max']}s
• Ultra: {SPEED_PROFILES['ultra']['min']}-{SPEED_PROFILES['ultra']['max']}s
• Instant: {SPEED_PROFILES['instant']['min']}-{SPEED_PROFILES['instant']['max']}s

<u>Storage:</u>
• Session: {SESSION_NAME}
• Admin: {ADMIN_ID}
• Time: {datetime.now().strftime('%H:%M:%S')}
    """
    await event.reply(stats_text, parse_mode='html')

# ===== MAIN FUNCTION =====
async def main():
    """मेन फंक्शन"""
    print("🔥 TELEGRAM RAID BOT")
    print("=" * 50)
    print(f"API ID: {API_ID}")
    print(f"Session: {SESSION_NAME}")
    print(f"Admin: {ADMIN_ID}")
    print("=" * 50)
    
    # Create necessary folders
    os.makedirs("message_packs", exist_ok=True)
    
    try:
        # Connect to Telegram
        await client.start()
        me = await client.get_me()
        
        print(f"Logged in as: {me.first_name} (@{me.username})")
        print(f"User ID: {me.id}")
        print("=" * 50)
        print("Bot is ready!")
        print("Available commands:")
        print(".raid [target] [speed] [pack:name] [count:number]")
        print(".stopraid [target]")
        print(".stopall")
        print(".packs")
        print(".stats")
        print(".addmsg [message]")
        print("=" * 50)
        
        # Run until disconnected
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"Error: {e}")

# ===== START BOT =====
if __name__ == "__main__":
    # Create default messages.txt if not exists
    if not os.path.exists("messages.txt"):
        with open("messages.txt", "w", encoding="utf-8") as f:
            f.write("नमस्ते! यह डिफॉल्ट मैसेज है।\n")
            f.write("टेस्ट मैसेज 1\n")
            f.write("टेस्ट मैसेज 2\n")
        print("Created default messages.txt")
    
    # Run the bot
    asyncio.run(main())
