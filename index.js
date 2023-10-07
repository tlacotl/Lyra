const { Client, GatewayIntentBits, EmbedBuilder, ButtonStyle, PermissionsBitField, Permissions, MessageManager, Embed, Collection, User, Events, ActionRowBuilder, ButtonBuilder } = require(`discord.js`);
const fs = require('fs');
const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent, GatewayIntentBits.GuildMembers, GatewayIntentBits.GuildPresences ] }); 

client.commands = new Collection();

require('dotenv').config();

const functions = fs.readdirSync("./src/functions").filter(file => file.endsWith(".js"));
const eventFiles = fs.readdirSync("./src/events").filter(file => file.endsWith(".js"));
const commandFolders = fs.readdirSync("./src/commands");

(async () => {
    for (file of functions) {
        require(`./functions/${file}`)(client);
    }
    client.handleEvents(eventFiles, "./src/events");
    client.handleCommands(commandFolders, "./src/commands");
})();

client.once("ready", () => {
    //bot activity
    client.user.setActivity("in Nae Nae HELL. /help");
});

//reminder
const remindSchema = require('./Schemas.js/remindSchema');
setInterval(async () => {

    const reminders = await remindSchema.find();
    if (!reminders) return;
    else {

        reminders.forEach( async reminder => {

            if(reminder.Time > Date.now()) return;

            const user = await client.users.fetch(reminder.User);

            user?.send({
                content: `${user}, you asked me to remind you about: \`${reminder.Remind}\``
            }).catch(err => {return;});

            await remindSchema.deleteMany({
                Time: reminder.Time,
                User: user.id,
                Remind: reminder.Remind
            });
        });
    }
}, 1000 * 5);


client.login(process.env.token); //logs in