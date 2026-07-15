"""
Module de logs avancés pour TicketMP.
Enregistre les événements du serveur avec des options de filtrage.
"""
import discord
from typing import Optional
from datetime import datetime


class AdvancedLogger:
    """Gestionnaire de logs avancés pour le serveur."""
    
    def __init__(self, bot: discord.Client, config: dict):
        self.bot = bot
        self.config = config
    
    def get_guild_config(self, guild_id: str) -> dict:
        """Récupère la configuration des logs pour un serveur."""
        guilds = self.config.get("guilds", {})
        gcfg = guilds.get(guild_id, {})
        return gcfg.get("advanced_logs", {})
    
    def is_enabled(self, guild_id: str, log_type: str) -> bool:
        """Vérifie si un type de log est activé pour le serveur."""
        log_config = self.get_guild_config(guild_id)
        return log_config.get(log_type, False)
    
    def get_log_channel(self, guild_id: str) -> Optional[discord.TextChannel]:
        """Récupère le salon de logs pour le serveur."""
        log_config = self.get_guild_config(guild_id)
        channel_id = log_config.get("channel_id")
        if not channel_id:
            return None
        return self.bot.get_channel(int(channel_id))
    
    async def log(self, guild_id: str, embed: discord.Embed) -> bool:
        """Envoie un log dans le salon configuré."""
        if not self.is_enabled(guild_id, "enabled"):
            return False
        
        channel = self.get_log_channel(guild_id)
        if not channel:
            return False
        
        try:
            await channel.send(embed=embed)
            return True
        except discord.Forbidden:
            return False
        except Exception:
            return False
    
    async def log_message_delete(self, message: discord.Message) -> bool:
        """Log la suppression d'un message."""
        if not self.is_enabled(str(message.guild.id), "message_delete"):
            return False
        
        embed = discord.Embed(
            title="🗑️ Message supprimé",
            description=f"Message de {message.author.mention} supprimé dans {message.channel.mention}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Auteur", value=message.author.mention, inline=True)
        embed.add_field(name="Salon", value=message.channel.mention, inline=True)
        
        if message.content:
            embed.add_field(name="Contenu", value=message.content[:1024], inline=False)
        
        if message.attachments:
            files_list = "\n".join([f"📎 {a.filename}" for a in message.attachments])
            embed.add_field(name="Pièces jointes", value=files_list, inline=False)
        
        return await self.log(str(message.guild.id), embed)
    
    async def log_message_edit(self, before: discord.Message, after: discord.Message) -> bool:
        """Log la modification d'un message."""
        if not self.is_enabled(str(after.guild.id), "message_edit"):
            return False
        
        if before.content == after.content:
            return False
        
        embed = discord.Embed(
            title="✏️ Message modifié",
            description=f"Message de {after.author.mention} modifié dans {after.channel.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Auteur", value=after.author.mention, inline=True)
        embed.add_field(name="Salon", value=after.channel.mention, inline=True)
        
        if before.content:
            embed.add_field(name="Avant", value=before.content[:1024], inline=False)
        
        if after.content:
            embed.add_field(name="Après", value=after.content[:1024], inline=False)
        
        return await self.log(str(after.guild.id), embed)
    
    async def log_member_join(self, member: discord.Member) -> bool:
        """Log l'arrivée d'un membre."""
        if not self.is_enabled(str(member.guild.id), "member_join"):
            return False
        
        embed = discord.Embed(
            title="👋 Membre rejoint",
            description=f"{member.mention} a rejoint le serveur",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Membre", value=f"{member.mention} ({member.id})", inline=True)
        embed.add_field(name="Compte créé", value=member.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        return await self.log(str(member.guild.id), embed)
    
    async def log_member_leave(self, member: discord.Member) -> bool:
        """Log le départ d'un membre."""
        if not self.is_enabled(str(member.guild.id), "member_leave"):
            return False
        
        embed = discord.Embed(
            title="👋 Membre parti",
            description=f"{member.mention} a quitté le serveur",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Membre", value=f"{member.mention} ({member.id})", inline=True)
        embed.add_field(name="Rejoint le", value=member.joined_at.strftime("%d/%m/%Y %H:%M") if member.joined_at else "N/A", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        return await self.log(str(member.guild.id), embed)
    
    async def log_role_add(self, member: discord.Member, role: discord.Role) -> bool:
        """Log l'ajout d'un rôle."""
        if not self.is_enabled(str(member.guild.id), "role_add"):
            return False
        
        embed = discord.Embed(
            title="➕ Rôle ajouté",
            description=f"Rôle {role.mention} ajouté à {member.mention}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Membre", value=member.mention, inline=True)
        embed.add_field(name="Rôle", value=role.mention, inline=True)
        
        return await self.log(str(member.guild.id), embed)
    
    async def log_role_remove(self, member: discord.Member, role: discord.Role) -> bool:
        """Log le retrait d'un rôle."""
        if not self.is_enabled(str(member.guild.id), "role_remove"):
            return False
        
        embed = discord.Embed(
            title="➖ Rôle retiré",
            description=f"Rôle {role.mention} retiré de {member.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Membre", value=member.mention, inline=True)
        embed.add_field(name="Rôle", value=role.mention, inline=True)
        
        return await self.log(str(member.guild.id), embed)
    
    async def log_role_change(self, before: discord.Member, after: discord.Member) -> bool:
        """Log les changements de rôles d'un membre."""
        if not self.is_enabled(str(after.guild.id), "role_add") and not self.is_enabled(str(after.guild.id), "role_remove"):
            return False
        
        # Détecter les rôles ajoutés
        added_roles = set(after.roles) - set(before.roles)
        for role in added_roles:
            if not role.is_default():
                await self.log_role_add(after, role)
        
        # Détecter les rôles retirés
        removed_roles = set(before.roles) - set(after.roles)
        for role in removed_roles:
            if not role.is_default():
                await self.log_role_remove(before, role)
        
        return True
    
    async def log_command_used(self, interaction: discord.Interaction, command_name: str) -> bool:
        """Log l'utilisation d'une commande."""
        if not interaction.guild:
            return False
        
        if not self.is_enabled(str(interaction.guild.id), "command_used"):
            return False
        
        embed = discord.Embed(
            title="⚡ Commande utilisée",
            description=f"`/{command_name}` utilisé par {interaction.user.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Utilisateur", value=interaction.user.mention, inline=True)
        embed.add_field(name="Salon", value=interaction.channel.mention if interaction.channel else "MP", inline=True)
        
        return await self.log(str(interaction.guild.id), embed)
    
    async def log_config_change(self, guild_id: str, changed_by: discord.Member, setting: str, old_value: str, new_value: str) -> bool:
        """Log un changement de configuration."""
        if not self.is_enabled(str(guild_id), "config_change"):
            return False
        
        embed = discord.Embed(
            title="⚙️ Configuration modifiée",
            description=f"Paramètre `{setting}` modifié par {changed_by.mention}",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Modifié par", value=changed_by.mention, inline=True)
        embed.add_field(name="Paramètre", value=setting, inline=True)
        embed.add_field(name="Avant", value=old_value, inline=True)
        embed.add_field(name="Après", value=new_value, inline=True)
        
        return await self.log(str(guild_id), embed)
