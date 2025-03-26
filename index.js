const { 
    Client, 
    GatewayIntentBits, 
    REST, 
    Routes, 
    PermissionsBitField, 
    ActionRowBuilder, 
    ButtonBuilder, 
    ButtonStyle, 
    ModalBuilder, 
    TextInputBuilder, 
    TextInputStyle
} = require("discord.js");
const MinecraftServerUtil = require('minecraft-server-util');  // Importamos la librería para obtener info del servidor de Minecraft

const client = new Client({ intents: 53608447 });

// ⚠️ Reemplaza estos valores con los tuyos
const token = "MTM1NDMxMDYyMjAyNzk3MjY1OA.GwSQgr.SFXX_nJFoNi6jF6iSPs4byyLFiJmC2gUPXDgjU";
const clientId = "1354310622027972658";
const guildId = "1348479360084213801";
const prefix = "!";
const commands = [
    {
        name: 'tiernow',
        description: 'Muestra un mensaje con el estado del tier ahora.',
    },
    {
        name: 'setup',
        description: 'Configuración de Tiers VS.',
    },
    {
        name: 'ping',
        description: 'Obtiene el ping, jugadores y la versión de un servidor Minecraft.',
        options: [
            {
                name: 'server',
                type: 3, // Tipo "string" para el servidor
                description: 'El nombre o IP del servidor de Minecraft.',
                required: true
            }
        ]
    }
];

const rest = new REST({ version: '10' }).setToken(token);

(async () => {
    try {
        console.log('⏳ Registrando comandos Slash...');
        await rest.put(
            Routes.applicationGuildCommands(clientId, guildId),
            { body: commands }
        );
        console.log('✅ Comandos Slash registrados con éxito!');
    } catch (error) {
        console.error('❌ Error al registrar comandos:', error);
    }
})();

// 📌 Evento cuando el bot se enciende
client.once("ready", () => {
    console.log(`🔥 Bot encendido como: ${client.user.tag}`);
});

// 📌 Evento para Slash Commands
client.on("interactionCreate", async (interaction) => {
    if (!interaction.isCommand()) return;

    const { commandName, member } = interaction;

    if (commandName === 'tiernow') {
        await interaction.reply('📢 Barrel Leader VS Xsupreme Xsy **follada inminente**');
    }

    if (commandName === 'setup') {
        // 📌 Verificar si es administrador
        if (!member.permissions.has(PermissionsBitField.Flags.Administrator)) {
            return interaction.reply({ 
                content: "❌ No tienes permisos para usar este comando.", 
                ephemeral: true 
            });    
        }

        // 📌 Crear botón de registro
        const row = new ActionRowBuilder()
            .addComponents(
                new ButtonBuilder()
                    .setCustomId('register')
                    .setLabel('📝 Registrarse en Tiers VS')
                    .setStyle(ButtonStyle.Primary)
            );

        // 📌 Enviar mensaje con botones
        await interaction.reply({
            content: "📢 **¡Bienvenidos al registro de Tiers VS!**\n\nHaz clic en el botón de abajo para registrarte.",
            components: [row]
        });
    }

    // 📌 Comando /ping para obtener información del servidor Minecraft Bedrock
    if (commandName === 'ping') {
        const server = interaction.options.getString('server'); // Obtener el nombre o IP del servidor
        const port = 25565;  // Puerto predeterminado para servidores Java

        try {
            // 📌 Comprobar si el servidor es de tipo Bedrock (puedes hacer esta comprobación de manera manual o automática)
            const server = interaction.options.getString('server'); // Obtener el nombre o IP del servidor
            const port = server.includes('bedrock') || server.includes('19132') ? 19132 : 25565; // Si contiene "bedrock" o el puerto de Bedrock, usar 19132, de lo contrario usar 25565 (Java Edition)

            // 📌 Extraer la información relevante
            const ping = status.ping; // Tiempo de ping
            const players = status.players.online; // Número de jugadores en línea
            const version = status.version.name; // Versión del servidor

            // 📌 Responder con la información del servidor
            await interaction.reply({
                content: `🏓 **Ping de ${server}:** ${ping} ms\n👥 **Jugadores en línea:** ${players}\n🌍 **Versión del servidor:** ${version}`,
                ephemeral: true
            });
        } catch (error) {
            // Si hubo un error al obtener la información
            console.error(error);
            await interaction.reply({
                content: `❌ No se pudo obtener información del servidor **${server}**.`,
                ephemeral: true
            });
        }
    }
});

// 📌 Manejar interacción con el botón "Registrarse"
client.on("interactionCreate", async (interaction) => {
    if (!interaction.isButton()) return;

    if (interaction.customId === 'register') {
        // 📌 Crear un modal (formulario)
        const modal = new ModalBuilder()
            .setCustomId('register_modal')
            .setTitle('Registro en Tiers VS');

        // 📌 Crear los campos del formulario
        const nameInput = new TextInputBuilder()
            .setCustomId('name')
            .setLabel('📛 Nombre:')
            .setStyle(TextInputStyle.Short)
            .setPlaceholder('Escribe tu nombre aquí...')
            .setRequired(true);

        const ageInput = new TextInputBuilder()
            .setCustomId('age')
            .setLabel('🎂 Edad:')
            .setStyle(TextInputStyle.Short)
            .setPlaceholder('Ejemplo: 18')
            .setRequired(true);

        const regionInput = new TextInputBuilder()
            .setCustomId('region')
            .setLabel('🌍 Región:')
            .setStyle(TextInputStyle.Short)
            .setPlaceholder('Ejemplo: LATAM, NA, EU, etc.')
            .setRequired(true);

        // 📌 Agregar los campos al modal
        const firstRow = new ActionRowBuilder().addComponents(nameInput);
        const secondRow = new ActionRowBuilder().addComponents(ageInput);
        const thirdRow = new ActionRowBuilder().addComponents(regionInput);

        modal.addComponents(firstRow, secondRow, thirdRow);

        // 📌 Mostrar el modal al usuario
        await interaction.showModal(modal);
    }
});

// 📌 Manejar los datos enviados por el formulario
const staffChannelId = "1352885601371951196"; // 🔴 Reemplaza con el ID del canal donde se enviarán los registros

client.on("interactionCreate", async (interaction) => {
    if (!interaction.isModalSubmit()) return;

    if (interaction.customId === 'register_modal') {
        const name = interaction.fields.getTextInputValue('name');
        const age = interaction.fields.getTextInputValue('age');
        const region = interaction.fields.getTextInputValue('region');

        // 📌 Buscar el canal de staff
        const staffChannel = client.channels.cache.get(staffChannelId);
        if (!staffChannel) return console.error('❌ No se encontró el canal de staff.');

        // 📌 Enviar los datos al canal de staff
        await staffChannel.send(`📌 **Nuevo Registro en Tiers VS**\n\n📛 **Nombre:** ${name}\n🎂 **Edad:** ${age}\n🌍 **Región:** ${region}\n\n🔍 Registrado por: <@${interaction.user.id}>`);

        // 📌 Responder al usuario
        await interaction.reply({
            content: "✅ ¡Tu registro ha sido enviado con éxito!",
            ephemeral: true
        });
    }
});

// 📌 Iniciar el bot
client.login(token);
