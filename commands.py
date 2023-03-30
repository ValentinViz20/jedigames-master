import asyncio
import difflib
import random
import time

import sqlitedict

import global_stuff
import global_stuff as gs

import discord

bot = gs.bot

STAFF_ROLE = 844107289261768744
APPROVAL_CHANNEL = 1041058921516912731


async def jed_help(channel, author):
    embed = discord.Embed(colour=0x962f27, description="")
    embed.set_author(name=f"{author.name}'s help", icon_url=author.avatar)
    embed.set_footer(text="Remember to add 'jed' in front of any command!")

    embed.description += """**These are the currently available commands:**

**Jedi's Word Game:**
[ `jed wg start` ] - start a word game
[ `jed wg help` ] - shows the rules of this game
[ `jed wg add [word] [definition]` ] - adds a new word into the bot!

"""

    await channel.send(embed=embed)


async def jed_wg_help(message):
    embed = discord.Embed(colour=random.randint(0, 0xffffff))
    embed.set_author(name=f"{message.author.name}'s word game help", icon_url=message.author.avatar)
    embed.set_footer(text="If you didn't join until the game started, you need to wait until the next round!")
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/892766502325997568/1038756303272681572/word_game_logo.png")

    embed.description = f"""
> ⭐ **HOW TO PLAY**:
— you need to guess words based on a definition
— you are given only the length of the word, each letter of a words gives 100 points
— you can request to see some of the word's letters, but each letter requested takes -100 points from the prize
— you start with 3 minutes to guess, and once your turn starts, this time will count down and you can request letters
— if you press the "GUESS" button the time will freeze and you have 30 seconds to guess the word, and you can't request letters anymore!
— if you don't guess the word you will receive negative points
— everyone will get 3 words of each length
"""

    await message.channel.send(embed=embed)


async def word_game(message: discord.Message):
    embed = discord.Embed(colour=random.randint(0, 0xffffff))
    embed.set_author(name=f"{message.author.name}'s word game", icon_url=message.author.avatar)
    embed.set_footer(text="If you didn't join until the game started, you need to wait until the next round!")
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/892766502325997568/1038756303272681572/word_game_logo.png")

    embed.description = f"""**{message.author.name}** wants to start a **Word Game**!
Press the join button to participate!
Use `jed wg help` to learn the rules of the game!

> __⏱ The game starts in 30 seconds!__"""

    view = discord.ui.View()
    view.add_item(
        join_btn := discord.ui.Button(label="Join", emoji="😺", style=discord.ButtonStyle.green, custom_id="join_wg"))
    view.add_item(
        leave_btn := discord.ui.Button(label="Leave", emoji="😿", style=discord.ButtonStyle.red, custom_id="leave_wg"))

    async def join_callback(interaction: discord.Interaction):
        if interaction.user in participants:
            await interaction.response.send_message("You already joined the game!", ephemeral=True)
            return

        participants.append(interaction.user)
        await interaction.response.send_message("You joined the game!", ephemeral=True)
        add_participant_field(embed, participants)
        await interaction.message.edit(embed=embed)

    async def leave_callback(interaction: discord.Interaction):
        if interaction.user not in participants:
            await interaction.response.send_message("You didn't join the game!", ephemeral=True)
            return

        participants.remove(interaction.user)
        await interaction.response.send_message("You left the game!", ephemeral=True)
        add_participant_field(embed, participants)
        await interaction.message.edit(embed=embed)

    join_btn.callback = join_callback
    leave_btn.callback = leave_callback

    participants = [message.author]
    add_participant_field(embed, participants)
    start_game_embed = await message.channel.send(embed=embed, view=view)

    await asyncio.sleep(5)

    view.stop()
    view.clear_items()
    view.add_item(discord.ui.Button(label="The game started!", emoji="✨", disabled=True))
    await start_game_embed.edit(view=view)

    if not participants:
        await message.channel.send("No one joined the game! Aborting...")
        return

    part_infos = {}

    for participant in participants:
        part_infos[participant.id] = {'user': participant, 'time_left': 60 * 3, 'points': 0}

    letter_btn = discord.ui.Button(label="Letter", emoji="❓", style=discord.ButtonStyle.blurple)
    guess_btn = discord.ui.Button(label="Guess!", emoji="✨", style=discord.ButtonStyle.green, custom_id='guess_wg')

    # WORDS = {1: ('word1', [('def', 'author')]),
    #          2: ('word2', [('def', 'author')])}

    word_length = 3
    valid_words_array = []
    change_length = True
    db = None
    show_of_this_size = 3

    while word_length < 11:
        at_lease_one = False

        if change_length:
            show_of_this_size = 3
            change_length = False
            word_length += 1

            db = sqlitedict.SqliteDict(f"databases/{word_length}-letter-words-db.sqlite", autocommit=True)
            try:
                amount_of_words_of_this_letter = db["ARRAY_SIZE"]
            except KeyError:
                await message.channel.send(f"⚠ I don't have any words of **length {word_length}**! Add more words with `jed wg add`! Game stopped!")
                await message.channel.send(f"{message.author.mention}, the game is over! These are the winners:",
                                           embed=show_leaderboard_wg(part_infos))
                return

            valid_words_array = list(range(amount_of_words_of_this_letter+1))

        for participant in part_infos:
            if part_infos[participant]['time_left'] <= 0:
                continue

            at_lease_one = True
            definition = ""
            word = ""
            append_back = []

            while True:
                if definition:
                    break

                if not valid_words_array:
                    await message.channel.send(f"⚠ No more eligible words of length {word_length}! Game aborted. (most likely because this user added a ton of words, or there are too many players!")
                    await message.channel.send(f"{message.author.mention}, the game is over! These are the winners:",
                                               embed=show_leaderboard_wg(part_infos))
                    return

                word_index = random.choice(valid_words_array)
                valid_words_array.remove(word_index)
                word, definitions = db[word_index]

                while True:
                    if not definitions:
                        append_back.append(word_index)
                        break
                    definition = random.choice(definitions)

                    # If the definition was given by this user, don't show the word
                    if definition[1] == participant:
                        definitions.remove(definition)
                        definition = ""
                    else:
                        definition = definition[0]
                        break

            # Add back the words that were not eligible for this user, but might be for others
            valid_words_array += append_back

            letters_found = [0 for i in word]

            async def get_letter_callback(interaction: discord.Interaction):
                if interaction.user.id != participant:
                    await interaction.response.send_message("It's not your turn!", ephemeral=True)
                    return

                not_guessed_indexes = []
                i = 0
                for letter, found in zip(word, letters_found):
                    if not found:
                        not_guessed_indexes.append(i)
                    else:
                        pass
                    i += 1

                index = random.choice(not_guessed_indexes)

                letters_found[index] = 1

                await interaction.response.defer()

            letter_btn.callback = get_letter_callback

            view = discord.ui.View()
            view.add_item(letter_btn)
            view.add_item(guess_btn)

            guess_info_embed = await message.channel.send(part_infos[participant]['user'].mention,
                                                          embed=format_game_embed(part_infos[participant], word,
                                                                                  definition, letters_found),
                                                          view=view)

            def check(inter: discord.Interaction):
                return inter.message.id == guess_info_embed.id and inter.user.id == participant

            timeout = 5 if part_infos[participant]['time_left'] > 5 else part_infos[participant]['time_left']
            time_freeze = False
            while True:
                try:
                    if timeout <= 0:
                        await message.channel.send(
                            f"{part_infos[participant]['user'].mention} your time expired! **Total points:** {part_infos[participant]['points']}")
                        break

                    if len(word) == sum(letters_found):
                        break

                    start_time = int(time.time())
                    interaction = await bot.wait_for('interaction', timeout=timeout, check=check)

                except asyncio.TimeoutError:
                    part_infos[participant]['time_left'] -= timeout
                    timeout = 5 if part_infos[participant]['time_left'] > 5 else part_infos[participant]['time_left']

                    await guess_info_embed.edit(
                        embed=format_game_embed(part_infos[participant], word, definition, letters_found))
                    continue

                if interaction.data['custom_id'] == 'guess_wg':
                    now = int(time.time())
                    time_passed = now - start_time

                    part_infos[participant]['time_left'] -= time_passed

                    time_freeze = True
                    await interaction.response.defer()
                    view.clear_items()
                    break

                else:
                    now = int(time.time())
                    time_passed = now - start_time

                    part_infos[participant]['time_left'] -= time_passed
                    await guess_info_embed.edit(embed=format_game_embed(part_infos[participant], word, definition,
                                                                        letters_found))
                    timeout = 5 if part_infos[participant]['time_left'] > 5 else part_infos[participant]['time_left']
                    continue

            won = False
            time_left = 30
            if time_freeze and part_infos[participant]['time_left'] > 0:
                def check(msg: discord.Message):
                    return msg.author.id == participant and msg.channel.id == message.channel.id

                while True:
                    try:
                        timeout = 10 if time_left > 10 else time_left
                        if timeout <= 0:
                            break

                        view.clear_items()
                        view.add_item(discord.ui.Button(label=f"Time left: {get_pretty_time(time_left)}", emoji="⏰",
                                                        disabled=True))
                        await guess_info_embed.edit(
                            embed=format_game_embed(part_infos[participant], word, definition, letters_found,
                                                    time_frozen=True), view=view)

                        start_time = int(time.time())

                        response = await bot.wait_for('message', timeout=timeout, check=check)
                    except asyncio.TimeoutError:
                        time_left -= timeout

                        continue

                    now = int(time.time())
                    time_left -= now - start_time

                    if ' ' in response.content:
                        await message.channel.send("The word doesn't contain any spaces!")
                        continue

                    if not response.content.isalpha():
                        await message.channel.send("The word doesn't contain any special characters, only letters!")
                        continue

                    if len(response.content) != len(word):
                        await message.channel.send(f"That's word has {len(response.content)} letters, not {len(word)}!")
                        continue

                    if response.content.lower() != word:
                        await message.channel.send("That's not the correct word!")
                        continue

                    pts = (len(word) * 100) - (100 * sum(letters_found))
                    part_infos[participant]['points'] += pts
                    await message.channel.send(f"Correct! You got {pts} points!")
                    won = True
                    break

            if not won and time_left <= 0:
                pts = -((len(word) * 100) - (100 * sum(letters_found)))
                part_infos[participant]['points'] += pts
                await message.channel.send(f"You didn't guess the word in time... You got {pts} points!")

            if not won and len(word) == sum(letters_found):
                pts = -len(word * 100)
                part_infos[participant]['points'] += pts
                await message.channel.send(f"You took all the letters?! You got {pts} points!")

        show_of_this_size -= 1

        if not show_of_this_size:
            change_length = True

        if not at_lease_one:
            await message.channel.send(f"{message.author.mention}, the game is over! These are the winners:",
                                       embed=show_leaderboard_wg(part_infos))
            break

        else:
            await message.channel.send(embed=show_leaderboard_wg(part_infos))


def show_leaderboard_wg(part_infos):
    users = []
    for user in part_infos:
        users.append((user, part_infos[user]['points']))

    sorted_users = sorted(users, key=lambda x: x[1], reverse=True)

    text = ""
    i = 1
    for user, score in sorted_users:
        text += f"**{i}.** {part_infos[user]['user']} — **{score} points**\n"
        i += 1

    embed = discord.Embed(colour=random.randint(0, 0xffffff))
    embed.description = f"""Leaderboard: 
{text}"""

    embed.set_author(name="Word Game Leaderboar!", icon_url=bot.user.avatar)
    embed.set_footer(text="This leaderboard is shown after everyone's turn is over!")

    return embed


def format_game_embed(user_info, word, definiton, current_guessed, time_frozen=False):
    embed = discord.Embed(colour=random.randint(0, 0xffffff))

    if time_frozen:
        embed.description = f"""**{user_info['user'].name}'s turn!**
**Your total score:** {user_info['points']}



> For **{(len(word) * 100) - (100 * sum(current_guessed))} points**:
"{definiton}" — **{len(word)} letters**

►► {word_to_emojis(word, current_guessed)} ◄◄
"""
        embed.description = f"""🔰**{user_info['user'].name}'s turn!**
**Your total score:** {user_info['points']}

❔ **{(len(word) * 100) - (100 * sum(current_guessed))} points** — **{len(word)} letters**:

> 📜 **This is the definition:** 
> "{definiton}" 

⏱ **TIME FROZEN** ❄
You have 30s to guess the word!

►► {word_to_emojis(word, current_guessed)} ◄◄
"""

    else:
        embed.description = f"""🔰**{user_info['user'].name}'s turn!**
**Your total score:** {user_info['points']}

❔ **{(len(word) * 100) - (100 * sum(current_guessed))} points** — **{len(word)} letters**:
> 📜 **This is the definition:** 
> "{definiton}" 

⏱ Time left: {get_pretty_time(user_info['time_left'])}

►► {word_to_emojis(word, current_guessed)} ◄◄
"""

    embed.set_author(name="Word Game!", icon_url=bot.user.avatar)
    embed.set_thumbnail(url=user_info['user'].avatar)
    return embed


def word_to_emojis(word, current_guessed):
    text = ""
    for letter, found in zip(word, current_guessed):
        if found:
            text += f":regional_indicator_{letter}:"
        else:
            text += "<:white_bar_down:1038771666899193936>"

    return text


def add_participant_field(embed: discord.Embed, participants):
    embed.clear_fields()
    participants_text = ""
    for i, participant in enumerate(participants, 1):
        participants_text += f"**{i}.** {participant}\n"

    if not participants_text:
        participants_text = "No one"

    embed.add_field(name="Participants:", value=participants_text)


def get_pretty_time(seconds):
    """Returns a string with the formatted time. If a unit of time is 0 (ex. 0 minutes, it wont be included.)
    Example:
    get_pretty_time(60) -> '1m'
    get_pretty_time(61) -> '1m 1s'
    get_pretty_time(3600) -> '1h'
    get_pretty_time(3601) -> '1h 1s'
"""
    if seconds <= 0:
        return '0s'

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)

    time_text = ""

    if weeks:
        time_text += f"{weeks}w "
    if days:
        time_text += f"{days}d "
    if hours:
        time_text += f"{hours}h "
    if minutes:
        time_text += f"{minutes}m "
    if seconds:  # if called with 0 returns 0s
        time_text += f"{seconds}s "

    return time_text[0:-1]


# ====================================================================================================================
# ====================================================================================================================
# ====================================================================================================================


async def add_word_wg(channel, author, command):
    args = command.split()[3:]

    if len(args) < 2:
        await channel.send(f"{author.mention} Correct usage: `jed wg add [word] [definition]`.\n"
                           f"The word must not contain spaces or special characters, you can add multiple definitions for the same word.")
        return

    word = args[0]
    definition = ' '.join(args[1:])

    if not word.isalpha() or ' ' in word:
        await channel.send(f"{author.mention} The word must not contain spaces or special characters!")
        return

    embed = discord.Embed(colour=random.randint(0, 0xffffff))
    embed.set_author(name=F"{author.name}'s word", icon_url=author.avatar)
    embed.set_footer(text="You can add multiple definitions for the same word!")

    embed.description = F"""❔ **Does everything look right?**
The word must not contain spaces or special characters.

**WORD:** {word}
**DEFINITION:** {definition}
"""

    view = discord.ui.View(timeout=60)
    view.add_item(yes_btn := discord.ui.Button(label="Yes", emoji="✔", style=discord.ButtonStyle.green))
    view.add_item(no_btn := discord.ui.Button(label="No", emoji="✖", style=discord.ButtonStyle.red))

    async def yes_callback(interaction: discord.Interaction):
        if interaction.user.id != author.id:
            return

        await interaction.response.send_message(f"{author.mention}, the word/definition was been send to approval to the bot's creators! You will get a DM if the word is approved!")

        if interaction.user.id != author.id:
            return
        approval_channel = bot.get_channel(APPROVAL_CHANNEL)
        yes_btn.label = "Approve"
        yes_btn.custom_id = "approve_word"

        no_btn.label = "Reject"
        no_btn.custom_id = "reject_word"

        wlength = len(word)

        db = sqlitedict.SqliteDict(f"databases/{wlength}-letter-words-db.sqlite", autocommit=True)
        all_definitions = []
        all_users = []
        similar_text = ""

        if word in db:
            index = db[word]
            definitions = db[index][1]

            for defi, user_id in definitions:
                all_definitions.append(defi)
                all_users.append(user_id)

            similar_def = difflib.get_close_matches(definition, all_definitions, 5)

            similar_text = '\n'.join(similar_def)

        if not similar_text:
            similar_text = "None"

        embed.description = F"""❔ **Does everything look right?**
The word must not contain spaces or special characters.

**WORD:** {word}
**DEFINITION:** {definition}

Word length: {len(word)}
Total definitions for this word: {len(all_definitions)}
Total definitions for this word added by this user: {all_users.count(author.id)}
Similar definitions found: 
{similar_text}
"""

        await approval_channel.send(f"{word}$$${definition}$$${author.id}", embed=embed, view=view)

        view.clear_items()
        view.stop()
        await interaction.message.edit(view=view)

    async def no_callback(interaction: discord.Interaction):
        if interaction.user.id != author.id:
            return

        view.clear_items()
        view.stop()

        await interaction.response.edit_message(view=view)
        await channel.send(f"{author.mention}, action cancelled. You can try again!")

    no_btn.callback = no_callback
    yes_btn.callback = yes_callback
    await channel.send(embed=embed, view=view)


# WORDS = {1: ('word1', [('def', 'author')]),
#          2: ('word2', [('def', 'author')])}


def add_word(word, definition, user_id):
    wlength = len(word)

    db = sqlitedict.SqliteDict(f"databases/{wlength}-letter-words-db.sqlite", autocommit=True)

    if word in db:
        index = db[word]
        definitions = db[index]

        definitions[1].append((definitions, user_id))
        db[index] = definitions
        db.close()

    else:
        try:
            index = db["ARRAY_SIZE"] + 1
        except KeyError:
            db["ARRAY_SIZE"] = 0
            index = 0

        definitions = (word, [(definition, user_id)])

        db[index] = definitions
        db[word] = index
        db["ARRAY_SIZE"] = index
        db.close()


async def jed_see_words(channel, author):
    text = f"""> These are all the words we have for the Jedi's Word Game:\n\n"""

    for i in range(1, 15):
        db = db = sqlitedict.SqliteDict(f"databases/{i}-letter-words-db.sqlite")

        if "ARRAY_SIZE" in db:
            text += f"**{i} letters long:** {db['ARRAY_SIZE'] + 1} words\n"

        db.close()

    embed = discord.Embed(colour=random.randint(0, 0xffffff))
    embed.set_author(name=F"{author.name}'s words", icon_url=author.avatar)
    embed.set_footer(text="You can add words using `jed wg add [word] [definition]`!")

    embed.description = text

    await channel.send(embed=embed)


def has_role(messageDOTauthor, role_ID):
    """Give it the message.author and the roleID int and it will return true if they havethe role!"""
    for roles in messageDOTauthor.roles:
        if roles.id == role_ID:
            return True
    return False


def get_empty_gem_data():
    return {'last_command': 0, 'amethyst': 0, 'cateye': 0, 'diamond': 0, 'emerald': 0, 'granite': 0, 'peridot': 0,
            'ruby': 0, 'opal': 0, 'sapphire': 0, 'quartz': 0, 'boosts': {}}


async def cooldown_warning(channel, author, time_left):
    embed = discord.Embed(colour=0x5907de)
    embed.set_author(name=f"{author.name} gem cooldown!", icon_url=author.avatar)

    hours, remainder = divmod(time_left, 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)

    time_text = ""

    if hours:
        time_text += f"{hours}h "
    if minutes:
        time_text += f"{minutes}m "
    if seconds:
        time_text += f"{seconds}s "

    embed.description = f"""You don't have enough energy to search for gems now!

Try again in **{time_text}**"""

    embed.set_footer(text="This command is on cooldown!")

    await channel.send(embed=embed)


async def jed_help_gems(channel: discord.TextChannel, author: discord.User):
    if author.id not in global_stuff.gem_db:
        data = get_empty_gem_data()
        data['name'] = str(author)
        global_stuff.gem_db[author.id] = data

    embed = discord.Embed(colour=0x5907de)
    embed.set_author(name=f"{author.name}'s gem help", icon_url=author.avatar)

    embed.description = f"""♦ **These commands are for the Gem Game!** ♦

🔹`jed gem help`/`jg help` - View this help command
🔹`jed gem search`/`jg search` - Search for more gems
🔹`jed gem inv`/`jg inv` - View your current gems
🔹`jg use [gem]` - Use one gem for temporary boosts!
🔹`jed gem boosts`/`jg boosts` - View what boosts the gem give and your active boosts!

🔹`jed gem lb`/`jg lb` - View the leaderboard with the best gem collectors!
"""

    await channel.send(embed=embed)

GEM_BOOSTS = {'amethyst': "Swaps the amount of 2 of your gems",
          'cateye': "Curse another player for 30m to have 25% chance to fail in finding a gem. ",
          'diamond': "Gives you 10% chance to find 2 gems at once for 20m",
          'emerald': "Removes a random gem of another user",
          'granite': "Gem Search cooldown becomes 10m for 1h, but you get 3 gems at once",
          'peridot': "Removes one of the gem boosts of another user",
          'ruby': "Gem Search cooldown is reduced by 1m30s for 20m",
          'opal': "30% chance to remove one random active curse form you",
          'sapphire': "Curse a player to add 1m to their Gem Search cooldown for 25m",
          'quartz': "45% chance to give you 3 random gems and 55% chance to remove 3 gems"}


async def jed_gems_boosts(channel: discord.TextChannel, author: discord.User):
    if author.id not in global_stuff.gem_db:
        data = get_empty_gem_data()
        data['name'] = str(author)
        global_stuff.gem_db[author.id] = data
    else:
        data = global_stuff.gem_db[author.id]

    embed = discord.Embed(colour=0x5907de)
    embed.set_author(name=f"{author.name}'s gem boosts", icon_url=author.avatar)

    embed.description = f"""♦ **These the boosts of the gems!** ♦\n\n⚠ Active curse gems means you are cursed yourself!.\n"""

    for gem in global_stuff.EMOJIS:
        embed.description += f"""{global_stuff.EMOJIS[gem]} **{gem.title()}** {'`[NOT ACTIVE]`' if gem not in data['boosts'] else f"`[{get_pretty_time(data['boosts'][gem] - int(time.time()))} left]`"}: {GEM_BOOSTS[gem]}\n"""

    await channel.send(embed=embed)


async def jed_view_lb(channel: discord.TextChannel, author: discord.User):
    embed = discord.Embed(colour=0x5907de)
    embed.set_author(name=f"{author.name}'s gem leaderboard", icon_url=author.avatar)

    most_gems = []
    most_collected = []

    for user in global_stuff.gem_db:
        data = global_stuff.gem_db[user]
        name = data['name']

        total_gems = sum([data[gem] for gem in global_stuff.EMOJIS])
        collected = sum([1 for gem in global_stuff.EMOJIS if data[gem] > 0])

        if len(most_gems) < 10:
            most_gems.append((user, total_gems, collected, name))

        else:
            for i, added_user in enumerate(most_gems):
                if added_user[1] < total_gems:
                    most_gems[i] = (user, total_gems, collected, name)
                    break

        if len(most_collected) < 10:
            most_collected.append((user, total_gems, collected, name))

        else:
            for i, added_user in enumerate(most_collected):
                if added_user[2] < collected:
                    most_collected[i] = (user, total_gems, collected, name)
                    break

    most_gems = sorted(most_collected, key=lambda x: x[1], reverse=True)
    most_collected = sorted(most_collected, key=lambda x: x[2], reverse=True)
    
    description = "> 🔶 **Most gems collected:** 🔶\n"
    for i, user in enumerate(most_gems, 1):
        description += f"**{i}.** {user[3]} - `gems`: {user[1]}, `found`: {user[2]}/10\n"

    description += "\n> 🔷 **Most gems found:** 🔷\n"
    for i, user in enumerate(most_collected, 1):
        description += f"**{i}.** {user[3]} - `gems`: {user[1]}, `found`: {user[2]}/10\n"

    embed.description = description
    await channel.send(embed=embed)


async def jed_use_gems(channel: discord.TextChannel, author: discord.User, command: str, mentions: list):
    command = command.replace('jg use', '')
    args = command.split()

    if not args:
        await channel.send(f"{author.mention} You must specify a gem! Example: `jg use ruby`.")
        return

    gem = args[0]
    if gem not in global_stuff.EMOJIS:
        await channel.send(f"{author.mention} Unknown gem type! Use `jg boosts` to see all the gems. Correct usage `js use [gem]`")
        return

    if author.id not in global_stuff.gem_db:
        data = get_empty_gem_data()
        data['name'] = str(author)
        global_stuff.gem_db[author.id] = data
    else:
        data = global_stuff.gem_db[author.id]

    if data[gem] < 1:
        await channel.send(f"{author.mention} You don't have any {gem}s in your inventory.")
        return

    if gem == 'amethyst':
        gem1 = random.choice(global_stuff.GEM_LIST)
        gem2 = random.choice(global_stuff.GEM_LIST)

        data[gem1], data[gem2] = data[gem2], data[gem1]
        await channel.send(f"{author.mention} The {gem} **SWAPED** the {gem1}s with {gem2}s!")

    elif gem == 'cateye':
        if not mentions:
            await channel.send(f"{author.mention} Please also ping the user at the end like this `jg use cateye @User`")
            return

        user = mentions[0]
        if user.id == author.id:
            await channel.send(f"{author.mention} You can't curse yourself!")
            return

        if user.id not in global_stuff.gem_db:
            await channel.send(f"{author.mention} You can't curse that player since they never played this game!")
            return

        user_data = global_stuff.gem_db[user.id]
        user_data['boosts']['cateye'] = int(time.time()) + 30*60
        global_stuff.gem_db[user.id] = user_data

        await channel.send(f"{author.mention} You **cursed** {user.mention} with a **Cateye**!")

    elif gem == 'diamond':
        data['boosts']['diamond'] = int(time.time()) + 20*60
        await channel.send(f"{author.mention} **Diamond** boost activated!")

    elif gem == 'emerald':
        if not mentions:
            await channel.send(f"{author.mention} Please also ping the user at the end like this `jg use emerald @User`")
            return

        user = mentions[0]
        if user.id == author.id:
            await channel.send(f"{author.mention} You can't curse yourself!")
            return

        if user.id not in global_stuff.gem_db:
            await channel.send(f"{author.mention} You can't curse that player since they never played this game!")
            return

        user_data = global_stuff.gem_db[user.id]
        gem1 = random.choice(global_stuff.GEM_LIST)
        user_data[gem1] -= 1
        if user_data[gem1] < 0:
            user_data[gem1] = 0

        global_stuff.gem_db[user.id] = user_data

        await channel.send(f"{author.mention} The **Emerald** took one {gem1} from {user.mention}!")

    elif gem == 'granite':
        data['boosts']['granite'] = int(time.time()) + 60 * 60
        await channel.send(f"{author.mention} **Granite** boost activated!")

    elif gem == 'peridot':
        if not mentions:
            await channel.send(f"{author.mention} Please also ping the user at the end like this `jg use emerald @User`")
            return

        user = mentions[0]
        if user.id == author.id:
            await channel.send(f"{author.mention} You can't curse yourself!")
            return

        if user.id not in global_stuff.gem_db:
            await channel.send(f"{author.mention} You can't curse that player since they never played this game!")
            return

        user_data = global_stuff.gem_db[user.id]

        if not user_data['boosts']:
            boost_to_remove = None
        else:
            boost_to_remove = random.choice(list(user_data['boosts'].keys()))

        if not boost_to_remove:
            await channel.send(f"{author.mention} That user didn't have a boost active, but you lost the peridot...")

        else:
            del user_data['boosts'][boost_to_remove]
            global_stuff.gem_db[user.id] = user_data
            await channel.send(f"{author.mention} The **peridot** removed the {boost_to_remove} boost from {user.mention}!")

    elif gem == 'ruby':
        data['boosts']['ruby'] = int(time.time()) + 20 * 60
        await channel.send(f"{author.mention} **Ruby** boost activated!")

    elif gem == 'opal':
        if random.randint(1, 100) >= 70:
            await channel.send(f"{author.mention} The opal shifts out of reality without removing a curse...")
        else:
            can_remove = []
            if 'cateye' in data['boosts']:
                can_remove.append('cateye')
            if 'sapphire' in data['boosts']:
               can_remove.append('sapphire')

            if not can_remove:
                await channel.send(f"{author.mention} You didn't have an active curse, but you lost the opal...")
            else:
                removed = random.choice(can_remove)
                del data['boosts'][removed]
                await channel.send(f"{author.mention} The **opal** removed your {removed} curse!")

    elif gem == 'sapphire':
        if not mentions:
            await channel.send(f"{author.mention} Please also ping the user at the end like this `jg use emerald @User`")
            return

        user = mentions[0]
        if user.id == author.id:
            await channel.send(f"{author.mention} You can't curse yourself!")
            return

        if user.id not in global_stuff.gem_db:
            await channel.send(f"{author.mention} You can't curse that player since they never played this game!")
            return

        user_data = global_stuff.gem_db[user.id]
        user_data['boosts']['sapphire'] = int(time.time()) + 25 * 60
        global_stuff.gem_db[user.id] = user_data

        await channel.send(f"{author.mention} The **Sapphire** cursed {user.mention}!")

    elif gem == 'quartz':
        added = [random.choice(global_stuff.GEM_LIST) for i in range(3)]
        if random.randint(1, 100) <= 45:

            for added_gem in added:
                data[added_gem] += 1
            await channel.send(f"{author.mention} The **Quartz** added you a {added[0]}, {added[1]} and a {added[2]}!")

        else:
            for added_gem in added:
                data[added_gem] -= 1
                if data[added_gem] < 0:
                    data[added_gem] = 0
            await channel.send(f"{author.mention} The **Quartz** removed you a {added[0]}, {added[1]} and a {added[2]}!")

    data[gem] -= 1
    global_stuff.gem_db[author.id] = data


async def jed_search_gems(channel: discord.TextChannel, author: discord.User):
    if author.id not in global_stuff.gem_db:
        data = get_empty_gem_data()
    else:
        data = global_stuff.gem_db[author.id]

    data['name'] = str(author)
    current_time = time.time()

    for boost in data['boosts'].copy():
        if data['boosts'][boost] < current_time:
            del data['boosts'][boost]

    if current_time - data['last_command'] <= 180.0:
        await cooldown_warning(channel, author, 180 - int(current_time - data['last_command']))
        return

    embed = discord.Embed(colour=0x5907de)
    embed.set_author(name=f"{author.name}'s gem search", icon_url=author.avatar)

    gem_found, amount = random.choice(list(global_stuff.EMOJIS.keys())), 1
    cooldown = 3 * 60

    if 'cateye' in data['boosts'] and random.randint(1, 100) <= 25:
        embed.description = f"""🙀 **THE CATEYE CURSE PREVENTS YOU FROM FINDING A GEM** 🙀"""
        amount = 0

    elif 'granite' in data['boosts']:
        amount = 3
        current_time += 7*60
        cooldown += 7*60
        embed.description = f"""ㅤ\nYou found **{amount} {global_stuff.EMOJIS[gem_found]} {gem_found.title()}**!\nㅤ"""

    elif 'diamond' in data['boosts'] and random.randint(1, 100) <= 10:
        amount = 2
        embed.description = f"""ㅤ\nYou found **{amount} {global_stuff.EMOJIS[gem_found]} {gem_found.title()}**!\nㅤ"""

    else:
        embed.description = f"""ㅤ\nYou found **{amount} {global_stuff.EMOJIS[gem_found]} {gem_found.title()}**!\nㅤ"""

    if 'ruby' in data['boosts']:
        current_time -= 90
        cooldown -= 90

    if 'sapphire' in data['boosts']:
        current_time += 60
        cooldown += 60

    embed.set_footer(text=f"View your gems using [jg inv]!")

    data[gem_found] += amount
    data['last_command'] = current_time

    global_stuff.gem_db[author.id] = data

    await channel.send(embed=embed)

    await asyncio.sleep(cooldown)
    await channel.send(f"{author.mention} **GEM SEARCH** is ready!")


async def jed_view_gems(channel: discord.TextChannel, author: discord.User, command: str):
    if author.id not in global_stuff.gem_db:
        data = get_empty_gem_data()
        data['name'] = str(author)

        global_stuff.gem_db[author.id] = data
    else:
        data = global_stuff.gem_db[author.id]

    command = command.replace("jed gem inv", '')\
        .replace("jg inv", '')\
        .replace("jed gem i", '')\
        .replace("jg i", '')\
        .replace('<@', '').replace('>', '')

    args = command.split()

    if args:
        another_user = args[0]

        if not another_user.isnumeric() or int(another_user) not in global_stuff.gem_db:
            await channel.send(f"{author.mention}, This user is not in my database! Correct usage: `jg i [@User / USER_ID]`.")
            return

        author = await global_stuff.bot.fetch_user(int(another_user))

    embed = discord.Embed(colour=0x5907de)
    embed.set_author(name=f"{author.name}'s gems", icon_url=author.avatar)

    description = f"> **These are your current gems!**\n\n"

    for gem in data:
        if gem in global_stuff.EMOJIS:
            description += f"{global_stuff.EMOJIS[gem]} **{gem.title()}** - {data[gem]}\n"

    description += "\n♦ `Collect more gems using `jed gem search`!`"

    embed.description = description

    await channel.send(embed=embed)


# elif command.startswith("jg show"):
#     for user in global_stuff.gem_db:
#         print(user, global_stuff.gem_db[user])
#
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