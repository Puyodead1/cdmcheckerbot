import base64
import json
import os
from typing import Optional
import discord
from discord import app_commands
import requests
from treelib import Tree
from dotenv import load_dotenv

from pywidevine.cdm.formats import wv_proto2_pb2
from pywidevine.decrypt.wvdecryptcustom import WvDecrypt

load_dotenv()

GUILD = discord.Object(id=os.environ["GUILD_ID"])
TOKEN = os.environ["TOKEN"]
IS_DEV = True if os.environ.get("IS_DEV_ENV") else False

INIT_DATA = "AAAAaXBzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAAEkIARIQb2sbmIT4PQuGahvYrKOQ0hoIY2FzdGxhYnMiIGV5SmhjM05sZEVsa0lqb2lZV2RsYm5RdE16STNJbjA9MgdkZWZhdWx0"
LICENSE_URL = "https://lic.staging.drmtoday.com/license-proxy-widevine/cenc/?assetId=agent-327"

HEADERS = {
    "dt-custom-data":  base64.b64encode(json.dumps({
        "userId": "purchase",
        "sessionId": "default",
        "merchant": "client_dev",
    }).encode()).decode()
}

DT_CODES = {
    40001: "Widevine Device Certificate Revocation",
    40002: "Widevine Device Certificate Serial Number Revocation"
}


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
        # # This copies the global commands over to your guild.
        # self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync()


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
async def deivce_info(interaction: discord.Interaction, blob: discord.Attachment, private: bool = True):
    await interaction.response.defer(ephemeral=private, thinking=True)

    if blob.size > 4000:
        await interaction.followup.send(content='Nice fake blob. I\'m not going to check it.')
        return

    try:
        data = await blob.read()
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


@client.tree.command()
@app_commands.describe(
    device_client_id_blob='Device Client ID Blob',
    device_private_key='Device Private Key',
    private="Whether the information should be shown to only you or to everyone (default is just you)",
)
async def check_device(interaction: discord.Interaction, device_client_id_blob: discord.Attachment, device_private_key: discord.Attachment, private: bool = True):
    await interaction.response.defer(ephemeral=private, thinking=True)

    if device_client_id_blob.size > 4000:
        return await interaction.followup.send(content='Your client id blob is too big. I\'m not going to check it.')

    if device_private_key.size > 4000:
        return await interaction.followup.send(content='Your private key blob is too big. I\'m not going to check it.')

    try:
        device_client_id_bytes = await device_client_id_blob.read()
        device_private_key_bytes = await device_private_key.read()

        wvdecrypt = WvDecrypt(
            INIT_DATA, None, device_client_id_bytes, device_private_key_bytes)
        challenge = wvdecrypt.get_challenge()

        response = requests.post(LICENSE_URL, data=challenge, headers=HEADERS)
        if not response.ok:
            dt_resp_code = response.headers.get("x-dt-resp-code")
            res = "Unknown error"
            if dt_resp_code:
                res = "{} ({})".format(dt_resp_code, DT_CODES.get(
                    int(dt_resp_code), "Unknown Error"))
            return await interaction.followup.send(content=res, ephemeral=private)

        data = response.json()
        (make, model, level, whitelist_status, platform, device_state, max_hdcp, client_info, platform_verification, sys_id, crypto_version, soc, client_capabilities) = (
            data["make"], data["model"], data["security_level"], data["device_whitelist_state"], data["platform"], data["device_state"], data["client_max_hdcp_version"], data["client_info"], data["platform_verification_status"], data["system_id"], data["oem_crypto_api_version"], data["soc"], data["client_capabilities"])

        tree = Tree()
        tree.create_node("**__Device Information__**", "root")
        tree.create_node(f"**Make**: {make}", "make", parent="root")
        tree.create_node(f"**Model**: {model}", "model", parent="root")
        tree.create_node(
            f"**Security Level**: {level}", "level", parent="root")
        tree.create_node(f"**Whitelist Status**: {whitelist_status}",
                         "whitelist_status", parent="root")
        tree.create_node(
            f"**Platform**: {platform}", "platform", parent="root")
        tree.create_node(f"**Device State**: {device_state}",
                         "device_state", parent="root")
        tree.create_node(f"**Max HDCP Version**: {max_hdcp}",
                         "max_hdcp", parent="root")
        tree.create_node(f"**Client Info**:",
                         "client_info_root", parent="root")
        for info in client_info:
            name = info.get("name")
            value = info.get("value")
            tree.create_node(f"**{name}**: {value}",
                             name, parent="client_info_root")
        tree.create_node(f"**Platform Verification**: {platform_verification}",
                         "platform_verification", parent="root")
        tree.create_node(f"**System ID**: {sys_id}", "sys_id", parent="root")
        tree.create_node(f"**Crypto Version**: {crypto_version}",
                         "crypto_version", parent="root")
        tree.create_node(f"**SOC**: {soc}", "soc", parent="root")
        # tree.create_node(f"**Client Capabilities**: {client_capabilities}",
        #                     "client_capabilities", parent="root")
        tree.create_node(f"**Client Capabilities**:",
                         "client_capabilities_root", parent="root")
        for key, value in client_capabilities.items():
            tree.create_node(f"**{key}**: {value}", key,
                             parent="client_capabilities_root")

        response_text = tree.show(stdout=False)
        await interaction.followup.send(content=response_text, ephemeral=private)

    except Exception as e:
        return await interaction.followup.send(content=f"Error: {e}", ephemeral=private)


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
