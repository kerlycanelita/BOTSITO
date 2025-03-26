const { REST, Routes } = require("discord.js");

const clientId = "1354310622027972658"; // Reemplaza con tu Client ID
const guildId = "1348479360084213801"; // Reemplaza con tu Guild ID
const token = "MTM1NDMxMDYyMjAyNzk3MjY1OA.GwSQgr.SFXX_nJFoNi6jF6iSPs4byyLFiJmC2gUPXDgjU"; // Reemplaza con tu token

const commands = [
    {
        name: 'tiernow',
        description: 'Muestra un mensaje con el estado del tier ahora.',
    },
    {
        name: 'setup',
        description: 'Configuracion de tiers VS.',
    }
];

const rest = new REST({ version: "10" }).setToken(token);

(async () => {
    try {
        console.log("⏳ Registrando comandos...");
        await rest.put(Routes.applicationGuildCommands(clientId, guildId), { body: commands });
        console.log("✅ Comandos registrados con éxito.");
    } catch (error) {
        console.error("❌ Error al registrar comandos:", error);
    }
})();
