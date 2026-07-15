"""
Module de gestion des niveaux et XP pour TicketMP.
Gère le système XP, les rangs et les classements.
"""
import discord
from typing import Optional, List, Dict


class LevelsManager:
    """Gestionnaire des niveaux et XP pour le serveur."""
    
    def __init__(self, bot: discord.Client, config: dict):
        self.bot = bot
        self.config = config
    
    def get_guild_config(self, guild_id: str) -> dict:
        """Récupère la configuration des niveaux pour un serveur."""
        guilds = self.config.get("guilds", {})
        gcfg = guilds.get(guild_id, {})
        return gcfg.get("levels", {})
    
    def is_enabled(self, guild_id: str) -> bool:
        """Vérifie si le système de niveaux est activé pour le serveur."""
        levels_config = self.get_guild_config(guild_id)
        return levels_config.get("enabled", False)
    
    def get_xp_per_message(self, guild_id: str) -> int:
        """Récupère le nombre d'XP par message."""
        levels_config = self.get_guild_config(guild_id)
        return levels_config.get("xp_per_message", 10)
    
    def get_xp_cooldown(self, guild_id: str) -> int:
        """Récupère le cooldown en secondes entre les gains d'XP."""
        levels_config = self.get_guild_config(guild_id)
        return levels_config.get("xp_cooldown", 60)
    
    def get_user_xp(self, guild_id: str, user_id: str) -> int:
        """Récupère l'XP d'un utilisateur."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            return 0
        
        gcfg = guilds[guild_id]
        if "levels" not in gcfg:
            return 0
        
        users_xp = gcfg["levels"].get("users_xp", {})
        return users_xp.get(user_id, 0)
    
    def set_user_xp(self, guild_id: str, user_id: str, xp: int) -> None:
        """Définit l'XP d'un utilisateur."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            guilds[guild_id] = {}
        
        gcfg = guilds[guild_id]
        if "levels" not in gcfg:
            gcfg["levels"] = {
                "enabled": False,
                "xp_per_message": 10,
                "xp_cooldown": 60,
                "users_xp": {},
                "ranks": [],
            }
        
        gcfg["levels"]["users_xp"][user_id] = xp
    
    def add_user_xp(self, guild_id: str, user_id: str, xp: int) -> int:
        """Ajoute de l'XP à un utilisateur et retourne le nouveau total."""
        current_xp = self.get_user_xp(guild_id, user_id)
        new_xp = current_xp + xp
        self.set_user_xp(guild_id, user_id, new_xp)
        return new_xp
    
    def get_level_from_xp(self, xp: int) -> int:
        """Calcule le niveau à partir de l'XP."""
        # Formule: niveau = floor(sqrt(xp / 10))
        return int((xp / 10) ** 0.5)
    
    def get_xp_for_level(self, level: int) -> int:
        """Calcule l'XP nécessaire pour un niveau."""
        # Formule inverse: xp = niveau^2 * 10
        return (level ** 2) * 10
    
    def get_user_level(self, guild_id: str, user_id: str) -> int:
        """Récupère le niveau d'un utilisateur."""
        xp = self.get_user_xp(guild_id, user_id)
        return self.get_level_from_xp(xp)
    
    def get_rank_role(self, guild_id: str, level: int) -> Optional[str]:
        """Récupère le rôle de rang pour un niveau."""
        levels_config = self.get_guild_config(guild_id)
        ranks = levels_config.get("ranks", [])
        
        for rank in sorted(ranks, key=lambda x: x.get("level", 0), reverse=True):
            if level >= rank.get("level", 0):
                return rank.get("role_id")
        
        return None
    
    def get_leaderboard(self, guild_id: str, limit: int = 10) -> List[tuple]:
        """Récupère le classement des utilisateurs."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            return []
        
        gcfg = guilds[guild_id]
        if "levels" not in gcfg:
            return []
        
        users_xp = gcfg["levels"].get("users_xp", {})
        
        # Trier par XP décroissant
        sorted_users = sorted(users_xp.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_users[:limit]
    
    def add_rank(self, guild_id: str, level: int, role_id: str) -> bool:
        """Ajoute un rang de niveau."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            guilds[guild_id] = {}
        
        gcfg = guilds[guild_id]
        if "levels" not in gcfg:
            gcfg["levels"] = {
                "enabled": False,
                "xp_per_message": 10,
                "xp_cooldown": 60,
                "users_xp": {},
                "ranks": [],
            }
        
        ranks = gcfg["levels"]["ranks"]
        
        # Vérifier si le niveau existe déjà
        for rank in ranks:
            if rank.get("level") == level:
                rank["role_id"] = role_id
                return True
        
        ranks.append({
            "level": level,
            "role_id": role_id,
        })
        
        return True
    
    def remove_rank(self, guild_id: str, level: int) -> bool:
        """Retire un rang de niveau."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            return False
        
        gcfg = guilds[guild_id]
        if "levels" not in gcfg:
            return False
        
        ranks = gcfg["levels"]["ranks"]
        
        for i, rank in enumerate(ranks):
            if rank.get("level") == level:
                ranks.pop(i)
                return True
        
        return False
    
    def get_ranks(self, guild_id: str) -> List[dict]:
        """Récupère la liste des rangs."""
        levels_config = self.get_guild_config(guild_id)
        return levels_config.get("ranks", [])
    
    async def assign_rank_role(self, member: discord.Member) -> bool:
        """Assigne le rôle de rang correspondant au niveau de l'utilisateur."""
        if not self.is_enabled(str(member.guild.id)):
            return False
        
        user_level = self.get_user_level(str(member.guild.id), str(member.id))
        rank_role_id = self.get_rank_role(str(member.guild.id), user_level)
        
        if not rank_role_id:
            return False
        
        role = member.guild.get_role(int(rank_role_id))
        if not role:
            return False
        
        try:
            # Retirer tous les rôles de rang
            ranks = self.get_ranks(str(member.guild.id))
            for rank in ranks:
                rank_role = member.guild.get_role(int(rank.get("role_id")))
                if rank_role and rank_role in member.roles:
                    await member.remove_roles(rank_role, reason="Mise à jour du rang")
            
            # Ajouter le nouveau rôle de rang
            if role not in member.roles:
                await member.add_roles(role, reason="Attribution du rang")
                return True
        except discord.Forbidden:
            return False
        except Exception:
            return False
        
        return False
