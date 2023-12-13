### paps-bot
Discord bot for planning pen-and-paper-shenanigans and more.

Creating an organising events like in-person pen-and-paper gaming sessions can be a pain, so while chatting and trying to organise sessions over discord a thought occoured:"Why not have a bot for that?!"

So here is the pen-and-paper shennenigans bot for discord. A bot used to help set up, and sign up for pen-and-paper events, and displaying reminders for future events.

Currently the main feature of paps-bot, is incorporating the discord bot API to receive commands from discord, mainly surrounding planning events. And supporting the organisation of such.

I learned a great deal during this endavour, it was a first dive into asynchronous python programming, and it was a trip to figure out. 

Paps-bot using asynchronous commands and the discord-api to listen in on a assigned channel for specific prompts and formats, once a supported command is submitted, like an event. 
![image](https://github.com/DanishKodeMonkey/paps-bot/assets/121358075/89365777-afec-45fe-ae97-0927c075db2b)



Then paps bot handles the formatting and submitting of the event to a postgresSQL database
![image](https://github.com/DanishKodeMonkey/paps-bot/assets/121358075/f8e8a63f-aa52-4fb0-ba7b-45cc2d596a85)



Then, as needed, a event can be edited, pulled, or removed, by the users. 
![image](https://github.com/DanishKodeMonkey/paps-bot/assets/121358075/e666af32-df25-4db9-b4b1-eb183c6e9590)

![image](https://github.com/DanishKodeMonkey/paps-bot/assets/121358075/8fad4fc7-131f-4ff8-bdd1-89debe64b169)

![image](https://github.com/DanishKodeMonkey/paps-bot/assets/121358075/414b81d9-f74b-4980-88cd-6f3e6e7b5fb4)



It's even possible to submit a search query and pull specific searches depending on what time/date or game sort it is about.
Furthermore, should need be a event can be submitted in form of a vote from participating members, should enough members vote for an event, it will be saved. If not, discarded.
![image](https://github.com/DanishKodeMonkey/paps-bot/assets/121358075/8e80dc47-eeee-4e3b-979b-91a8e0ac966a)



UPDATE:
Slash commands implemented, much cleaner, all commands converted to slash command format.
![image](https://github.com/DanishKodeMonkey/paps-bot/assets/121358075/4cecb516-354c-42bf-aa48-14da1ca1dee0)


WIP features:
Attendee signup:
Discord server members can associate their user to the bot, allowing for event signups, reminders, and more.
