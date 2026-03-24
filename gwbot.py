import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime
import json
import os
from typing import Optional

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration - REPLACE WITH YOUR ACTUAL VALUES
OWNER_ID = 1312961127851884578  # Your Discord User ID
GW_CHANNEL_ID = 1417796009282768916  # Your giveaway channel ID
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'  # Replace with your actual bot token

# File to store giveaway data persistently
DATA_FILE = 'giveaways.json'

# Store giveaway data
active_giveaways = {}

# Load saved giveaways
def load_giveaways():
    global active_giveaways
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                for g_id, giveaway in data.items():
                    giveaway['participants'] = [int(uid) for uid in giveaway['participants']]
                    giveaway['id'] = int(giveaway['id'])
                active_giveaways = {int(k): v for k, v in data.items()}
        except:
            active_giveaways = {}

# Save giveaways to file
def save_giveaways():
    with open(DATA_FILE, 'w') as f:
        data = {}
        for g_id, giveaway in active_giveaways.items():
            data[str(g_id)] = {
                **giveaway,
                'participants': [str(uid) for uid in giveaway['participants']]
            }
        json.dump(data, f, indent=4)

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
    
    @discord.ui.button(label="🎉 Enter Giveaway", style=discord.ButtonStyle.primary, custom_id="enter_giveaway")
    async def enter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        if self.giveaway_id not in active_giveaways:
            await interaction.response.send_message("❌ This giveaway has ended!", ephemeral=True)
            return
        
        giveaway = active_giveaways[self.giveaway_id]
        
        if user_id in giveaway['participants']:
            await interaction.response.send_message("⚠️ You're already entered in this giveaway!", ephemeral=True)
        else:
            giveaway['participants'].append(user_id)
            save_giveaways()
            await interaction.response.send_message("✅ You've successfully entered the giveaway!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} has connected to Discord!')
    print(f'📊 Bot ID: {bot.user.id}')
    print(f'👑 Owner ID: {OWNER_ID}')
    print(f'📢 Giveaway Channel: {GW_CHANNEL_ID}')
    load_giveaways()
    print(f'🎁 Loaded {len(active_giveaways)} active giveaways')
    
    # Register the persistent view for all giveaways
    for giveaway_id in active_giveaways:
        bot.add_view(GiveawayView(giveaway_id))
    
    # Restart timers for giveaways
    for giveaway_id, giveaway in active_giveaways.items():
        remaining = giveaway['end_time'] - datetime.utcnow().timestamp()
        if remaining > 0:
            asyncio.create_task(end_giveaway_delayed(giveaway_id, remaining))
        else:
            asyncio.create_task(end_giveaway(giveaway_id))
    
    print('🎉 Bot is ready to use!')

async def end_giveaway_delayed(giveaway_id, delay):
    await asyncio.sleep(delay)
    await end_giveaway(giveaway_id)

@bot.command(name='setupgw')
@commands.has_permissions(administrator=True)
async def setup_giveaway(ctx, duration: str, winner_count: int, image_url: Optional[str] = None, *, prize: str):
    """Setup a new giveaway with optional image"""
    
    if ctx.channel.id != GW_CHANNEL_ID:
        await ctx.send(f"❌ Please use this command in <#{GW_CHANNEL_ID}>", delete_after=5)
        await ctx.message.delete()
        return
    
    # Parse duration
    time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    unit = duration[-1]
    try:
        time_value = int(duration[:-1])
        total_seconds = time_value * time_units[unit]
    except:
        await ctx.send("❌ Invalid duration format! Use format like: 10s, 5m, 2h, 1d", delete_after=5)
        await ctx.message.delete()
        return
    
    # Create giveaway ID
    giveaway_id = len(active_giveaways) + 1
    
    # Create embed
    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉",
        description=f"**Prize:** {prize}\n**Winners:** {winner_count}\n**Hosted by:** {ctx.author.mention}\n\nClick the button below to enter!",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    
    end_time = datetime.utcnow().timestamp() + total_seconds
    embed.add_field(name="⏰ Ends in:", value=f"<t:{int(end_time)}:R>", inline=False)
    embed.set_footer(text=f"Giveaway ID: {giveaway_id}")
    
    # Add image if provided and valid
    if image_url and (image_url.startswith('http://') or image_url.startswith('https://')):
        embed.set_image(url=image_url)
        actual_prize = prize
    else:
        # If no image was provided, the first argument might be part of the prize
        if image_url and not (image_url.startswith('http://') or image_url.startswith('https://')):
            actual_prize = f"{image_url} {prize}"
        else:
            actual_prize = prize
    
    # Store giveaway data
    active_giveaways[giveaway_id] = {
        'id': giveaway_id,
        'prize': actual_prize,
        'winner_count': winner_count,
        'host': ctx.author.id,
        'participants': [],
        'end_time': end_time,
        'channel_id': ctx.channel.id,
        'message_id': None,
        'image_url': image_url if image_url and (image_url.startswith('http://') or image_url.startswith('https://')) else None
    }
    
    save_giveaways()
    
    # Send the giveaway message
    view = GiveawayView(giveaway_id)
    message = await ctx.send(embed=embed, view=view)
    active_giveaways[giveaway_id]['message_id'] = message.id
    save_giveaways()
    
    # Delete the command message
    await ctx.message.delete()
    
    # Send confirmation
    confirm_msg = await ctx.send(f"✅ Giveaway #{giveaway_id} setup successfully! Ends in {duration}", delete_after=5)
    
    # Wait for giveaway to end
    await asyncio.sleep(total_seconds)
    await end_giveaway(giveaway_id)

async def end_giveaway(giveaway_id):
    """End the giveaway and announce winners"""
    if giveaway_id not in active_giveaways:
        return
    
    giveaway = active_giveaways[giveaway_id]
    
    # Get the channel and message
    channel = bot.get_channel(giveaway['channel_id'])
    if not channel:
        del active_giveaways[giveaway_id]
        save_giveaways()
        return
    
    try:
        message = await channel.fetch_message(giveaway['message_id'])
    except:
        # Message might have been deleted
        del active_giveaways[giveaway_id]
        save_giveaways()
        return
    
    # Update embed to show giveaway ended
    embed = discord.Embed(
        title="🎉 GIVEAWAY ENDED 🎉",
        description=f"**Prize:** {giveaway['prize']}\n**Winners:** {giveaway['winner_count']}\n**Hosted by:** <@{giveaway['host']}>",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    
    if giveaway.get('image_url'):
        embed.set_image(url=giveaway['image_url'])
    
    # Select winners
    participants = giveaway['participants']
    winner_count = min(giveaway['winner_count'], len(participants))
    
    if participants and winner_count > 0:
        winners = random.sample(participants, winner_count)
        winner_mentions = [f"<@{winner}>" for winner in winners]
        
        winners_text = "\n".join(winner_mentions)
        embed.add_field(name="🏆 Winners:", value=winners_text, inline=False)
        embed.add_field(name="Total Participants:", value=str(len(participants)), inline=True)
        
        # Announce winners
        await message.edit(embed=embed, view=None)
        
        # Create winner announcement
        winner_embed = discord.Embed(
            title="🎉 GIVEAWAY WINNERS ANNOUNCED! 🎉",
            description=f"**Prize:** {giveaway['prize']}\n**Winners:** {', '.join(winner_mentions)}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        if giveaway.get('image_url'):
            winner_embed.set_image(url=giveaway['image_url'])
        
        await channel.send(embed=winner_embed)
        
        # DM the winners
        for winner_id in winners:
            try:
                winner = await bot.fetch_user(winner_id)
                dm_embed = discord.Embed(
                    title="🎉 Congratulations! You won a giveaway! 🎉",
                    description=f"You won: **{giveaway['prize']}**\nHosted by: <@{giveaway['host']}>",
                    color=discord.Color.gold()
                )
                await winner.send(embed=dm_embed)
            except:
                pass
    else:
        embed.add_field(name="❌ No winners:", value="Not enough participants", inline=False)
        await message.edit(embed=embed, view=None)
    
    # Remove from active giveaways
    del active_giveaways[giveaway_id]
    save_giveaways()

@bot.command(name='gw')
@commands.is_owner()
async def private_giveaway_command(ctx, *, args=None):
    """Private command - only you can see and use this"""
    if ctx.author.id != OWNER_ID:
        return
    
    # ONLY delete the command if it's the "pick" subcommand
    if args and args.split()[0].lower() == "pick":
        try:
            await ctx.message.delete()
        except:
            pass
    
    if not args:
        help_text = """**🎮 Giveaway Management System** 🎮
        
**📋 Basic Commands:**
`!gw list` - List all active giveaways
`!gw pick <id> [count]` - Manually pick winners (ONLY this command auto-deletes)
`!gw end <id>` - Force end a giveaway
`!gw status <id>` - Show giveaway status

**👥 Participant Management:**
`!gw add <id> @user` - Add a user to giveaway
`!gw remove <id> @user` - Remove a user from giveaway
`!gw participants <id>` - Show all participants

**📊 Statistics:**
`!gw stats` - Show overall giveaway statistics
`!gw export <id>` - Export participant list

**🔒 Note:** Only `!gw pick` command auto-deletes for privacy!
**📝 Examples:**
`!gw list` - Stays visible
`!gw pick 1 3` - Auto-deletes after picking winners
`!gw end 2` - Stays visible
`!gw add 1 @User` - Stays visible"""
        
        # Send ephemeral message (only visible to you)
        await ctx.send(help_text, ephemeral=True)
        return
    
    args_list = args.split()
    subcommand = args_list[0].lower()
    
    # List active giveaways
    if subcommand == "list":
        if not active_giveaways:
            await ctx.send("📭 No active giveaways.", ephemeral=True)
            return
        
        embed = discord.Embed(title="📊 Active Giveaways", color=discord.Color.blue())
        for g_id, giveaway in active_giveaways.items():
            remaining = int(giveaway['end_time'] - datetime.utcnow().timestamp())
            if remaining > 0:
                embed.add_field(
                    name=f"🎁 Giveaway #{g_id}",
                    value=f"**Prize:** {giveaway['prize']}\n**Winners:** {giveaway['winner_count']}\n**Participants:** {len(giveaway['participants'])}\n**Ends:** <t:{int(giveaway['end_time'])}:R>",
                    inline=False
                )
        
        await ctx.send(embed=embed, ephemeral=True)
    
    # Pick winners manually - THIS IS THE ONLY COMMAND THAT AUTO-DELETES
    elif subcommand == "pick":
        try:
            giveaway_id = int(args_list[1])
            winner_count = int(args_list[2]) if len(args_list) > 2 else None
            
            if giveaway_id not in active_giveaways:
                await ctx.send("❌ Giveaway not found!", ephemeral=True)
                return
            
            giveaway = active_giveaways[giveaway_id]
            
            if winner_count is None:
                winner_count = giveaway['winner_count']
            
            participants = giveaway['participants']
            
            if not participants:
                await ctx.send("❌ No participants in this giveaway!", ephemeral=True)
                return
            
            winner_count = min(winner_count, len(participants))
            winners = random.sample(participants, winner_count)
            winner_mentions = [f"<@{winner}>" for winner in winners]
            
            # Get the giveaway message
            channel = bot.get_channel(giveaway['channel_id'])
            message = await channel.fetch_message(giveaway['message_id'])
            
            # Update embed with winners
            embed = discord.Embed(
                title="🎉 GIVEAWAY WINNERS (Manual Pick) 🎉",
                description=f"**Prize:** {giveaway['prize']}\n**Winners:** {', '.join(winner_mentions)}\n\n**Picked by:** {ctx.author.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            if giveaway.get('image_url'):
                embed.set_image(url=giveaway['image_url'])
            
            embed.add_field(name="Total Participants:", value=str(len(participants)), inline=True)
            
            await message.edit(embed=embed, view=None)
            
            # Announce winners
            winner_embed = discord.Embed(
                title="🎉 GIVEAWAY WINNERS ANNOUNCED! 🎉",
                description=f"**Prize:** {giveaway['prize']}\n**Winners:** {', '.join(winner_mentions)}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            if giveaway.get('image_url'):
                winner_embed.set_image(url=giveaway['image_url'])
            
            await channel.send(embed=winner_embed)
            
            # DM winners
            for winner_id in winners:
                try:
                    winner = await bot.fetch_user(winner_id)
                    dm_embed = discord.Embed(
                        title="🎉 Congratulations! You won a giveaway! 🎉",
                        description=f"You won: **{giveaway['prize']}**\nHosted by: <@{giveaway['host']}>",
                        color=discord.Color.gold()
                    )
                    await winner.send(embed=dm_embed)
                except:
                    pass
            
            # Remove from active giveaways
            del active_giveaways[giveaway_id]
            save_giveaways()
            
            # Send confirmation
            await ctx.send(f"✅ Winners picked and announced for giveaway #{giveaway_id}!\nWinners: {', '.join(winner_mentions)}", ephemeral=True)
            
        except (IndexError, ValueError):
            await ctx.send("❌ Usage: `!gw pick <giveaway_id> [winner_count]`", ephemeral=True)
    
    # Force end giveaway
    elif subcommand == "end":
        try:
            giveaway_id = int(args_list[1])
            
            if giveaway_id not in active_giveaways:
                await ctx.send("❌ Giveaway not found!", ephemeral=True)
                return
            
            await end_giveaway(giveaway_id)
            await ctx.send(f"✅ Giveaway #{giveaway_id} has been ended!", ephemeral=True)
            
        except (IndexError, ValueError):
            await ctx.send("❌ Usage: `!gw end <giveaway_id>`", ephemeral=True)
    
    # Add participant
    elif subcommand == "add":
        try:
            giveaway_id = int(args_list[1])
            user_mention = args_list[2]
            user_id = int(user_mention.replace('<@', '').replace('>', '').replace('!', ''))
            
            if giveaway_id not in active_giveaways:
                await ctx.send("❌ Giveaway not found!", ephemeral=True)
                return
            
            giveaway = active_giveaways[giveaway_id]
            
            if user_id in giveaway['participants']:
                await ctx.send("⚠️ User is already in the giveaway!", ephemeral=True)
            else:
                giveaway['participants'].append(user_id)
                save_giveaways()
                await ctx.send(f"✅ Added <@{user_id}> to giveaway #{giveaway_id}!", ephemeral=True)
                
        except (IndexError, ValueError):
            await ctx.send("❌ Usage: `!gw add <giveaway_id> @user`", ephemeral=True)
    
    # Remove participant
    elif subcommand == "remove":
        try:
            giveaway_id = int(args_list[1])
            user_mention = args_list[2]
            user_id = int(user_mention.replace('<@', '').replace('>', '').replace('!', ''))
            
            if giveaway_id not in active_giveaways:
                await ctx.send("❌ Giveaway not found!", ephemeral=True)
                return
            
            giveaway = active_giveaways[giveaway_id]
            
            if user_id in giveaway['participants']:
                giveaway['participants'].remove(user_id)
                save_giveaways()
                await ctx.send(f"✅ Removed <@{user_id}> from giveaway #{giveaway_id}!", ephemeral=True)
            else:
                await ctx.send("❌ User not found in this giveaway!", ephemeral=True)
                
        except (IndexError, ValueError):
            await ctx.send("❌ Usage: `!gw remove <giveaway_id> @user`", ephemeral=True)
    
    # Show participants
    elif subcommand == "participants":
        try:
            giveaway_id = int(args_list[1])
            
            if giveaway_id not in active_giveaways:
                await ctx.send("❌ Giveaway not found!", ephemeral=True)
                return
            
            giveaway = active_giveaways[giveaway_id]
            participants = giveaway['participants']
            
            if not participants:
                await ctx.send("📭 No participants in this giveaway!", ephemeral=True)
                return
            
            # Create a paginated response if there are many participants
            participants_list = [f"{i+1}. <@{uid}>" for i, uid in enumerate(participants)]
            chunks = [participants_list[i:i+20] for i in range(0, len(participants_list), 20)]
            
            for i, chunk in enumerate(chunks):
                embed = discord.Embed(
                    title=f"🎁 Giveaway #{giveaway_id} Participants (Page {i+1}/{len(chunks)})",
                    description=f"**Prize:** {giveaway['prize']}\n**Total:** {len(participants)}\n\n" + "\n".join(chunk),
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed, ephemeral=True)
            
        except (IndexError, ValueError):
            await ctx.send("❌ Usage: `!gw participants <giveaway_id>`", ephemeral=True)
    
    # Show giveaway status
    elif subcommand == "status":
        try:
            giveaway_id = int(args_list[1])
            
            if giveaway_id not in active_giveaways:
                await ctx.send("❌ Giveaway not found!", ephemeral=True)
                return
            
            giveaway = active_giveaways[giveaway_id]
            remaining = int(giveaway['end_time'] - datetime.utcnow().timestamp())
            
            embed = discord.Embed(
                title=f"🎁 Giveaway #{giveaway_id} Status",
                color=discord.Color.blue()
            )
            embed.add_field(name="Prize:", value=giveaway['prize'], inline=False)
            embed.add_field(name="Winners:", value=str(giveaway['winner_count']), inline=True)
            embed.add_field(name="Participants:", value=str(len(giveaway['participants'])), inline=True)
            embed.add_field(name="Ends in:", value=f"<t:{int(giveaway['end_time'])}:R>", inline=False)
            embed.add_field(name="Host:", value=f"<@{giveaway['host']}>", inline=True)
            embed.add_field(name="Channel:", value=f"<#{giveaway['channel_id']}>", inline=True)
            
            if giveaway.get('image_url'):
                embed.set_image(url=giveaway['image_url'])
            
            await ctx.send(embed=embed, ephemeral=True)
            
        except (IndexError, ValueError):
            await ctx.send("❌ Usage: `!gw status <giveaway_id>`", ephemeral=True)
    
    # Statistics
    elif subcommand == "stats":
        total_giveaways = len(active_giveaways)
        total_participants = sum(len(g['participants']) for g in active_giveaways.values())
        total_winners = sum(g['winner_count'] for g in active_giveaways.values())
        
        embed = discord.Embed(
            title="📊 Giveaway Statistics",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Active Giveaways:", value=str(total_giveaways), inline=True)
        embed.add_field(name="Total Participants:", value=str(total_participants), inline=True)
        embed.add_field(name="Total Winners to Pick:", value=str(total_winners), inline=True)
        
        await ctx.send(embed=embed, ephemeral=True)
    
    # Export participants
    elif subcommand == "export":
        try:
            giveaway_id = int(args_list[1])
            
            if giveaway_id not in active_giveaways:
                await ctx.send("❌ Giveaway not found!", ephemeral=True)
                return
            
            giveaway = active_giveaways[giveaway_id]
            participants = giveaway['participants']
            
            if not participants:
                await ctx.send("📭 No participants to export!", ephemeral=True)
                return
            
            # Create a text file with participants
            filename = f"giveaway_{giveaway_id}_participants.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Giveaway #{giveaway_id} - {giveaway['prize']}\n")
                f.write(f"Total Participants: {len(participants)}\n")
                f.write("="*50 + "\n\n")
                for i, uid in enumerate(participants, 1):
                    try:
                        user = await bot.fetch_user(uid)
                        f.write(f"{i}. {user.name}#{user.discriminator} ({uid})\n")
                    except:
                        f.write(f"{i}. User ID: {uid}\n")
            
            await ctx.send(file=discord.File(filename), ephemeral=True)
            os.remove(filename)
            
        except (IndexError, ValueError):
            await ctx.send("❌ Usage: `!gw export <giveaway_id>`", ephemeral=True)

# Auto-delete only non-owner commands in GW channel (keeps help messages)
@bot.event
async def on_message(message):
    # ONLY auto-delete messages that are NOT from owner
    if message.channel.id == GW_CHANNEL_ID and message.author != bot.user:
        if message.content.startswith('!') and message.author.id != OWNER_ID:
            await asyncio.sleep(2)
            try:
                await message.delete()
            except:
                pass
    
    await bot.process_commands(message)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        # Silently fail for non-owners
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!", delete_after=5)
        try:
            await ctx.message.delete()
        except:
            pass
    else:
        print(f"Error: {error}")
        await ctx.send(f"❌ An error occurred: {str(error)}", delete_after=5)

# Run the bot
if __name__ == "__main__":
    load_giveaways()
    bot.run(BOT_TOKEN)