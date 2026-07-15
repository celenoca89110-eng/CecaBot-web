"""
Module de gestion des suggestions pour TicketMP.
Gère le système de suggestions avec votes, acceptation et refus.
"""
import discord
from typing import Optional, List, Dict
from datetime import datetime


class SuggestionsManager:
    """Gestionnaire des suggestions pour le serveur."""
    
    def __init__(self, bot: discord.Client, config: dict):
        self.bot = bot
        self.config = config
    
    def get_guild_config(self, guild_id: str) -> dict:
        """Récupère la configuration des suggestions pour un serveur."""
        guilds = self.config.get("guilds", {})
        gcfg = guilds.get(guild_id, {})
        return gcfg.get("suggestions", {})
    
    def is_enabled(self, guild_id: str) -> bool:
        """Vérifie si le système de suggestions est activé pour le serveur."""
        suggestions_config = self.get_guild_config(guild_id)
        return suggestions_config.get("enabled", False)
    
    def get_suggestions_channel(self, guild_id: str) -> Optional[str]:
        """Récupère l'ID du salon de suggestions."""
        suggestions_config = self.get_guild_config(guild_id)
        return suggestions_config.get("channel_id")
    
    def create_suggestion(self, guild_id: str, user_id: str, content: str) -> str:
        """Crée une nouvelle suggestion et retourne son ID."""
        guilds = self.config.get("guilds", {})
        if guild_id not in guilds:
            guilds[guild_id] = {}
        
        gcfg = guilds[guild_id]
        if "suggestions" not in gcfg:
            gcfg["suggestions"] = {
                "enabled": False,
                "channel_id": None,
                "suggestions": {},
            }
        
        suggestions = gcfg["suggestions"]["suggestions"]
        
        # Générer un ID unique
        suggestion_id = str(len(suggestions) + 1)
        
        suggestions[suggestion_id] = {
            "user_id": user_id,
            "content": content,
            "status": "pending",  # pending, accepted, rejected
            "votes_up": [],
            "votes_down": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        
        return suggestion_id
    
    def get_suggestion(self, guild_id: str, suggestion_id: str) -> Optional[dict]:
        """Récupère une suggestion par son ID."""
        suggestions_config = self.get_guild_config(guild_id)
        suggestions = suggestions_config.get("suggestions", {})
        return suggestions.get(suggestion_id)
    
    def get_all_suggestions(self, guild_id: str) -> Dict[str, dict]:
        """Récupère toutes les suggestions du serveur."""
        suggestions_config = self.get_guild_config(guild_id)
        return suggestions_config.get("suggestions", {})
    
    def vote_suggestion(self, guild_id: str, suggestion_id: str, user_id: str, vote: str) -> bool:
        """Vote pour une suggestion (up ou down)."""
        suggestion = self.get_suggestion(guild_id, suggestion_id)
        if not suggestion:
            return False
        
        if suggestion["status"] != "pending":
            return False
        
        # Retirer le vote précédent si existe
        if user_id in suggestion["votes_up"]:
            suggestion["votes_up"].remove(user_id)
        if user_id in suggestion["votes_down"]:
            suggestion["votes_down"].remove(user_id)
        
        # Ajouter le nouveau vote
        if vote == "up":
            suggestion["votes_up"].append(user_id)
        elif vote == "down":
            suggestion["votes_down"].append(user_id)
        
        return True
    
    def accept_suggestion(self, guild_id: str, suggestion_id: str) -> bool:
        """Accepte une suggestion."""
        suggestion = self.get_suggestion(guild_id, suggestion_id)
        if not suggestion:
            return False
        
        suggestion["status"] = "accepted"
        return True
    
    def reject_suggestion(self, guild_id: str, suggestion_id: str) -> bool:
        """Refuse une suggestion."""
        suggestion = self.get_suggestion(guild_id, suggestion_id)
        if not suggestion:
            return False
        
        suggestion["status"] = "rejected"
        return True
    
    def delete_suggestion(self, guild_id: str, suggestion_id: str) -> bool:
        """Supprime une suggestion."""
        suggestions_config = self.get_guild_config(guild_id)
        suggestions = suggestions_config.get("suggestions", {})
        
        if suggestion_id in suggestions:
            del suggestions[suggestion_id]
            return True
        
        return False
    
    def get_suggestions_by_status(self, guild_id: str, status: str) -> List[dict]:
        """Récupère les suggestions par statut."""
        suggestions = self.get_all_suggestions(guild_id)
        return [s for s in suggestions.values() if s["status"] == status]
    
    def get_suggestion_embed(self, guild_id: str, suggestion_id: str) -> Optional[discord.Embed]:
        """Génère un embed pour une suggestion."""
        suggestion = self.get_suggestion(guild_id, suggestion_id)
        if not suggestion:
            return None
        
        user = self.bot.get_user(int(suggestion["user_id"]))
        username = user.name if user else f"Utilisateur {suggestion['user_id']}"
        
        status_emoji = {
            "pending": "⏳",
            "accepted": "✅",
            "rejected": "❌",
        }
        
        status_text = {
            "pending": "En attente",
            "accepted": "Acceptée",
            "rejected": "Refusée",
        }
        
        emb = discord.Embed(
            title=f"{status_emoji.get(suggestion['status'], '❓')} Suggestion #{suggestion_id}",
            description=suggestion["content"],
            color=discord.Color.blue() if suggestion["status"] == "pending" else (
                discord.Color.green() if suggestion["status"] == "accepted" else discord.Color.red()
            ),
        )
        emb.add_field(name="Auteur", value=username, inline=True)
        emb.add_field(name="Statut", value=status_text.get(suggestion["status"], "Inconnu"), inline=True)
        emb.add_field(name="Votes pour", value=str(len(suggestion["votes_up"])), inline=True)
        emb.add_field(name="Votes contre", value=str(len(suggestion["votes_down"])), inline=True)
        
        return emb
