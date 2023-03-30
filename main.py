import asyncio
import random

import discord
import commands
import global_stuff
import global_stuff as gs

bot = gs.bot


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data['custom_id'] == 'approve_word':
        view = discord.ui.View()
        view.add_item(discord.ui.Button(emoji='✔', label='Approve', style=discord.ButtonStyle.green, disabled=True))
        view.add_item(discord.ui.Button(emoji='✖', label='Reject', style=discord.ButtonStyle.red, disabled=True))

        await interaction.response.edit_message(content=f'> **✅ APPROVED by {interaction.user.name}**', view=view)

        args = interaction.message.content.split("$$$")
        word, definition, user_id = args[0], args[1], int(args[2])

        try:
            host_dm = await bot.fetch_user(user_id)
            await host_dm.send(f"✅ Hello! Your word has been **approved** and added to the bot!\n"
                               f"You received 5 credits (`glob help` for more details)\n"
                               f"**WORD:** {word}\n"
                               f"**DEFINITION:** {definition}\nㅤ")

        except discord.errors.Forbidden:
            pass

        commands.add_word(word, definition, user_id)
        await interaction.message.channel.send(f"glob addcredits {user_id} 5")

    elif interaction.data['custom_id'] == 'reject_word':
        args = interaction.message.content.split("$$$")
        word, definition, user_id = args[0], args[1], int(args[2])

        host_dm = await bot.fetch_user(user_id)
        reason_modal = discord.ui.Modal(title="Reason for deny", custom_id='deny_reason')
        reason_modal.add_item(
            discord.ui.TextInput(label="What is the reason for denying?", style=discord.TextStyle.short))

        await interaction.response.send_modal(reason_modal)
        while True:
            try:
                interaction: discord.Interaction = await bot.wait_for('interaction', timeout=120)
            except asyncio.TimeoutError:
                return

            if interaction.data['custom_id'] == 'deny_reason':
                reason = interaction.data['components'][0]['components'][0]['value'].strip()
                break

        view = discord.ui.View()
        view.add_item(discord.ui.Button(emoji='✔', label='Approve', style=discord.ButtonStyle.green, disabled=True))
        view.add_item(discord.ui.Button(emoji='✖', label='Reject', style=discord.ButtonStyle.red, disabled=True))

        await interaction.response.edit_message(content=f'> **❌ DENIED by {interaction.user.name}**\n'
                                                        f'**Reason:** {reason}', view=view)

        try:
            await host_dm.send(f"""❌ Hello! Your word/definition has been **rejected**.
**Reason:** {reason}.
**WORD:** {word}
**DEFINITION:** {definition}
ㅤ""")

        except discord.errors.Forbidden:
            pass


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if str(bot.user.id) in message.content:
        await message.channel.send("Meow! I am online! My prefix is `jed`")
        return

    command = ' '.join(message.content.lower().split())

    if command.startswith("jed help"):
        await commands.jed_help(message.channel, message.author)
        return

    elif command.startswith(("jed wg help", "jed word game help")):
        await commands.jed_wg_help(message)
        return

    elif command.startswith(("jed wg add", "jed word game add")):
        await commands.add_word_wg(message.channel, message.author, command)
        return

    elif command.startswith(("jed wg words", "jed word game words")):
        await commands.jed_see_words(message.channel, message.author)
        return

    elif command.startswith(("jed gem help", "jg help")):
        await commands.jed_help_gems(message.channel, message.author)
        return

    elif command.startswith(("jed gem search", "jg search")):
        await commands.jed_search_gems(message.channel, message.author)
        return

    elif command.startswith(("jed gem lb", "jg lb")):
        await commands.jed_view_lb(message.channel, message.author)
        return

    elif command.startswith(("jed gem boosts", "jg boosts")):
        await commands.jed_gems_boosts(message.channel, message.author)
        return

    elif command.startswith("jg use"):
        await commands.jed_use_gems(message.channel, message.author, command, message.mentions)
        return

    elif command.startswith(("jed gem reset", "jg reset")) and message.author.id in (557841939375063068, 535023771879211010):
        for user in global_stuff.gem_db:
            del global_stuff.gem_db[user]

        await message.channel.send("DELETED the data of everyone!")

    # elif command.startswith("jg show"):
    #     for user in global_stuff.gem_db:
    #         print(user, global_stuff.gem_db[user])
    #
    elif command.startswith("jg addggg"):
        data = global_stuff.gem_db[557841939375063068]

        for gem in global_stuff.GEM_LIST:
            data[gem] = random.randint(10, 1000)

        global_stuff.gem_db[557841939375063068] = data
        await message.channel.send("DONE")

    # elif command.startswith("jg gen_rand"):
    #     for i in range(100):
    #         _id = random.randint(10000000, 9999999999)
    #         name = str(_id) + "USER"
    #         gems = {gem: random.randint(0, 1) for gem in global_stuff.EMOJIS}
    #         gems['last_command'] = 0
    #         gems['name'] = name
    #
    #         global_stuff.gem_db[_id] = gems
    #
    #     await message.channel.send("Generated 100 random users")
    #     return

    elif command.startswith(("jed gem inv", "jg inv",
                             "jed gem i", "jg i")):
        await commands.jed_view_gems(message.channel, message.author, command)
        return

    if commands.has_role(message.author, commands.STAFF_ROLE):
        if command.startswith(("jed wg start", "jed word game start")):
            await commands.word_game(message)
            return

if __name__ == '__main__':
    bot.run(gs.BOT_TOKEN)
