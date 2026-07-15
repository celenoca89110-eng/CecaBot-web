"""
Module de gestion des auto-rôles pour TicketMP.
Gère les rôles automatiques à l'arrivée, les rôles par réaction et les rôles personnalisés.
"""
import discord
from typing import Optional, List


class AutoRoleManager:
    """Gestionnaire des auto-rôles pour le serveur."""
    
    def __init__(self, bot: discord.Client, config: dict):
        self.bot = bot
        self.config = config
    
    def get_guild_config(self, guild_id: str) -> dict:
        """Récupère la configuration des auto-rôles pour un serveur."""
        guilds = self.config.get("guilds", {})
        gcfg = guilds.get(guild_id, {})
        return gcfg.get("autorole", {})
    
    def is_enabled(self, guild_id: str) -> bool:
        """Vérifie si les auto-rôles sont activés pour le serveur."""
        autorole_config = self.get_guild_config(guild_id)
        return autorole_config.get("enabled", False)
    
    async def assign_join_roles(self, member: discord.Member) -> bool:
        """Assigne les rôles automatiques à l'arrivée d'un membre."""
        if not self.is_enabled(str(member.guild.id)):
            return False
        
        autorole_config = self.get_guild_config(str(member.guild.id))
        join_roles = autorole_config.get("join_roles", [])
        
        if not join_roles:
            return False
        
        try:
            roles_to_add = []
            for role_id in join_roles:
                role = member.guild.get_role(int(role_id))
                if role and role not in member.roles:
                    roles_to_add.append(role)
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Auto-rôle à l'arrivée")
                return True
        except discord.Forbidden:
            return False
        except Exception:
            return False
        
        return False
    
    async def assign_reaction_role(self, payload: discord.RawReactionActionEvent) -> bool:
        """Assigne un rôle lors de l'ajout d'une réaction."""
        if not payload.guild_id:
            return False
        
        if not self.is_enabled(str(payload.guild_id)):
            return False
        
        autorole_config = self.get_guild_config(str(payload.guild_id))
        reaction_roles = autorole_config.get("reaction_roles", [])
        
        # Trouver le rôle correspondant à l'emoji et au message
        for rr in reaction_roles:
            if rr.get("message_id") == str(payload.message_id) and rr.get("emoji") == str(payload.emoji):
                role_id = rr.get("role_id")
                if not role_id:
                    continue
                
                guild = self.bot.get_guild(payload.guild_id)
                if not guild:
                    continue
                
                member = guild.get_member(payload.user_id)
                if not member:
                    continue
                
                role = guild.get_role(int(role_id))
                if not role:
                    continue
                
                try:
                    if role not in member.roles:
                        await member.add_roles(role, reason="Rôle par réaction")
                        return True
                except discord.Forbidden:
                    return False
                except Exception:
                    return False
        
        return False
    
    async def remove_reaction_role(self, payload: discord.RawReactionActionEvent) -> bool:
        """Retire un rôle lors du retrait d'une réaction."""
        if not payload.guild_id:
            return False
        
        if not self.is_enabled(str(payload.guild_id)):
            return False
        
        autorole_config = self.get_guild_config(str(payload.guild_id))
        reaction_roles = autorole_config.get("reaction_roles", [])
        
        # Trouver le rôle correspondant à l'emoji et au message
        for rr in reaction_roles:
            if rr.get("message_id") == str(payload.message_id) and rr.get("emoji") == str(payload.emoji):
                role_id = rr.get("role_id")
                if not role_id:
                    continue
                
                guild = self.bot.get_guild(payload.guild_id)
                if not guild:
                    continue
                
                member = guild.get_member(payload.user_id)
                if not member:
                    continue
                
                role = guild.get_role(int(role_id))
                if not role:
                    continue
                
                try:
                    if role in member.roles:
                        await member.remove_roles(role, reason="Rôle par réaction retiré")
                        return True
                except discord.Forbidden:
                    return False
                except Exception:
                    return False
        
        return False
    
    def add_reaction_role(self, guild_id: str, message_id: str, emoji: str, role_id: str) -> bool:
        """Ajoute un rôle par réaction."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            guilds[guild_id] = {}
        
        gcfg = guilds[guild_id]
        if "autorole" not in gcfg:
            gcfg["autorole"] = {
                "enabled": False,
                "join_roles": [],
                "reaction_roles": [],
            }
        
        reaction_roles = gcfg["autorole"]["reaction_roles"]
        
        # Vérifier si la combinaison existe déjà
        for rr in reaction_roles:
            if rr.get("message_id") == message_id and rr.get("emoji") == emoji:
                return False
        
        reaction_roles.append({
            "message_id": message_id,
            "emoji": emoji,
            "role_id": role_id,
        })
        
        return True
    
    def remove_reaction_role(self, guild_id: str, message_id: str, emoji: str) -> bool:
        """Retire un rôle par réaction."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            return False
        
        gcfg = guilds[guild_id]
        if "autorole" not in gcfg:
            return False
        
        reaction_roles = gcfg["autorole"]["reaction_roles"]
        
        for i, rr in enumerate(reaction_roles):
            if rr.get("message_id") == message_id and rr.get("emoji") == emoji:
                reaction_roles.pop(i)
                return True
        
        return False
    
    def add_join_role(self, guild_id: str, role_id: str) -> bool:
        """Ajoute un rôle automatique à l'arrivée."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            guilds[guild_id] = {}
        
        gcfg = guilds[guild_id]
        if "autorole" not in gcfg:
            gcfg["autorole"] = {
                "enabled": False,
                "join_roles": [],
                "reaction_roles": [],
            }
        
        join_roles = gcfg["autorole"]["join_roles"]
        
        if role_id not in join_roles:
            join_roles.append(role_id)
            return True
        
        return False
    
    def remove_join_role(self, guild_id: str, role_id: str) -> bool:
        """Retire un rôle automatique à l'arrivée."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            return False
        
        gcfg = guilds[guild_id]
        if "autorole" not in gcfg:
            return False
        
        join_roles = gcfg["autorole"]["join_roles"]
        
        if role_id in join_roles:
            join_roles.remove(role_id)
            return True
        
        return False
    
    def get_reaction_roles(self, guild_id: str) -> List[dict]:
        """Récupère la liste des rôles par réaction."""
        autorole_config = self.get_guild_config(guild_id)
        return autorole_config.get("reaction_roles", [])
    
    def get_join_roles(self, guild_id: str) -> List[str]:
        """Récupère la liste des rôles automatiques à l'arrivée."""
        autorole_config = self.get_guild_config(guild_id)
        return autorole_config.get("join_roles", [])
