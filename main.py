import os
from typing import Optional
import discord
from discord import Attachment, app_commands
from treelib import Tree

from pywidevine.cdm.formats import wv_proto2_pb2

GUILD = discord.Object(id=os.environ["GUILD_ID"])
TOKEN = os.environ["TOKEN"]

IS_DEV = True if os.environ.get("IS_DEV_ENV") else False


class Client(discord.Client):
    def __init__(self, *, intents: discord.Intents, application_id: int):
        super().__init__(intents=intents, application_id=application_id)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store it and work with it.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)


intents = discord.Intents.default()
client = Client(intents=intents, application_id=os.environ["APPLICATION_ID"])


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


@client.tree.command()
@app_commands.describe(
    blob='Device Client ID Blob',
    private="Whether the information should be shown to only you or to everyone (default is just you)",
)
async def check(interaction: discord.Interaction, blob: discord.Attachment, private: bool = True):
    await interaction.response.defer(ephemeral=private, thinking=True)

    if blob.size > 4000:
        await interaction.followup.send(content='Nice fake blob. I\'m not going to check it.')
        return

    try:
        data = blob.read()
        client_id = wv_proto2_pb2.ClientIdentification()
        client_id.ParseFromString(data)
        tree = Tree()
        tree.create_node("**__Device Information__**", "root")
        client_info = client_id.ClientInfo
        for info in client_info:
            tree.create_node(f"**{info.Name}**: {info.Value}",
                             info.Name, parent="root")

        response_text = tree.show(stdout=False)
        await interaction.followup.send(content=response_text, ephemeral=private)
    except Exception as e:
        return await interaction.followup.send(content=f"Failed to parse id blob: {e}", ephemeral=private)


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing library. This example does both.
@client.tree.command()
@app_commands.describe(member='The member you want to get the joined date from, defaults to the user who uses the command')
async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    await interaction.response.send_message(f'{member} joined in {member.joined_at}')


client.run(TOKEN)
