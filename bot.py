import os
from dotenv import load_dotenv
import discord
from discord import option
import asyncio

# Load the Discord token from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise SystemExit("DISCORD_TOKEN not set in .env")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("ANNOUNCEMENT_CHANNEL_ID", "0"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))  # seconds between checks

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Helper function to check if user is admin
def is_admin(ctx):
    if not ctx.author.guild_permissions.administrator:
        return False
    return True

# keep track of the last processed message
last_message_id = None

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    bot.loop.create_task(monitor_announcements())  # start background task

async def monitor_announcements():
    """Continuously checks the announcement channel for new messages and DMs the sender."""
    global last_message_id

    await bot.wait_until_ready()  # make sure bot is fully started
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)

    if not channel:
        print("❌ Announcement channel not found! Check ANNOUNCEMENT_CHANNEL_ID.")
        return

    print(f"🔍 Monitoring #{channel.name} every {CHECK_INTERVAL} seconds...")

    while not bot.is_closed():
        try:
            # get the latest message in the channel
            async for msg in channel.history(limit=1):
                latest_msg = msg
                break
            else:
                await asyncio.sleep(CHECK_INTERVAL)
                continue  # no messages yet

            # if we haven't seen this message before and it's not from the bot itself
            if last_message_id != latest_msg.id and latest_msg.author != bot.user:
                last_message_id = latest_msg.id
                print(f"📨 New announcement by {latest_msg.author}: {latest_msg.content!r}")

                # Prepare the DM with the announcement inside triple backticks for easy copy
                dm_text = (
                    "hi there Don't forget to send this message in the WhatsApp group!\n\n"
                    "Here it is :P\n"
                    "```\n"
                    f"{latest_msg.content}\n"
                    "```"
                )

                # try to DM the user
                try:
                    await latest_msg.author.send(dm_text)
                    print(f"✅ Sent DM to {latest_msg.author} (ID: {latest_msg.author.id})")
                except discord.Forbidden:
                    print(f"⚠️ Can't DM {latest_msg.author} (DMs disabled or privacy settings).")

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"⚠️ Error in monitor_announcements: {e}")
            await asyncio.sleep(CHECK_INTERVAL)

# Post a message to a channel through the bot
@bot.slash_command(guild_ids=[DISCORD_GUILD_ID], description="Post a message to a channel")
@option("channel", description="Channel to post in", required=True, channel_types=[discord.ChannelType.text])
@option("message", description="Message to post", required=True)
@option("mention_everyone", description="Include @everyone mention", required=False)
async def post_message(
    ctx,
    channel: discord.TextChannel,
    message: str,
    mention_everyone: bool = False
):
    # Admin permission check
    if not is_admin(ctx):
        await ctx.respond("❌ This command is restricted to server administrators.", ephemeral=True)
        return
        
    try:
        # Check if bot has permission to send in the target channel
        perms = channel.permissions_for(ctx.guild.me)
        if not perms.send_messages:
            await ctx.respond(f"❌ I don't have permission to send messages in {channel.mention}", ephemeral=True)
            return
            
        if mention_everyone and not perms.mention_everyone:
            await ctx.respond(f"⚠️ I don't have permission to mention everyone in {channel.mention}", ephemeral=True)
            # Continue anyway, just without the mention
        
        # Format the message with @everyone if requested and permitted
        content = message
        if mention_everyone and perms.mention_everyone:
            content = f"@everyone\n{content}"
        
        # Send the message to the target channel
        await channel.send(content)
        
        # Confirm to the command user
        await ctx.respond(f"✅ Message posted in {channel.mention}", ephemeral=True)
        
    except Exception as e:
        await ctx.respond(f"❌ Error: {str(e)}", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)