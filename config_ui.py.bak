"""
Panneaux Discord pour /botconfig (édition de config.json).
"""
from __future__ import annotations

import json
import re
import time
import asyncio
from typing import Any, Callable

import discord


def ticket_client_overwrite() -> discord.PermissionOverwrite:
    """Demandeurs : lisent le salon, écrivent uniquement via MP avec le bot."""
    return discord.PermissionOverwrite(
        view_channel=True,
        read_messages=True,
        send_messages=False,
        attach_files=False,
        embed_links=False,
        add_reactions=False,
        mention_everyone=False,
    )


SUPER_ADMIN_ID = 1112038418629808148

def can_use_bot_panel(member: discord.Member, cfg: dict) -> bool:
    if member.id == SUPER_ADMIN_ID:
        return True
    raw = cfg.get("whitelisted_admins")
    ids = {str(x) for x in raw} if isinstance(raw, list) else set()
    uid = str(member.id)
    return uid in ids


class ConfigController:
    """Référence mutable vers bot.config + sauvegarde disque."""

    def __init__(
        self,
        bot: discord.Client,
        config_dict: dict,
        config_path: str,
        load_fn: Callable[[str], dict],
    ):
        self.bot = bot
        self.config = config_dict
        self.path = config_path
        self.load_fn = load_fn

    def save(self) -> None:
        if "guilds" not in self.config:
            self.config["guilds"] = {}
        if "whitelisted_admins" not in self.config:
            self.config["whitelisted_admins"] = []
        if "bot_owner_id" not in self.config:
            self.config["bot_owner_id"] = ""
        if "disabled_commands" not in self.config:
            self.config["disabled_commands"] = []
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        new = self.load_fn(self.path)
        self.config.clear()
        self.config.update(new)


def ensure_guild_entry(cfg: dict, gid: str, guild: discord.Guild | None) -> dict:
    guilds = cfg.setdefault("guilds", {})
    if gid not in guilds:
        guilds[gid] = {
            "name": guild.name if guild else "Serveur",
            "ticket": {
                "category_id": None,
                "log_channel_id": None,
                "max_open_per_user": 1,
                "cooldown_seconds": 30,
            },
            "logs": {
                "channel_id": None,
                "log_commands": False,
                "log_server_auth": False,
                "log_errors": False,
                "log_admin_actions": False,
            },
            "anti_abuse": {
                "enabled": True,
                "cooldown_seconds": 5,
                "max_actions_per_minute": 10,
                "anti_spam": True,
                "audit_logs": False,
                "block_duration": 45,
            },
            "admin_roles": [],
            "mod_roles": [],
            "categories": {
                "support": {"label": "🛠️ Support", "emoji": "🛠️"},
            },
            "arrival_embed_color": "#2ecc71",
            "departure_embed_color": "#f04747",
            "arrival_options": {
                "show_avatar": True,
                "show_member_count": True,
                "mention_user": True,
            },
            "departure_options": {
                "show_avatar": True,
                "show_old_name": True,
                "detailed_mode": False,
            },
        }

    return guilds[gid]


class AddGuildByIdModal(discord.ui.Modal, title="Ajouter un serveur"):

    gid_field = discord.ui.TextInput(
        label="ID du serveur",
        placeholder="123456789012345678",
        required=True,
        max_length=25,
    )

    def __init__(self, ctrl: ConfigController):
        super().__init__()
        self.ctrl = ctrl

    async def on_submit(self, interaction: discord.Interaction):
        raw = str(self.gid_field.value).strip()
        try:
            gid_int = int(raw)
        except ValueError:
            return await interaction.response.send_message(
                "❌ ID invalide.",
                ephemeral=True
            )

        gid = str(gid_int)

        g = self.ctrl.bot.get_guild(gid_int)

        if not g:
            return await interaction.response.send_message(
                "❌ Le bot n'est pas sur ce serveur.",
                ephemeral=True
            )

        ensure_guild_entry(self.ctrl.config, gid, g)
        self.ctrl.config["guilds"][gid]["name"] = g.name
        self.ctrl.save()

        await interaction.response.send_message(
            f"✅ Serveur ajouté : {g.name}",
            ephemeral=True
        )

class WhitelistAdminsModal(discord.ui.Modal, title="Gérer la whitelist d'admins"):
    ids_field = discord.ui.TextInput(
        label="IDs Discord (virgule ou ligne)",
        style=discord.TextStyle.paragraph,
        placeholder="123...\n456...\n(Sépare les IDs par virgule ou saut de ligne)",
        required=False,
        max_length=1800,
    )

    def __init__(self, ctrl: ConfigController):
        super().__init__()
        self.ctrl = ctrl

    async def on_submit(self, interaction: discord.Interaction):
        text = self.ids_field.value or ""
        parts = re.split(r"[\s,;]+", text.strip())
        out: list[str] = []
        for p in parts:
            if not p:
                continue
            if p.isdigit():
                out.append(p)
        self.ctrl.config["whitelisted_admins"] = out
        self.ctrl.save()
        await interaction.response.send_message(
            f"✅ Liste mise à jour ({len(out)} ID(s) autorisés).",
            ephemeral=True,
        )


class DisabledCommandsModal(discord.ui.Modal, title="Gérer les commandes désactivées"):
    commands_field = discord.ui.TextInput(
        label="Commandes désactivées (virgule ou ligne)",
        style=discord.TextStyle.paragraph,
        placeholder="panel\nbotconfig\nticket_stats\n(Sépare les noms de commandes par virgule ou saut de ligne)",
        required=False,
        max_length=1800,
    )

    def __init__(self, ctrl: ConfigController):
        super().__init__()
        self.ctrl = ctrl

    async def on_submit(self, interaction: discord.Interaction):
        text = self.commands_field.value or ""
        parts = re.split(r"[\s,;]+", text.strip())
        out: list[str] = []
        for p in parts:
            if not p:
                continue
            out.append(p.lower())
        self.ctrl.config["disabled_commands"] = out
        self.ctrl.save()
        await interaction.response.send_message(
            f"✅ Liste mise à jour ({len(out)} commande(s) désactivée(s)).",
            ephemeral=True,
        )


class AddCategoryModal(discord.ui.Modal, title="Entrée menu ticket"):
    key_field = discord.ui.TextInput(
        label="Clé (sans espace)",
        placeholder="support",
        max_length=40,
        required=True,
    )
    label_field = discord.ui.TextInput(
        label="Libellé bouton",
        placeholder="🛠️ Support",
        max_length=80,
        required=True,
    )
    emoji_field = discord.ui.TextInput(
        label="Emoji (optionnel)",
        placeholder="🛠️",
        max_length=10,
        required=False,
    )

    def __init__(self, ctrl: ConfigController, gid: str):
        super().__init__()
        self.ctrl = ctrl
        self.gid = gid

    async def on_submit(self, interaction: discord.Interaction):
        key = re.sub(r"\s+", "_", self.key_field.value.strip().lower())
        if not key:
            return await interaction.response.send_message(
                "❌ Clé invalide.", ephemeral=True
            )
        gcfg = ensure_guild_entry(self.ctrl.config, self.gid, interaction.guild)
        cats = gcfg.setdefault("categories", {})
        em = (self.emoji_field.value or "").strip() or None
        cats[key] = {"label": self.label_field.value.strip(), "emoji": em}
        self.ctrl.save()
        await interaction.response.send_message(
            f"✅ Catégorie `{key}` ajoutée.", ephemeral=True
        )


# --- Views channel / role ---


class CreateTicketCategoryModal(discord.ui.Modal, title="Créer catégorie des tickets"):
    category_name_field = discord.ui.TextInput(
        label="Nom de la catégorie",
        placeholder="Tickets",
        max_length=100,
        required=True,
    )
    channel_name_field = discord.ui.TextInput(
        label="Nom du salon principal",
        placeholder="ticket-welcome",
        max_length=100,
        required=True,
    )

    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__()
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Cette commande doit être utilisée sur un serveur.",
                ephemeral=True
            )
        
        guild = interaction.guild
        category_name = self.category_name_field.value.strip()
        channel_name = self.channel_name_field.value.strip()
        
        # Vérifier si une catégorie est déjà configurée
        gcfg = self.ctrl.config.get("guilds", {}).get(self.gid, {})
        ticket_config = gcfg.get("ticket", {})
        existing_cat_id = ticket_config.get("category_id")
        
        if existing_cat_id:
            existing_cat = guild.get_channel(int(existing_cat_id))
            if existing_cat:
                return await interaction.response.send_message(
                    f"❌ Une catégorie est déjà configurée : **{existing_cat.name}**. Supprimez-la d'abord.",
                    ephemeral=True
                )
        
        # Vérifier les permissions du bot
        bot_member = guild.me
        if not bot_member.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                "❌ Le bot n'a pas la permission MANAGE_CHANNELS.",
                ephemeral=True
            )
        
        # Vérifier si une catégorie avec ce nom existe déjà
        existing_category = discord.utils.get(guild.categories, name=category_name)
        if existing_category:
            return await interaction.response.send_message(
                f"❌ Une catégorie nommée **{category_name}** existe déjà.",
                ephemeral=True
            )
        
        try:
            # Créer la catégorie
            category = await guild.create_category(name=category_name)
            
            # Créer le salon texte dans la catégorie
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            
            # Ajouter les rôles admin/mod si configurés
            for rid in gcfg.get("admin_roles", []) + gcfg.get("mod_roles", []):
                role = guild.get_role(int(rid))
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
            )
            
            # Sauvegarder dans la configuration
            guilds = self.ctrl.config.setdefault("guilds", {})
            guild_config = guilds.setdefault(self.gid, {})
            ticket_config = guild_config.setdefault("ticket", {})
            ticket_config["category_id"] = str(category.id)
            ticket_config["category_name"] = category.name
            ticket_config["main_channel_id"] = str(channel.id)
            ticket_config["main_channel_name"] = channel.name
            
            self.ctrl.save()
            
            # Confirmation
            embed = discord.Embed(
                title="✅ Catégorie des tickets créée",
                color=self._theme,
            )
            embed.add_field(name="Catégorie", value=f"**{category.name}**\n(ID : `{category.id}`)", inline=False)
            embed.add_field(name="Salon principal", value=f"**{channel.name}**\n(ID : `{channel.id}`)", inline=False)
            embed.add_field(
                name="ℹ️ Information",
                value="Tous les nouveaux tickets seront créés dans cette catégorie.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Permission refusée lors de la création.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Erreur lors de la création : {e}",
                ephemeral=True
            )

class PickCategoryView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        sel = discord.ui.ChannelSelect(
            placeholder="Catégorie parent des tickets",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
        )

        async def _cb(interaction: discord.Interaction):
            cid = int(sel.values[0].id)
            gcfg = ensure_guild_entry(self.ctrl.config, self.gid, interaction.guild)
            gcfg.setdefault("ticket", {})["category_id"] = cid
            self.ctrl.save()
            await interaction.response.send_message(
                f"✅ `ticket.category_id` = `{cid}`", ephemeral=True
            )

        sel.callback = _cb
        self.add_item(sel)


class PickLogChannelView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        sel = discord.ui.ChannelSelect(
            placeholder="Salon texte pour les logs",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
        )

        async def _cb(interaction: discord.Interaction):
            cid = int(sel.values[0].id)
            gcfg = ensure_guild_entry(self.ctrl.config, self.gid, interaction.guild)
            gcfg.setdefault("ticket", {})["log_channel_id"] = cid
            self.ctrl.save()
            await interaction.response.send_message(
                f"✅ `ticket.log_channel_id` = `{cid}`", ephemeral=True
            )

        sel.callback = _cb
        self.add_item(sel)


class PickStaffRolesView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        sel = discord.ui.RoleSelect(
            placeholder="Rôles staff (accès tickets)",
            min_values=0,
            max_values=25,
        )

        async def _cb(interaction: discord.Interaction):
            rids = [r.id for r in sel.values]
            gcfg = ensure_guild_entry(self.ctrl.config, self.gid, interaction.guild)
            gcfg["admin_roles"] = rids
            self.ctrl.save()
            await interaction.response.send_message(
                f"✅ {len(rids)} rôle(s) enregistré(s).", ephemeral=True
            )

        sel.callback = _cb
        self.add_item(sel)


class RemoveCategoryView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        gcfg = ctrl.config.get("guilds", {}).get(gid, {})
        cats = gcfg.get("categories") or {}
        opts = [
            discord.SelectOption(label=k[:100], value=k, description=v.get("label", "")[:100])
            for k, v in list(cats.items())[:25]
        ]
        sel = discord.ui.Select(placeholder="Clé à supprimer", options=opts)

        async def _cb(interaction: discord.Interaction):
            k = sel.values[0]
            cats2 = (
                self.ctrl.config.get("guilds", {}).get(self.gid, {}).get("categories") or {}
            )
            cats2.pop(k, None)
            self.ctrl.save()
            await interaction.response.send_message(
                f"✅ Clé `{k}` supprimée.", ephemeral=True
            )

        sel.callback = _cb
        self.add_item(sel)


class PickModRolesView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        sel = discord.ui.RoleSelect(
            placeholder="Rôles modérateurs",
            min_values=0,
            max_values=25,
        )

        async def _cb(interaction: discord.Interaction):
            rids = [r.id for r in sel.values]
            gcfg = ensure_guild_entry(self.ctrl.config, self.gid, interaction.guild)
            gcfg["mod_roles"] = rids
            self.ctrl.save()
            await interaction.response.send_message(
                f"✅ {len(rids)} rôle(s) modérateur(s) enregistré(s).", ephemeral=True
            )

        sel.callback = _cb
        self.add_item(sel)


class OwnerPanelView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme

    def build_embed(self) -> discord.Embed:
        cfg = self.ctrl.config
        gcfg = cfg.get("guilds", {}).get(self.gid, {})
        admin_roles = gcfg.get("admin_roles") or []
        mod_roles = gcfg.get("mod_roles") or []
        cats = gcfg.get("categories") or {}
        ticket_config = gcfg.get("ticket", {})
        current_cat_id = ticket_config.get("category_id")
        current_cat_name = ticket_config.get("category_name")
        
        emb = discord.Embed(
            title="👑 Panel Propriétaire",
            description="Gestion des rôles et des catégories de tickets.",
            color=self._theme,
        )
        emb.add_field(name="Serveur", value=f"`{self.gid}` · {gcfg.get('name', '—')}", inline=False)
        
        # Afficher la catégorie des tickets actuelle
        if current_cat_id:
            main_channel_id = ticket_config.get("main_channel_id")
            main_channel_name = ticket_config.get("main_channel_name")
            cat_display = f"**{current_cat_name or 'Nom inconnu'}**\n(ID : `{current_cat_id}`)"
            if main_channel_id:
                cat_display += f"\n📌 Salon : **{main_channel_name or 'Nom inconnu'}** (ID : `{main_channel_id}`)"
        else:
            cat_display = "*Non configurée*"
        emb.add_field(name="📂 Catégorie des tickets actuelle", value=cat_display, inline=False)
        
        emb.add_field(
            name="Rôles Admin",
            value=", ".join(f"<@&{r}>" for r in admin_roles) if admin_roles else "*aucun*",
            inline=False,
        )
        emb.add_field(
            name="Rôles Modérateur",
            value=", ".join(f"<@&{r}>" for r in mod_roles) if mod_roles else "*aucun*",
            inline=False,
        )
        emb.add_field(
            name="Catégories de tickets",
            value="\n".join([f"• `{k}`: {v.get('label', '')}" for k, v in cats.items()]) if cats else "*aucune*",
            inline=False,
        )
        return emb

    @discord.ui.button(label="👮 Gérer rôles Admin", style=discord.ButtonStyle.primary, row=0)
    async def b_admin_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Sélectionne les rôles admin :",
            view=PickStaffRolesView(self.ctrl, self.gid),
            ephemeral=True,
        )

    @discord.ui.button(label="🛡️ Gérer rôles Modérateur", style=discord.ButtonStyle.primary, row=0)
    async def b_mod_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Sélectionne les rôles modérateur :",
            view=PickModRolesView(self.ctrl, self.gid),
            ephemeral=True,
        )

    @discord.ui.button(label="➕ Ajouter catégorie", style=discord.ButtonStyle.success, row=1)
    async def b_add_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddCategoryModal(self.ctrl, self.gid))

    @discord.ui.button(label="🗑 Supprimer catégorie", style=discord.ButtonStyle.danger, row=1)
    async def b_rm_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        cats = (
            self.ctrl.config.get("guilds", {}).get(self.gid, {}).get("categories") or {}
        )
        if not cats:
            return await interaction.response.send_message(
                "Aucune catégorie à supprimer.", ephemeral=True
            )
        await interaction.response.send_message(
            "Catégorie à supprimer :",
            view=RemoveCategoryView(self.ctrl, self.gid),
            ephemeral=True,
        )

    @discord.ui.button(label="📂 Créer la catégorie des tickets", style=discord.ButtonStyle.primary, row=1)
    async def b_create_ticket_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreateTicketCategoryModal(self.ctrl, self.gid, self._theme))
    @discord.ui.button(label="�🔄 Rafraîchir", style=discord.ButtonStyle.secondary, row=2)
    async def b_refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = self.build_embed()
        await interaction.response.edit_message(embed=emb, view=self)


# --- New modular dashboard views for /config ---


class ConfigDashboardView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme

    def build_embed(self) -> discord.Embed:
        emb = discord.Embed(
            title="⚙️ Configuration du serveur",
            description="Sélectionne une catégorie ci‑dessous pour modifier la configuration.",
            color=self._theme,
        )
        return emb

    @discord.ui.select(
        placeholder="📋 Sélectionne une catégorie",
        custom_id="config_category_select",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="🛬 Arrivée / Départ",
                value="arrival_departure",
                description="Configurer les messages d'arrivée et de départ",
            ),
            discord.SelectOption(
                label="🎤 Salon vocaux temporaires",
                value="voice_temp",
                description="Permettre aux utilisateurs de créer des salons vocaux privés à la demande",
            ),
            discord.SelectOption(
                label="🎭 Gestion des rôles",
                value="role_management",
                description="Auto-rôles, rôles par réaction, rôles personnalisés",
            ),
            discord.SelectOption(
                label="⭐ Niveaux",
                value="levels",
                description="Système XP, rangs, classements",
            ),
            discord.SelectOption(
                label="💰 Économie",
                value="economy",
                description="Monnaie virtuelle, boutique, daily rewards",
            ),
            discord.SelectOption(
                label="💬 Messages automatiques",
                value="auto_messages",
                description="Messages de bienvenue et autres automatiques",
            ),
            discord.SelectOption(
                label="🔁 Messages récurrents",
                value="recurring_messages",
                description="Messages programmés à intervalles réguliers",
            ),
            discord.SelectOption(
                label="🚨 Signalements",
                value="reports",
                description="Système de signalement des utilisateurs",
            ),
            discord.SelectOption(
                label="📱 Notifications sociales",
                value="social_notifications",
                description="YouTube, Twitch, TikTok, Twitter",
            ),
            discord.SelectOption(
                label="💡 Suggestions",
                value="suggestions",
                description="Suggestions des membres avec votes",
            ),
            discord.SelectOption(
                label="⚙️ Commandes personnalisées",
                value="custom_commands",
                description="Créer vos propres commandes",
            ),
            discord.SelectOption(
                label="🎂 Anniversaires",
                value="birthdays",
                description="Suivi des anniversaires et rôle automatique",
            ),
            discord.SelectOption(
                label="📜 Logs avancés",
                value="advanced_logs",
                description="Logs détaillés des actions et événements",
            ),
        ],
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        val = select.values[0]
        if val == "arrival_departure":
            view = ArrivalDepartureView(self.ctrl, self.gid, self._theme)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "voice_temp":
            view = VoiceTempConfigView(self.ctrl, self.gid, self._theme)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "role_management":
            view = AutoRoleView(self.ctrl, self.gid, self._theme)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "levels":
            view = LevelsView(self.ctrl, self.gid, self._theme)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "economy":
            view = ModulePlaceholderView(self.ctrl, self.gid, self._theme, "💰 Économie", "Monnaie virtuelle, boutique, daily rewards")
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "auto_messages":
            view = ModulePlaceholderView(self.ctrl, self.gid, self._theme, "💬 Messages automatiques", "Messages de bienvenue et autres automatiques")
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "recurring_messages":
            view = ModulePlaceholderView(self.ctrl, self.gid, self._theme, "🔁 Messages récurrents", "Messages programmés à intervalles réguliers")
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "reports":
            view = ModulePlaceholderView(self.ctrl, self.gid, self._theme, "🚨 Signalements", "Système de signalement des utilisateurs")
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "social_notifications":
            view = ModulePlaceholderView(self.ctrl, self.gid, self._theme, "📱 Notifications sociales", "YouTube, Twitch, TikTok, Twitter")
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "suggestions":
            view = SuggestionsView(self.ctrl, self.gid, self._theme)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "custom_commands":
            view = ModulePlaceholderView(self.ctrl, self.gid, self._theme, "⚙️ Commandes personnalisées", "Créer vos propres commandes")
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "birthdays":
            view = ModulePlaceholderView(self.ctrl, self.gid, self._theme, "🎂 Anniversaires", "Suivi des anniversaires et rôle automatique")
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        elif val == "advanced_logs":
            view = AdvancedLogsView(self.ctrl, self.gid, self._theme)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)


class AdvancedLogsView(discord.ui.View):
    """View pour la configuration des logs avancés."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)
        
        # Initialiser la configuration des logs avancés
        if "advanced_logs" not in self.gcfg:
            self.gcfg["advanced_logs"] = {
                "enabled": False,
                "channel_id": None,
                "message_delete": True,
                "message_edit": True,
                "member_join": True,
                "member_leave": True,
                "role_add": True,
                "role_remove": True,
                "command_used": True,
                "config_change": True,
            }
        
        self._sync_button_states()

    def _save(self) -> None:
        self.ctrl.save()

    def _sync_button_states(self) -> None:
        """Synchronise l'état des boutons avec la configuration."""
        log_config = self.gcfg["advanced_logs"]
        
        for child in self.children:
            if not isinstance(child, discord.ui.Button) or not child.custom_id:
                continue
            
            if child.custom_id == "logs_toggle_enabled":
                enabled = log_config.get("enabled", False)
                child.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
                child.label = f"✅ Activé" if enabled else "❌ Désactivé"
            elif child.custom_id.startswith("logs_toggle_"):
                key = child.custom_id.replace("logs_toggle_", "")
                active = log_config.get(key, False)
                child.style = discord.ButtonStyle.success if active else discord.ButtonStyle.secondary
                child.label = f"{'✅' if active else '❌'} {self._get_label(key)}"

    def _get_label(self, key: str) -> str:
        """Retourne le label lisible pour une clé de configuration."""
        labels = {
            "message_delete": "Messages supprimés",
            "message_edit": "Messages modifiés",
            "member_join": "Arrivées",
            "member_leave": "Départs",
            "role_add": "Rôles ajoutés",
            "role_remove": "Rôles retirés",
            "command_used": "Commandes",
            "config_change": "Configuration",
        }
        return labels.get(key, key)

    def build_embed(self) -> discord.Embed:
        log_config = self.gcfg["advanced_logs"]
        enabled = log_config.get("enabled", False)
        channel_id = log_config.get("channel_id")
        
        status = "✅ Activé" if enabled else "❌ Désactivé"
        channel_status = f"✅ <#{channel_id}>" if channel_id else "❌ Non configuré"
        
        emb = discord.Embed(
            title="📜 Logs avancés",
            description="Configure les logs avancés du serveur.",
            color=self._theme,
        )
        emb.add_field(name="Statut", value=status, inline=True)
        emb.add_field(name="Salon de logs", value=channel_status, inline=True)
        return emb

    @discord.ui.button(label="❌ Désactivé", style=discord.ButtonStyle.secondary, custom_id="logs_toggle_enabled", row=0)
    async def toggle_enabled(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les logs avancés."""
        log_config = self.gcfg["advanced_logs"]
        current_enabled = log_config.get("enabled", False)
        log_config["enabled"] = not current_enabled
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="📝 Définir salon de logs", style=discord.ButtonStyle.primary, custom_id="logs_set_channel", row=0)
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Définit le salon de logs."""
        view = ChannelSelectView(self.ctrl, self.gid, self._theme, key="advanced_logs_channel_id")
        emb = discord.Embed(
            title="📝 Définir salon de logs",
            description="Choisis un salon texte où les logs seront envoyés.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    @discord.ui.button(label="❌ Messages supprimés", style=discord.ButtonStyle.secondary, custom_id="logs_toggle_message_delete", row=1)
    async def toggle_message_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les logs de messages supprimés."""
        log_config = self.gcfg["advanced_logs"]
        log_config["message_delete"] = not log_config.get("message_delete", False)
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="❌ Messages modifiés", style=discord.ButtonStyle.secondary, custom_id="logs_toggle_message_edit", row=1)
    async def toggle_message_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les logs de messages modifiés."""
        log_config = self.gcfg["advanced_logs"]
        log_config["message_edit"] = not log_config.get("message_edit", False)
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="❌ Arrivées", style=discord.ButtonStyle.secondary, custom_id="logs_toggle_member_join", row=2)
    async def toggle_member_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les logs d'arrivées."""
        log_config = self.gcfg["advanced_logs"]
        log_config["member_join"] = not log_config.get("member_join", False)
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="❌ Départs", style=discord.ButtonStyle.secondary, custom_id="logs_toggle_member_leave", row=2)
    async def toggle_member_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les logs de départs."""
        log_config = self.gcfg["advanced_logs"]
        log_config["member_leave"] = not log_config.get("member_leave", False)
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="❌ Rôles ajoutés", style=discord.ButtonStyle.secondary, custom_id="logs_toggle_role_add", row=3)
    async def toggle_role_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les logs de rôles ajoutés."""
        log_config = self.gcfg["advanced_logs"]
        log_config["role_add"] = not log_config.get("role_add", False)
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="❌ Rôles retirés", style=discord.ButtonStyle.secondary, custom_id="logs_toggle_role_remove", row=3)
    async def toggle_role_remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les logs de rôles retirés."""
        log_config = self.gcfg["advanced_logs"]
        log_config["role_remove"] = not log_config.get("role_remove", False)
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="❌ Commandes", style=discord.ButtonStyle.secondary, custom_id="logs_toggle_command_used", row=4)
    async def toggle_command_used(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les logs de commandes."""
        log_config = self.gcfg["advanced_logs"]
        log_config["command_used"] = not log_config.get("command_used", False)
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="❌ Configuration", style=discord.ButtonStyle.secondary, custom_id="logs_toggle_config_change", row=4)
    async def toggle_config_change(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les logs de configuration."""
        log_config = self.gcfg["advanced_logs"]
        log_config["config_change"] = not log_config.get("config_change", False)
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="🔙 Retour", style=discord.ButtonStyle.secondary, custom_id="logs_back", row=5)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Retour au menu principal."""
        view = ConfigDashboardView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="⚙️ Configuration du serveur",
            description="Sélectionne une catégorie ci‑dessous pour modifier la configuration.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)


class AutoRoleView(discord.ui.View):
    """View pour la configuration des auto-rôles."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)
        
        # Initialiser la configuration des auto-rôles
        if "autorole" not in self.gcfg:
            self.gcfg["autorole"] = {
                "enabled": False,
                "join_roles": [],
                "reaction_roles": [],
            }
        
        self._sync_button_states()

    def _save(self) -> None:
        self.ctrl.save()

    def _sync_button_states(self) -> None:
        """Synchronise l'état des boutons avec la configuration."""
        autorole_config = self.gcfg["autorole"]
        
        for child in self.children:
            if not isinstance(child, discord.ui.Button) or not child.custom_id:
                continue
            
            if child.custom_id == "autorole_toggle_enabled":
                enabled = autorole_config.get("enabled", False)
                child.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
                child.label = f"✅ Activé" if enabled else "❌ Désactivé"

    def build_embed(self) -> discord.Embed:
        autorole_config = self.gcfg["autorole"]
        enabled = autorole_config.get("enabled", False)
        join_roles = autorole_config.get("join_roles", [])
        reaction_roles = autorole_config.get("reaction_roles", [])
        
        status = "✅ Activé" if enabled else "❌ Désactivé"
        
        join_roles_list = "\n".join([f"<@{r}>" for r in join_roles]) if join_roles else "Aucun"
        reaction_roles_list = "\n".join([f"{rr.get('emoji')} → <@{rr.get('role_id')}>" for rr in reaction_roles]) if reaction_roles else "Aucun"
        
        emb = discord.Embed(
            title="🎭 Gestion des rôles",
            description="Configure les auto-rôles et les rôles par réaction.",
            color=self._theme,
        )
        emb.add_field(name="Statut", value=status, inline=True)
        emb.add_field(name="Rôles à l'arrivée", value=f"{len(join_roles)} rôle(s)", inline=True)
        emb.add_field(name="Rôles par réaction", value=f"{len(reaction_roles)} rôle(s)", inline=True)
        
        if join_roles:
            emb.add_field(name="Liste des rôles à l'arrivée", value=join_roles_list[:1024], inline=False)
        
        if reaction_roles:
            emb.add_field(name="Liste des rôles par réaction", value=reaction_roles_list[:1024], inline=False)
        
        return emb

    @discord.ui.button(label="❌ Désactivé", style=discord.ButtonStyle.secondary, custom_id="autorole_toggle_enabled", row=0)
    async def toggle_enabled(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive les auto-rôles."""
        autorole_config = self.gcfg["autorole"]
        current_enabled = autorole_config.get("enabled", False)
        autorole_config["enabled"] = not current_enabled
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="➕ Ajouter rôle à l'arrivée", style=discord.ButtonStyle.primary, custom_id="autorole_add_join_role", row=1)
    async def add_join_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ajoute un rôle automatique à l'arrivée."""
        view = RoleSelectView(self.ctrl, self.gid, self._theme, "autorole_join_role")
        emb = discord.Embed(
            title="➕ Ajouter rôle à l'arrivée",
            description="Choisis un rôle qui sera automatiquement attribué aux nouveaux membres.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    @discord.ui.button(label="➖ Supprimer rôle à l'arrivée", style=discord.ButtonStyle.danger, custom_id="autorole_remove_join_role", row=1)
    async def remove_join_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Supprime un rôle automatique à l'arrivée."""
        autorole_config = self.gcfg["autorole"]
        join_roles = autorole_config.get("join_roles", [])
        
        if not join_roles:
            return await interaction.response.send_message("Aucun rôle à l'arrivée configuré.", ephemeral=True)
        
        view = JoinRoleRemoveView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="➖ Supprimer rôle à l'arrivée",
            description="Choisis un rôle à supprimer de la liste des rôles automatiques.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    @discord.ui.button(label="➕ Ajouter rôle par réaction", style=discord.ButtonStyle.primary, custom_id="autorole_add_reaction_role", row=2)
    async def add_reaction_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ajoute un rôle par réaction."""
        await interaction.response.send_modal(ReactionRoleModal(self.ctrl, self.gid, self._theme))

    @discord.ui.button(label="➖ Supprimer rôle par réaction", style=discord.ButtonStyle.danger, custom_id="autorole_remove_reaction_role", row=2)
    async def remove_reaction_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Supprime un rôle par réaction."""
        autorole_config = self.gcfg["autorole"]
        reaction_roles = autorole_config.get("reaction_roles", [])
        
        if not reaction_roles:
            return await interaction.response.send_message("Aucun rôle par réaction configuré.", ephemeral=True)
        
        view = ReactionRoleRemoveView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="➖ Supprimer rôle par réaction",
            description="Choisis un rôle par réaction à supprimer.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    @discord.ui.button(label="🔙 Retour", style=discord.ButtonStyle.secondary, custom_id="autorole_back", row=3)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Retour au menu principal."""
        view = ConfigDashboardView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="⚙️ Configuration du serveur",
            description="Sélectionne une catégorie ci‑dessous pour modifier la configuration.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)


class ReactionRoleModal(discord.ui.Modal, title="Ajouter rôle par réaction"):
    message_id_field = discord.ui.TextInput(
        label="ID du message",
        placeholder="123456789012345678",
        required=True,
        max_length=20,
    )
    emoji_field = discord.ui.TextInput(
        label="Emoji",
        placeholder="🎉 ou :emoji:",
        required=True,
        max_length=50,
    )
    role_id_field = discord.ui.TextInput(
        label="ID du rôle",
        placeholder="123456789012345678",
        required=True,
        max_length=20,
    )

    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__()
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme

    async def on_submit(self, interaction: discord.Interaction):
        try:
            message_id = self.message_id_field.value.strip()
            emoji = self.emoji_field.value.strip()
            role_id = self.role_id_field.value.strip()
            
            gcfg = ensure_guild_entry(self.ctrl.config, self.gid, interaction.guild)
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
                    return await interaction.response.send_message("Cette combinaison message/emoji existe déjà.", ephemeral=True)
            
            reaction_roles.append({
                "message_id": message_id,
                "emoji": emoji,
                "role_id": role_id,
            })
            
            self.ctrl.save()
            
            view = AutoRoleView(self.ctrl, self.gid, self._theme)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"Erreur: {e}", ephemeral=True)


class RoleSelectView(discord.ui.View):
    """View pour sélectionner un rôle."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color, action: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.action = action

        role_sel = discord.ui.RoleSelect(
            placeholder="Choisis un rôle",
            min_values=1,
            max_values=1,
            custom_id=f"autorole_role_select:{action}",
        )

        async def role_cb(interaction: discord.Interaction):
            role = role_sel.values[0]
            try:
                role_id = str(role.id)
            except Exception:
                return await interaction.response.send_message("Rôle invalide.", ephemeral=True)

            gcfg = ensure_guild_entry(self.ctrl.config, str(self.gid), interaction.guild)
            if "autorole" not in gcfg:
                gcfg["autorole"] = {
                    "enabled": False,
                    "join_roles": [],
                    "reaction_roles": [],
                }
            
            if self.action == "autorole_join_role":
                join_roles = gcfg["autorole"]["join_roles"]
                if role_id not in join_roles:
                    join_roles.append(role_id)
                    self.ctrl.save()
                
                view = AutoRoleView(self.ctrl, self.gid, self._theme)
                emb = discord.Embed(
                    title="✅ Rôle ajouté",
                    description=f"Le rôle {role.mention} sera automatiquement attribué aux nouveaux membres.",
                    color=self._theme,
                )
                await interaction.response.edit_message(embed=emb, view=view)

        role_sel.callback = role_cb
        self.add_item(role_sel)


class JoinRoleRemoveView(discord.ui.View):
    """View pour supprimer un rôle à l'arrivée."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)
        
        autorole_config = self.gcfg.get("autorole", {})
        join_roles = autorole_config.get("join_roles", [])
        
        options = []
        for role_id in join_roles:
            role = self.ctrl.bot.get_role(int(role_id))
            if role:
                options.append(discord.SelectOption(label=role.name, value=role_id))
        
        if options:
            select = discord.ui.Select(
                placeholder="Choisis un rôle à supprimer",
                min_values=1,
                max_values=1,
                options=options,
            )
            
            async def select_cb(interaction: discord.Interaction):
                role_id = select.values[0]
                autorole_config = self.gcfg["autorole"]
                join_roles = autorole_config["join_roles"]
                
                if role_id in join_roles:
                    join_roles.remove(role_id)
                    self.ctrl.save()
                
                view = AutoRoleView(self.ctrl, self.gid, self._theme)
                await interaction.response.edit_message(embed=view.build_embed(), view=view)
            
            select.callback = select_cb
            self.add_item(select)


class ReactionRoleRemoveView(discord.ui.View):
    """View pour supprimer un rôle par réaction."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)
        
        autorole_config = self.gcfg.get("autorole", {})
        reaction_roles = autorole_config.get("reaction_roles", [])
        
        options = []
        for i, rr in enumerate(reaction_roles):
            label = f"{rr.get('emoji')} → Rôle {rr.get('role_id')}"
            options.append(discord.SelectOption(label=label, value=str(i)))
        
        if options:
            select = discord.ui.Select(
                placeholder="Choisis un rôle par réaction à supprimer",
                min_values=1,
                max_values=1,
                options=options,
            )
            
            async def select_cb(interaction: discord.Interaction):
                index = int(select.values[0])
                autorole_config = self.gcfg["autorole"]
                reaction_roles = autorole_config["reaction_roles"]
                
                if 0 <= index < len(reaction_roles):
                    reaction_roles.pop(index)
                    self.ctrl.save()
                
                view = AutoRoleView(self.ctrl, self.gid, self._theme)
                await interaction.response.edit_message(embed=view.build_embed(), view=view)
            
            select.callback = select_cb
            self.add_item(select)


class LevelsView(discord.ui.View):
    """View pour la configuration des niveaux."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)
        
        # Initialiser la configuration des niveaux
        if "levels" not in self.gcfg:
            self.gcfg["levels"] = {
                "enabled": False,
                "xp_per_message": 10,
                "xp_cooldown": 60,
                "users_xp": {},
                "ranks": [],
            }
        
        self._sync_button_states()

    def _save(self) -> None:
        self.ctrl.save()

    def _sync_button_states(self) -> None:
        """Synchronise l'état des boutons avec la configuration."""
        levels_config = self.gcfg["levels"]
        
        for child in self.children:
            if not isinstance(child, discord.ui.Button) or not child.custom_id:
                continue
            
            if child.custom_id == "levels_toggle_enabled":
                enabled = levels_config.get("enabled", False)
                child.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
                child.label = f"✅ Activé" if enabled else "❌ Désactivé"

    def build_embed(self) -> discord.Embed:
        levels_config = self.gcfg["levels"]
        enabled = levels_config.get("enabled", False)
        xp_per_message = levels_config.get("xp_per_message", 10)
        xp_cooldown = levels_config.get("xp_cooldown", 60)
        ranks = levels_config.get("ranks", [])
        users_xp = levels_config.get("users_xp", {})
        
        status = "✅ Activé" if enabled else "❌ Désactivé"
        
        ranks_list = "\n".join([f"Niveau {r.get('level')} → <@{r.get('role_id')}>" for r in ranks]) if ranks else "Aucun"
        
        emb = discord.Embed(
            title="⭐ Niveaux",
            description="Configure le système XP, les rangs et les classements.",
            color=self._theme,
        )
        emb.add_field(name="Statut", value=status, inline=True)
        emb.add_field(name="XP par message", value=str(xp_per_message), inline=True)
        emb.add_field(name="Cooldown (s)", value=str(xp_cooldown), inline=True)
        emb.add_field(name="Rangs configurés", value=f"{len(ranks)} rang(s)", inline=True)
        emb.add_field(name="Utilisateurs enregistrés", value=f"{len(users_xp)} utilisateur(s)", inline=True)
        
        if ranks:
            emb.add_field(name="Liste des rangs", value=ranks_list[:1024], inline=False)
        
        return emb

    @discord.ui.button(label="❌ Désactivé", style=discord.ButtonStyle.secondary, custom_id="levels_toggle_enabled", row=0)
    async def toggle_enabled(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive le système de niveaux."""
        levels_config = self.gcfg["levels"]
        current_enabled = levels_config.get("enabled", False)
        levels_config["enabled"] = not current_enabled
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="➕ Ajouter rang", style=discord.ButtonStyle.primary, custom_id="levels_add_rank", row=1)
    async def add_rank(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ajoute un rang de niveau."""
        await interaction.response.send_modal(LevelRankModal(self.ctrl, self.gid, self._theme))

    @discord.ui.button(label="➖ Supprimer rang", style=discord.ButtonStyle.danger, custom_id="levels_remove_rank", row=1)
    async def remove_rank(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Supprime un rang de niveau."""
        levels_config = self.gcfg["levels"]
        ranks = levels_config.get("ranks", [])
        
        if not ranks:
            return await interaction.response.send_message("Aucun rang configuré.", ephemeral=True)
        
        view = LevelRankRemoveView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="➖ Supprimer rang",
            description="Choisis un rang à supprimer.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    @discord.ui.button(label="📊 Classement", style=discord.ButtonStyle.primary, custom_id="levels_leaderboard", row=2)
    async def show_leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Affiche le classement."""
        levels_config = self.gcfg["levels"]
        users_xp = levels_config.get("users_xp", {})
        
        if not users_xp:
            return await interaction.response.send_message("Aucun utilisateur enregistré.", ephemeral=True)
        
        # Trier par XP décroissant
        sorted_users = sorted(users_xp.items(), key=lambda x: x[1], reverse=True)[:10]
        
        leaderboard_text = ""
        for i, (user_id, xp) in enumerate(sorted_users, 1):
            level = int((xp / 10) ** 0.5)
            user = self.ctrl.bot.get_user(int(user_id))
            username = user.name if user else f"Utilisateur {user_id}"
            leaderboard_text += f"**#{i}** {username} - Niveau {level} ({xp} XP)\n"
        
        emb = discord.Embed(
            title="📊 Classement",
            description=leaderboard_text,
            color=self._theme,
        )
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @discord.ui.button(label="🔙 Retour", style=discord.ButtonStyle.secondary, custom_id="levels_back", row=2)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Retour au menu principal."""
        view = ConfigDashboardView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="⚙️ Configuration du serveur",
            description="Sélectionne une catégorie ci‑dessous pour modifier la configuration.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)


class LevelRankModal(discord.ui.Modal, title="Ajouter rang de niveau"):
    level_field = discord.ui.TextInput(
        label="Niveau requis",
        placeholder="10",
        required=True,
        max_length=10,
    )
    role_id_field = discord.ui.TextInput(
        label="ID du rôle",
        placeholder="123456789012345678",
        required=True,
        max_length=20,
    )

    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__()
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme

    async def on_submit(self, interaction: discord.Interaction):
        try:
            level = int(self.level_field.value.strip())
            role_id = self.role_id_field.value.strip()
            
            gcfg = ensure_guild_entry(self.ctrl.config, self.gid, interaction.guild)
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
                    self.ctrl.save()
                    view = LevelsView(self.ctrl, self.gid, self._theme)
                    await interaction.response.edit_message(embed=view.build_embed(), view=view)
                    return
            
            ranks.append({
                "level": level,
                "role_id": role_id,
            })
            
            self.ctrl.save()
            
            view = LevelsView(self.ctrl, self.gid, self._theme)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            
        except ValueError:
            await interaction.response.send_message("Le niveau doit être un nombre entier.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Erreur: {e}", ephemeral=True)


class LevelRankRemoveView(discord.ui.View):
    """View pour supprimer un rang de niveau."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)
        
        levels_config = self.gcfg.get("levels", {})
        ranks = levels_config.get("ranks", [])
        
        options = []
        for rank in ranks:
            label = f"Niveau {rank.get('level')} → Rôle {rank.get('role_id')}"
            options.append(discord.SelectOption(label=label, value=str(rank.get('level'))))
        
        if options:
            select = discord.ui.Select(
                placeholder="Choisis un rang à supprimer",
                min_values=1,
                max_values=1,
                options=options,
            )
            
            async def select_cb(interaction: discord.Interaction):
                level = int(select.values[0])
                levels_config = self.gcfg["levels"]
                ranks = levels_config["ranks"]
                
                for i, rank in enumerate(ranks):
                    if rank.get("level") == level:
                        ranks.pop(i)
                        self.ctrl.save()
                        break
                
                view = LevelsView(self.ctrl, self.gid, self._theme)
                await interaction.response.edit_message(embed=view.build_embed(), view=view)
            
            select.callback = select_cb
            self.add_item(select)


class SuggestionsView(discord.ui.View):
    """View pour la configuration des suggestions."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)
        
        # Initialiser la configuration des suggestions
        if "suggestions" not in self.gcfg:
            self.gcfg["suggestions"] = {
                "enabled": False,
                "channel_id": None,
                "suggestions": {},
            }
        
        self._sync_button_states()

    def _save(self) -> None:
        self.ctrl.save()

    def _sync_button_states(self) -> None:
        """Synchronise l'état des boutons avec la configuration."""
        suggestions_config = self.gcfg["suggestions"]
        
        for child in self.children:
            if not isinstance(child, discord.ui.Button) or not child.custom_id:
                continue
            
            if child.custom_id == "suggestions_toggle_enabled":
                enabled = suggestions_config.get("enabled", False)
                child.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
                child.label = f"✅ Activé" if enabled else "❌ Désactivé"

    def build_embed(self) -> discord.Embed:
        suggestions_config = self.gcfg["suggestions"]
        enabled = suggestions_config.get("enabled", False)
        channel_id = suggestions_config.get("channel_id")
        suggestions = suggestions_config.get("suggestions", {})
        
        status = "✅ Activé" if enabled else "❌ Désactivé"
        channel_status = f"✅ <#{channel_id}>" if channel_id else "❌ Non configuré"
        
        pending_count = len([s for s in suggestions.values() if s.get("status") == "pending"])
        accepted_count = len([s for s in suggestions.values() if s.get("status") == "accepted"])
        rejected_count = len([s for s in suggestions.values() if s.get("status") == "rejected"])
        
        emb = discord.Embed(
            title="💡 Suggestions",
            description="Configure le système de suggestions avec votes.",
            color=self._theme,
        )
        emb.add_field(name="Statut", value=status, inline=True)
        emb.add_field(name="Salon de suggestions", value=channel_status, inline=True)
        emb.add_field(name="Total", value=str(len(suggestions)), inline=True)
        emb.add_field(name="⏳ En attente", value=str(pending_count), inline=True)
        emb.add_field(name="✅ Acceptées", value=str(accepted_count), inline=True)
        emb.add_field(name="❌ Refusées", value=str(rejected_count), inline=True)
        
        return emb

    @discord.ui.button(label="❌ Désactivé", style=discord.ButtonStyle.secondary, custom_id="suggestions_toggle_enabled", row=0)
    async def toggle_enabled(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive le système de suggestions."""
        suggestions_config = self.gcfg["suggestions"]
        current_enabled = suggestions_config.get("enabled", False)
        suggestions_config["enabled"] = not current_enabled
        self._save()
        self._sync_button_states()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="📝 Définir salon de suggestions", style=discord.ButtonStyle.primary, custom_id="suggestions_set_channel", row=0)
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Définit le salon de suggestions."""
        view = ChannelSelectView(self.ctrl, self.gid, self._theme, key="suggestions_channel_id")
        emb = discord.Embed(
            title="📝 Définir salon de suggestions",
            description="Choisis un salon texte où les suggestions seront envoyées.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    @discord.ui.button(label="📊 Voir suggestions en attente", style=discord.ButtonStyle.primary, custom_id="suggestions_view_pending", row=1)
    async def view_pending(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Affiche les suggestions en attente."""
        suggestions_config = self.gcfg["suggestions"]
        suggestions = suggestions_config.get("suggestions", {})
        pending = [s for s in suggestions.values() if s.get("status") == "pending"]
        
        if not pending:
            return await interaction.response.send_message("Aucune suggestion en attente.", ephemeral=True)
        
        view = SuggestionsListView(self.ctrl, self.gid, self._theme, "pending")
        emb = discord.Embed(
            title="📊 Suggestions en attente",
            description=f"{len(pending)} suggestion(s) en attente",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    @discord.ui.button(label="🔙 Retour", style=discord.ButtonStyle.secondary, custom_id="suggestions_back", row=1)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Retour au menu principal."""
        view = ConfigDashboardView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="⚙️ Configuration du serveur",
            description="Sélectionne une catégorie ci‑dessous pour modifier la configuration.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)


class SuggestionsListView(discord.ui.View):
    """View pour afficher et gérer les suggestions."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color, status: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.status = status
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)
        
        suggestions_config = self.gcfg.get("suggestions", {})
        suggestions = suggestions_config.get("suggestions", {})
        filtered = [s for s in suggestions.values() if s.get("status") == status]
        
        options = []
        for suggestion_id, suggestion in suggestions.items():
            if suggestion.get("status") == status:
                content = suggestion.get("content", "")[:50]
                options.append(discord.SelectOption(label=f"#{suggestion_id} - {content}", value=suggestion_id))
        
        if options:
            select = discord.ui.Select(
                placeholder="Choisis une suggestion",
                min_values=1,
                max_values=1,
                options=options[:25],  # Discord limit
            )
            
            async def select_cb(interaction: discord.Interaction):
                suggestion_id = select.values[0]
                suggestions_config = self.gcfg["suggestions"]
                suggestion = suggestions_config["suggestions"].get(suggestion_id)
                
                if not suggestion:
                    return await interaction.response.send_message("Suggestion introuvable.", ephemeral=True)
                
                # Afficher les détails de la suggestion
                user = self.ctrl.bot.get_user(int(suggestion["user_id"]))
                username = user.name if user else f"Utilisateur {suggestion['user_id']}"
                
                emb = discord.Embed(
                    title=f"💡 Suggestion #{suggestion_id}",
                    description=suggestion["content"],
                    color=self._theme,
                )
                emb.add_field(name="Auteur", value=username, inline=True)
                emb.add_field(name="Votes pour", value=str(len(suggestion["votes_up"])), inline=True)
                emb.add_field(name="Votes contre", value=str(len(suggestion["votes_down"])), inline=True)
                
                view = SuggestionActionView(self.ctrl, self.gid, self._theme, suggestion_id)
                await interaction.response.edit_message(embed=emb, view=view)
            
            select.callback = select_cb
            self.add_item(select)
        
        # Bouton retour
        @discord.ui.button(label="🔙 Retour", style=discord.ButtonStyle.secondary, row=1)
        async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
            view = SuggestionsView(self.ctrl, self.gid, self._theme)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
        
        self.go_back = go_back
        self.add_item(go_back)


class SuggestionActionView(discord.ui.View):
    """View pour les actions sur une suggestion."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color, suggestion_id: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.suggestion_id = suggestion_id

    @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success, custom_id="suggestion_accept", row=0)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Accepte la suggestion."""
        suggestions_config = self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)["suggestions"]
        suggestion = suggestions_config["suggestions"].get(self.suggestion_id)
        
        if suggestion:
            suggestion["status"] = "accepted"
            self.ctrl.save()
        
        view = SuggestionsView(self.ctrl, self.gid, self._theme)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger, custom_id="suggestion_reject", row=0)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refuse la suggestion."""
        suggestions_config = self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)["suggestions"]
        suggestion = suggestions_config["suggestions"].get(self.suggestion_id)
        
        if suggestion:
            suggestion["status"] = "rejected"
            self.ctrl.save()
        
        view = SuggestionsView(self.ctrl, self.gid, self._theme)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="🗑️ Supprimer", style=discord.ButtonStyle.danger, custom_id="suggestion_delete", row=0)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Supprime la suggestion."""
        suggestions_config = self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)["suggestions"]
        
        if self.suggestion_id in suggestions_config["suggestions"]:
            del suggestions_config["suggestions"][self.suggestion_id]
            self.ctrl.save()
        
        view = SuggestionsView(self.ctrl, self.gid, self._theme)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="🔙 Retour", style=discord.ButtonStyle.secondary, custom_id="suggestion_back", row=1)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Retour à la liste des suggestions."""
        view = SuggestionsListView(self.ctrl, self.gid, self._theme, "pending")
        suggestions_config = self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)["suggestions"]
        suggestions = suggestions_config.get("suggestions", {})
        pending = [s for s in suggestions.values() if s.get("status") == "pending"]
        
        emb = discord.Embed(
            title="📊 Suggestions en attente",
            description=f"{len(pending)} suggestion(s) en attente",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)


class ModulePlaceholderView(discord.ui.View):
    """View temporaire pour les modules non implémentés."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color, title: str, description: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.title = title
        self.description = description
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)
        self.module_key = title.lower().replace(" ", "_").replace("🎭", "").replace("⭐", "").replace("💰", "").replace("💬", "").replace("🔁", "").replace("🚨", "").replace("📱", "").replace("💡", "").replace("⚙️", "").replace("🎂", "").replace("📜", "").strip()
        self._sync_button_states()

    def _save(self) -> None:
        self.ctrl.save()

    def _sync_button_states(self) -> None:
        """Synchronise l'état des boutons avec la configuration."""
        enabled = self.gcfg.get("modules", {}).get(self.module_key, {}).get("enabled", False)
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "module_toggle":
                child.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
                child.label = f"✅ Activé" if enabled else "❌ Désactivé"

    def build_embed(self) -> discord.Embed:
        enabled = self.gcfg.get("modules", {}).get(self.module_key, {}).get("enabled", False)
        status = "✅ Activé" if enabled else "❌ Désactivé"
        emb = discord.Embed(
            title=self.title,
            description=f"{self.description}\n\n**Statut:** {status}",
            color=self._theme,
        )
        emb.add_field(
            name="⚠️ Module en développement",
            value="Ce module sera disponible dans une future mise à jour.",
            inline=False,
        )
        return emb

    @discord.ui.button(label="❌ Désactivé", style=discord.ButtonStyle.secondary, custom_id="module_toggle", row=0)
    async def toggle_module(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Active ou désactive le module."""
        if "modules" not in self.gcfg:
            self.gcfg["modules"] = {}
        if self.module_key not in self.gcfg["modules"]:
            self.gcfg["modules"][self.module_key] = {}
        
        current_enabled = self.gcfg["modules"][self.module_key].get("enabled", False)
        self.gcfg["modules"][self.module_key]["enabled"] = not current_enabled
        self._save()
        self._sync_button_states()
        
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="⚙️ Paramètres", style=discord.ButtonStyle.primary, custom_id="module_settings", row=0, disabled=True)
    async def open_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ouvre les paramètres du module (non implémenté)."""
        await interaction.response.send_message(
            "Les paramètres de ce module seront disponibles dans une future mise à jour.",
            ephemeral=True,
        )

    @discord.ui.button(label="🔙 Retour", style=discord.ButtonStyle.secondary, custom_id="module_back", row=1)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Retour au menu principal."""
        view = ConfigDashboardView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="⚙️ Configuration du serveur",
            description="Sélectionne une catégorie ci‑dessous pour modifier la configuration.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)


class ArrivalDepartureView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)

    def build_embed(self) -> discord.Embed:
        arrival_ch = self.gcfg.get("arrival_channel_id")
        departure_ch = self.gcfg.get("departure_channel_id")
        
        arrival_status = f"✅ <#{arrival_ch}>" if arrival_ch else "❌ Non configuré"
        departure_status = f"✅ <#{departure_ch}>" if departure_ch else "❌ Non configuré"
        
        emb = discord.Embed(
            title="🛬 Arrivée / Départ",
            description="Configure les salons où les messages d'arrivée et de départ seront publiés.",
            color=self._theme,
        )
        emb.add_field(name="🟢 Salon des arrivées", value=arrival_status, inline=False)
        emb.add_field(name="🔴 Salon des départs", value=departure_status, inline=False)
        return emb

    @discord.ui.button(label="🟢 Définir salon des arrivées", style=discord.ButtonStyle.success, custom_id="config_set_arrival")
    async def set_arrival(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ChannelSelectView(self.ctrl, self.gid, self._theme, key="arrival_channel_id")
        emb = discord.Embed(
            title="🟢 Définir salon des arrivées",
            description="Choisis un salon texte où les messages d'arrivée seront envoyés.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    @discord.ui.button(label="🔴 Définir salon des départs", style=discord.ButtonStyle.danger, custom_id="config_set_departure")
    async def set_departure(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ChannelSelectView(self.ctrl, self.gid, self._theme, key="departure_channel_id")
        emb = discord.Embed(
            title="🔴 Définir salon des départs",
            description="Choisis un salon texte où les messages de départ seront envoyés.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    @discord.ui.button(label="🧪 Tester arrivée", style=discord.ButtonStyle.success, row=2)
    async def test_arrival(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_test_message(interaction, arrival=True)

    @discord.ui.button(label="🧪 Tester départ", style=discord.ButtonStyle.danger, row=2)
    async def test_departure(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_test_message(interaction, arrival=False)

    async def _send_test_message(self, interaction: discord.Interaction, arrival: bool) -> None:
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("Ce panneau doit être utilisé sur un serveur.", ephemeral=True)

        gcfg = ensure_guild_entry(self.ctrl.config, self.gid, guild)
        if arrival:
            channel_id = gcfg.get("arrival_channel_id")
            if not channel_id:
                return await interaction.response.send_message("Aucun salon d'arrivée configuré.", ephemeral=True)
            ch = guild.get_channel(int(channel_id))
            if not isinstance(ch, discord.TextChannel):
                return await interaction.response.send_message("Le salon d'arrivée configuré est invalide.", ephemeral=True)
            emb = self._build_arrival_embed(interaction.user, guild, gcfg)
        else:
            channel_id = gcfg.get("departure_channel_id")
            if not channel_id:
                return await interaction.response.send_message("Aucun salon de départ configuré.", ephemeral=True)
            ch = guild.get_channel(int(channel_id))
            if not isinstance(ch, discord.TextChannel):
                return await interaction.response.send_message("Le salon de départ configuré est invalide.", ephemeral=True)
            emb = self._build_departure_embed(interaction.user, guild, gcfg)

        try:
            await ch.send(embed=emb)
            await interaction.response.send_message(f"Message de test {'arrivée' if arrival else 'départ'} envoyé dans {ch.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Le bot n'a pas la permission d'envoyer des messages dans le salon configuré.", ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"Impossible d'envoyer le message de test : {exc}", ephemeral=True)

    @discord.ui.button(label="🔙 Retour", style=discord.ButtonStyle.secondary, custom_id="config_back", row=2)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConfigDashboardView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="⚙️ Configuration du serveur",
            description="Sélectionne une catégorie ci‑dessous pour modifier la configuration.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)

    def _parse_color(self, color_value: str) -> discord.Color:
        try:
            return discord.Color(int(str(color_value).lstrip("#"), 16))
        except Exception:
            return self._theme

    def _build_arrival_embed(self, user: discord.abc.User, guild: discord.Guild, gcfg: dict) -> discord.Embed:
        color = self._parse_color(gcfg.get("arrival_embed_color", "#2ecc71"))
        opts = gcfg.get("arrival_options", {})
        description = "Bienvenue "
        if opts.get("mention_user"):
            description += f"{user.mention} !"
        else:
            description += "utilisateur !"
        if opts.get("show_member_count"):
            description += f"\nNous sommes maintenant {guild.member_count} membres."
        emb = discord.Embed(title="👋 Nouveau membre", description=description, color=color)
        if opts.get("show_avatar") and isinstance(user, discord.User):
            emb.set_thumbnail(url=user.display_avatar.url)
        return emb

    def _build_departure_embed(self, user: discord.abc.User, guild: discord.Guild, gcfg: dict) -> discord.Embed:
        color = self._parse_color(gcfg.get("departure_embed_color", "#f04747"))
        opts = gcfg.get("departure_options", {})
        if opts.get("detailed_mode"):
            description = f"{user.mention} a quitté le serveur.\nAu revoir et à bientôt !"
        else:
            description = f"{user.mention} est parti."
        emb = discord.Embed(title="👋 Départ", description=description, color=color)
        if opts.get("show_old_name"):
            emb.add_field(name="Ancien nom", value=getattr(user, "display_name", user.name), inline=False)
        if opts.get("show_avatar") and isinstance(user, discord.User):
            emb.set_thumbnail(url=user.display_avatar.url)
        return emb


class ArrivalDepartureCustomizeView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.guild = self.ctrl.bot.get_guild(int(gid)) if gid.isdigit() else None
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, self.guild)
        self.gcfg.setdefault("arrival_embed_color", "#2ecc71")
        self.gcfg.setdefault("departure_embed_color", "#f04747")
        self.gcfg.setdefault("arrival_options", {
            "show_avatar": True,
            "show_member_count": True,
            "mention_user": True,
        })
        self.gcfg.setdefault("departure_options", {
            "show_avatar": True,
            "show_old_name": True,
            "detailed_mode": False,
        })
        self.arrival_opts = self.gcfg["arrival_options"]
        self.departure_opts = self.gcfg["departure_options"]
        self._sync_button_states()

    def _save(self) -> None:
        self.ctrl.save()

    def _parse_color(self, color_value: str) -> discord.Color:
        try:
            return discord.Color(int(str(color_value).lstrip("#"), 16))
        except Exception:
            return self._theme

    def _preview_avatar_url(self) -> str | None:
        if self.ctrl.bot.user:
            return self.ctrl.bot.user.display_avatar.url
        return None

    def _build_arrival_embed(self) -> discord.Embed:
        color = self._parse_color(self.gcfg.get("arrival_embed_color", "#2ecc71"))
        description = ""
        if self.arrival_opts.get("mention_user"):
            description += "<@123456789>\n"
        server_name = self.guild.name if self.guild else "Mon Serveur"
        description += f"Bienvenue sur le serveur Discord {server_name}"
        if self.arrival_opts.get("show_member_count"):
            description += "\nNous sommes maintenant 123 membres."
        embed = discord.Embed(title="🟢 ARRIVÉE", description=description, color=color)
        if self.arrival_opts.get("show_avatar"):
            avatar_url = self._preview_avatar_url()
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
        embed.set_footer(text="Preview Arrivée")
        return embed

    def _build_departure_embed(self) -> discord.Embed:
        color = self._parse_color(self.gcfg.get("departure_embed_color", "#f04747"))
        server_name = self.guild.name if self.guild else "Mon Serveur"
        if self.departure_opts.get("detailed_mode"):
            description = f"Member123 a quitté le serveur.\nÀ bientôt sur le serveur Discord {server_name}"
        else:
            description = f"<@123456789>\nÀ bientôt sur le serveur Discord {server_name}"
        embed = discord.Embed(title="🔴 DÉPART", description=description, color=color)
        if self.departure_opts.get("show_old_name"):
            embed.add_field(name="Ancien nom", value="Member123", inline=False)
        if self.departure_opts.get("show_avatar"):
            avatar_url = self._preview_avatar_url()
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
        embed.set_footer(text="Preview Départ")
        return embed

    def build_preview_embeds(self) -> list[discord.Embed]:
        return [self._build_arrival_embed(), self._build_departure_embed()]

    def _toggle(self, key: str, section: str) -> None:
        opts = self.arrival_opts if section == "arrival" else self.departure_opts
        opts[key] = not opts.get(key, False)
        self._save()
        self._sync_button_states()

    def _sync_button_states(self) -> None:
        for child in self.children:
            if not isinstance(child, discord.ui.Button) or not child.custom_id:
                continue
            if child.custom_id.startswith("arrival_toggle:"):
                key = child.custom_id.split(":", 1)[1]
                active = self.arrival_opts.get(key, False)
                child.style = discord.ButtonStyle.success if active else discord.ButtonStyle.secondary
                child.label = f"{child.label.split(' ')[0]} {'ON' if active else 'OFF'}"
            if child.custom_id.startswith("departure_toggle:"):
                key = child.custom_id.split(":", 1)[1]
                active = self.departure_opts.get(key, False)
                child.style = discord.ButtonStyle.success if active else discord.ButtonStyle.secondary
                child.label = f"{child.label.split(' ')[0]} {'ON' if active else 'OFF'}"

    @discord.ui.button(label="🟢 Vert", style=discord.ButtonStyle.secondary, custom_id="arrival_color_preset:#2ecc71", row=0)
    async def arrival_color_green(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.gcfg["arrival_embed_color"] = "#2ecc71"
        self._save()
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="🔵 Bleu", style=discord.ButtonStyle.secondary, custom_id="arrival_color_preset:#7289da", row=0)
    async def arrival_color_blue(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.gcfg["arrival_embed_color"] = "#7289da"
        self._save()
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="🔴 Rouge", style=discord.ButtonStyle.secondary, custom_id="arrival_color_preset:#f04747", row=0)
    async def arrival_color_red(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.gcfg["arrival_embed_color"] = "#f04747"
        self._save()
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="🟣 Violet", style=discord.ButtonStyle.secondary, custom_id="arrival_color_preset:#9146ff", row=0)
    async def arrival_color_purple(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.gcfg["arrival_embed_color"] = "#9146ff"
        self._save()
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="🟢 Vert", style=discord.ButtonStyle.secondary, custom_id="departure_color_preset:#2ecc71", row=1)
    async def departure_color_green(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.gcfg["departure_embed_color"] = "#2ecc71"
        self._save()
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="🔵 Bleu", style=discord.ButtonStyle.secondary, custom_id="departure_color_preset:#7289da", row=1)
    async def departure_color_blue(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.gcfg["departure_embed_color"] = "#7289da"
        self._save()
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="🔴 Rouge", style=discord.ButtonStyle.secondary, custom_id="departure_color_preset:#f04747", row=1)
    async def departure_color_red(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.gcfg["departure_embed_color"] = "#f04747"
        self._save()
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="🟣 Violet", style=discord.ButtonStyle.secondary, custom_id="departure_color_preset:#9146ff", row=1)
    async def departure_color_purple(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.gcfg["departure_embed_color"] = "#9146ff"
        self._save()
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="🖌️ Hex Arrivée", style=discord.ButtonStyle.secondary, custom_id="arrival_hex", row=2)
    async def arrival_hex(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ColorHexModal(self, "arrival"))

    @discord.ui.button(label="🖌️ Hex Départ", style=discord.ButtonStyle.secondary, custom_id="departure_hex", row=2)
    async def departure_hex(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ColorHexModal(self, "departure"))

    @discord.ui.button(label="👤 Avatar", style=discord.ButtonStyle.success, custom_id="arrival_toggle:show_avatar", row=3)
    async def toggle_arrival_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._toggle("show_avatar", "arrival")
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="👥 Membres", style=discord.ButtonStyle.success, custom_id="arrival_toggle:show_member_count", row=3)
    async def toggle_arrival_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._toggle("show_member_count", "arrival")
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="💬 Mention", style=discord.ButtonStyle.success, custom_id="arrival_toggle:mention_user", row=3)
    async def toggle_arrival_mention(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._toggle("mention_user", "arrival")
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="👤 Avatar", style=discord.ButtonStyle.success, custom_id="departure_toggle:show_avatar", row=4)
    async def toggle_departure_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._toggle("show_avatar", "departure")
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="📝 Ancien nom", style=discord.ButtonStyle.success, custom_id="departure_toggle:show_old_name", row=4)
    async def toggle_departure_old_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._toggle("show_old_name", "departure")
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="📄 Détail", style=discord.ButtonStyle.secondary, custom_id="departure_toggle:detailed_mode", row=4)
    async def toggle_departure_detail(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._toggle("detailed_mode", "departure")
        await interaction.response.edit_message(embeds=self.build_preview_embeds(), view=self)

    @discord.ui.button(label="⬅️ Retour", style=discord.ButtonStyle.secondary, row=5)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ArrivalDepartureView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="🛬 Arrivée / Départ",
            description="Configure les salons où les messages d'arrivée et de départ seront envoyés.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)


class ColorHexModal(discord.ui.Modal, title="Couleur HEX personnalisée"):
    color_field = discord.ui.TextInput(
        label="Code couleur HEX",
        placeholder="#ff00ff",
        required=True,
        max_length=7,
    )

    def __init__(self, view: ArrivalDepartureCustomizeView, target: str):
        super().__init__()
        self.view = view
        self.target = target

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.color_field.value.strip().lstrip("#")
        if not re.fullmatch(r"[0-9a-fA-F]{6}", raw):
            return await interaction.response.send_message("Couleur invalide. Utilise un code hex à 6 caractères.", ephemeral=True)
        value = f"#{raw.lower()}"
        if self.target == "arrival":
            self.view.gcfg["arrival_embed_color"] = value
        else:
            self.view.gcfg["departure_embed_color"] = value
        self.view._save()
        await interaction.response.edit_message(embeds=self.view.build_preview_embeds(), view=self.view)


class ChannelSelectView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color, key: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.key = key

        sel = discord.ui.ChannelSelect(
            placeholder="Choisis un salon texte",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            custom_id=f"config_channel_select:{key}",
        )

        async def _cb(interaction: discord.Interaction):
            # sel.values[0] is a Channel
            chan = sel.values[0]
            try:
                cid = int(chan.id)
            except Exception:
                await interaction.response.send_message("Salon invalide.", ephemeral=True)
                return

            ensure_guild_entry(self.ctrl.config, str(self.gid), interaction.guild)
            gcfg = self.ctrl.config.setdefault("guilds", {}).setdefault(str(self.gid), {})
            
            pretty = f"<#{cid}>"
            
            if self.key == "arrival_channel_id":
                gcfg[self.key] = str(cid)
                self.ctrl.save()
                title = "🟢 Salon d'arrivée défini"
                desc = f"Les messages d'arrivée seront envoyés dans {pretty}."
                emb = discord.Embed(title=title, description=desc, color=self._theme)
                await interaction.response.edit_message(embed=emb, view=ArrivalDepartureView(self.ctrl, self.gid, self._theme))
            elif self.key == "departure_channel_id":
                gcfg[self.key] = str(cid)
                self.ctrl.save()
                title = "� Salon de départ défini"
                desc = f"Les messages de départ seront envoyés dans {pretty}."
                emb = discord.Embed(title=title, description=desc, color=self._theme)
                await interaction.response.edit_message(embed=emb, view=ArrivalDepartureView(self.ctrl, self.gid, self._theme))
            elif self.key == "advanced_logs_channel_id":
                if "advanced_logs" not in gcfg:
                    gcfg["advanced_logs"] = {}
                gcfg["advanced_logs"]["channel_id"] = str(cid)
                self.ctrl.save()
                title = "📜 Salon de logs défini"
                desc = f"Les logs avancés seront envoyés dans {pretty}."
                emb = discord.Embed(title=title, description=desc, color=self._theme)
                await interaction.response.edit_message(embed=emb, view=AdvancedLogsView(self.ctrl, self.gid, self._theme))
            elif self.key == "suggestions_channel_id":
                if "suggestions" not in gcfg:
                    gcfg["suggestions"] = {}
                gcfg["suggestions"]["channel_id"] = str(cid)
                self.ctrl.save()
                title = "💡 Salon de suggestions défini"
                desc = f"Les suggestions seront envoyées dans {pretty}."
                emb = discord.Embed(title=title, description=desc, color=self._theme)
                await interaction.response.edit_message(embed=emb, view=SuggestionsView(self.ctrl, self.gid, self._theme))
            else:
                gcfg[self.key] = str(cid)
                self.ctrl.save()
                emb = discord.Embed(title="⚙️ Configuration enregistrée", description=f"Paramètre sauvegardé : {pretty}", color=self._theme)
                await interaction.response.edit_message(embed=emb, view=VoiceTempView(self.ctrl, self.gid, self._theme))

        sel.callback = _cb
        self.add_item(sel)


class CategoryChooseView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color, key: str):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.key = key

        sel = discord.ui.ChannelSelect(
            placeholder="Choisis une catégorie Discord",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
            custom_id=f"config_category_select:{key}",
        )

        async def _cb(interaction: discord.Interaction):
            chan = sel.values[0]
            try:
                cid = int(chan.id)
            except Exception:
                await interaction.response.send_message("Catégorie invalide.", ephemeral=True)
                return

            ensure_guild_entry(self.ctrl.config, str(self.gid), interaction.guild)
            gcfg = self.ctrl.config.setdefault("guilds", {}).setdefault(str(self.gid), {})
            gcfg[self.key] = str(cid)
            self.ctrl.save()

            pretty = f"<#{cid}>"
            emb = discord.Embed(title="⚙️ Configuration enregistrée", description=f"Paramètre sauvegardé : {pretty}", color=self._theme)
            await interaction.response.edit_message(embed=emb, view=VoiceTempView(self.ctrl, self.gid, self._theme))

        sel.callback = _cb
        self.add_item(sel)


class VoiceTempConfigView(discord.ui.View):
    """View used in /config to pick the trigger voice channel and optional parent category."""
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
        self.gcfg = ensure_guild_entry(self.ctrl.config, self.gid, None)

        # Voice channel selector (trigger)
        self.voice_sel = discord.ui.ChannelSelect(
            placeholder="Choisis le salon vocal de trigger (ex: 🎤 ➕ Créer votre salon)",
            channel_types=[discord.ChannelType.voice],
            min_values=1,
            max_values=1,
            custom_id=f"config_voice_trigger_select:{gid}",
        )

        async def voice_cb(interaction: discord.Interaction):
            chan = self.voice_sel.values[0]
            try:
                cid = int(chan.id)
            except Exception:
                return await interaction.response.send_message("Salon invalide.", ephemeral=True)

            ensure_guild_entry(self.ctrl.config, str(self.gid), interaction.guild)
            gcfg = self.ctrl.config.setdefault("guilds", {}).setdefault(str(self.gid), {})
            gcfg["join_to_create_channel_id"] = str(cid)
            self.ctrl.save()
            await interaction.response.send_message(f"✅ Salon de trigger configuré : <#{cid}>", ephemeral=True)

        self.voice_sel.callback = voice_cb
        self.add_item(self.voice_sel)

        # Category selector (optional parent for created channels)
        self.cat_sel = discord.ui.ChannelSelect(
            placeholder="Choisis la catégorie parent (optionnel)",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
            custom_id=f"config_voice_parent_select:{gid}",
        )

        async def cat_cb(interaction: discord.Interaction):
            chan = self.cat_sel.values[0]
            try:
                cid = int(chan.id)
            except Exception:
                return await interaction.response.send_message("Catégorie invalide.", ephemeral=True)

            ensure_guild_entry(self.ctrl.config, str(self.gid), interaction.guild)
            gcfg = self.ctrl.config.setdefault("guilds", {}).setdefault(str(self.gid), {})
            gcfg["temp_voice_category_id"] = str(cid)
            self.ctrl.save()
            await interaction.response.send_message(f"✅ Catégorie parent définie : <#{cid}>", ephemeral=True)

        self.cat_sel.callback = cat_cb
        self.add_item(self.cat_sel)

    def build_embed(self) -> discord.Embed:
        trigger_ch = self.gcfg.get("join_to_create_channel_id")
        parent_cat = self.gcfg.get("temp_voice_category_id")
        
        trigger_status = f"✅ <#{trigger_ch}>" if trigger_ch else "❌ Non configuré"
        parent_status = f"✅ <#{parent_cat}>" if parent_cat else "❌ Non configuré"
        
        emb = discord.Embed(
            title="🎤 Salon vocaux temporaires",
            description=(
                "Join-To-Create automatique : crée un salon privé quand un utilisateur rejoint le salon\n"
                "de trigger. Configure ci‑dessous le salon de trigger (salon vocal fixe) et la catégorie parent."
            ),
            color=self._theme,
        )
        emb.add_field(name="🎤 Salon de trigger", value=trigger_status, inline=False)
        emb.add_field(name="📂 Catégorie parent", value=parent_status, inline=False)
        return emb

    @discord.ui.button(label="🔙 Retour", style=discord.ButtonStyle.secondary, custom_id="config_back", row=2)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConfigDashboardView(self.ctrl, self.gid, self._theme)
        emb = discord.Embed(
            title="⚙️ Configuration du serveur",
            description="Sélectionne une catégorie ci‑dessous pour modifier la configuration.",
            color=self._theme,
        )
        await interaction.response.edit_message(embed=emb, view=view)


class VoiceTempView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme
    # No interactive buttons here by design — Join-To-Create is triggered via voice state updates.


class ConfigRootView(discord.ui.View):
    def __init__(self, ctrl: ConfigController, gid: str, theme: discord.Color):
        super().__init__(timeout=None)
        self.ctrl = ctrl
        self.gid = gid
        self._theme = theme

    def build_embed(self) -> discord.Embed:
        cfg = self.ctrl.config
        gcfg = cfg.get("guilds", {}).get(self.gid, {})
        admin_roles = gcfg.get("admin_roles") or []
        mod_roles = gcfg.get("mod_roles") or []
        cats = gcfg.get("categories") or {}
        ticket_config = gcfg.get("ticket", {})
        current_cat_id = ticket_config.get("category_id")
        current_cat_name = ticket_config.get("category_name")
        
        emb = discord.Embed(
            title="👑 Panel Propriétaire",
            description="Gestion des rôles et des catégories de tickets.",
            color=self._theme,
        )
        emb.add_field(name="Serveur", value=f"`{self.gid}` · {gcfg.get('name', '—')}", inline=False)
        
        # Afficher la catégorie des tickets actuelle
        if current_cat_id:
            main_channel_id = ticket_config.get("main_channel_id")
            main_channel_name = ticket_config.get("main_channel_name")
            cat_display = f"**{current_cat_name or 'Nom inconnu'}**\n(ID : `{current_cat_id}`)"
            if main_channel_id:
                cat_display += f"\n📌 Salon : **{main_channel_name or 'Nom inconnu'}** (ID : `{main_channel_id}`)"
        else:
            cat_display = "*Non configurée*"
        emb.add_field(name="📂 Catégorie des tickets actuelle", value=cat_display, inline=False)
        
        emb.add_field(
            name="Rôles Admin",
            value=", ".join(f"<@&{r}>" for r in admin_roles) if admin_roles else "*aucun*",
            inline=False,
        )
        emb.add_field(
            name="Rôles Modérateur",
            value=", ".join(f"<@&{r}>" for r in mod_roles) if mod_roles else "*aucun*",
            inline=False,
        )
        emb.add_field(
            name="Catégories de tickets",
            value="\n".join([f"• `{k}`: {v.get('label', '')}" for k, v in cats.items()]) if cats else "*aucune*",
            inline=False,
        )
        return emb

    @discord.ui.button(label="📁 Catégorie tickets", style=discord.ButtonStyle.primary, row=0)
    async def b_cat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Choisis la catégorie Discord :",
            view=PickCategoryView(self.ctrl, self.gid),
            ephemeral=True,
        )

    @discord.ui.button(label="📋 Salon logs", style=discord.ButtonStyle.primary, row=0)
    async def b_log(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Choisis le salon texte des logs :",
            view=PickLogChannelView(self.ctrl, self.gid),
            ephemeral=True,
        )

    @discord.ui.button(label="👮 Rôles staff", style=discord.ButtonStyle.secondary, row=0)
    async def b_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Sélectionne les rôles :",
            view=PickStaffRolesView(self.ctrl, self.gid),
            ephemeral=True,
        )

    @discord.ui.button(label="➕ Entrée menu", style=discord.ButtonStyle.success, row=1)
    async def b_add_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddCategoryModal(self.ctrl, self.gid))

    @discord.ui.button(label="🗑 Retirer entrée", style=discord.ButtonStyle.danger, row=1)
    async def b_rm_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        cats = (
            self.ctrl.config.get("guilds", {}).get(self.gid, {}).get("categories") or {}
        )
        if not cats:
            return await interaction.response.send_message(
                "Aucune entrée menu à supprimer.", ephemeral=True
            )
        await interaction.response.send_message(
            "Clé à supprimer :",
            view=RemoveCategoryView(self.ctrl, self.gid),
            ephemeral=True,
        )

    @discord.ui.button(label="🌐 Nouveau serveur (ID)", style=discord.ButtonStyle.secondary, row=2)
    async def b_guild(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddGuildByIdModal(self.ctrl))

    @discord.ui.button(label="🔑 Gérer whitelist admins", style=discord.ButtonStyle.secondary, row=2)
    async def b_admins(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistAdminsModal(self.ctrl))

    @discord.ui.button(label="� Gérer commandes désactivées", style=discord.ButtonStyle.secondary, row=2)
    async def b_disabled_commands(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_disabled = self.ctrl.config.get("disabled_commands", [])
        modal = DisabledCommandsModal(self.ctrl)
        modal.commands_field.default = "\n".join(current_disabled) if current_disabled else ""
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="�🔄 Rafraîchir le panneau", style=discord.ButtonStyle.secondary, row=3)
    async def b_refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = self.build_embed()
        await interaction.response.edit_message(embed=emb, view=self)


