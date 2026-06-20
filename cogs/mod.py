import discord
from discord.ext import commands
import asyncio
import re
from sqlalchemy import select
from dbdata import ReactionRoleMessage, AsyncSessionLocal, UserMDBs
from discord import app_commands

def interpretar_valor(valor_str: str) -> int:
    valor_str = valor_str.lower().replace(",", ".").strip()
    multiplicadores = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}

    if valor_str[-1] in multiplicadores:
        try:
            numero = float(valor_str[:-1])
            return int(numero * multiplicadores[valor_str[-1]])
        except ValueError:
            raise ValueError("Valor de aposta inválido.")
    else:
        try:
            return int(float(valor_str))
        except ValueError:
            raise ValueError("Valor de aposta inválido.")

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.restore_reaction_roles())

    async def restore_reaction_roles(self):
        await self.bot.wait_until_ready()
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ReactionRoleMessage))
            rr_messages = result.scalars().all()

            for rr in rr_messages:
                try:
                    guild = self.bot.get_guild(int(rr.guild_id))
                    if not guild:
                        continue
                    channel = guild.get_channel(int(rr.channel_id))
                    if channel:
                        message = await channel.fetch_message(int(rr.message_id))
                        current_reactions = [str(r.emoji) for r in message.reactions]
                        for emoji in rr.role_data.keys():
                            if emoji not in current_reactions:
                                await message.add_reaction(emoji)
                except Exception as e:
                    print(f"Erro restaurando reaction role: {e}")

    @commands.command(name="addmdbs")
    @commands.is_owner()
    async def addmdbs(self, ctx: commands.Context, quantidade: interpretar_valor):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
            userdb = result.scalars().first()
            if not userdb:
                userdb = UserMDBs(membro_id=ctx.author.id, MDBs=0)
                session.add(userdb)
            userdb.MDBs += quantidade
            await session.commit()
            await ctx.reply(f"{quantidade} MDBs adicionados ao {ctx.author.name}")

    @commands.command(name="ban", aliases=["banir", "aplicarban", "banindo"])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, membro: discord.Member, *, motivo="Não especificado"):
        if not await self._check_permissions(ctx, membro):
            return

        try:
            await membro.send(f"🚫 Você foi **banido** do servidor **{ctx.guild.name}** pelo motivo: **{motivo}**")
        except:
            pass

        await membro.ban(reason=f"{motivo} | Banido por {ctx.author}")

        embed = discord.Embed(
            title="🚫 Membro Banido",
            color=discord.Color.red(),
            timestamp=ctx.message.created_at
        )
        embed.add_field(name="👤 Usuário", value=f"{membro} (`{membro.id}`)", inline=False)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.add_field(name="👮‍♂️ Banido por", value=f"{ctx.author} (`{ctx.author.id}`)", inline=False)
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text=f"Ação realizada por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para usar este comando!")

    @commands.command(name="unban", aliases=["desbanir", "desbanido"])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
        except:
            return await ctx.send("❌ Não consegui encontrar esse usuário no Discord.")

        async for ban_entry in ctx.guild.bans(limit=None):
            if ban_entry.user.id == user_id:
                try:
                    await ctx.guild.unban(ban_entry.user)
                    embed = discord.Embed(
                        title="✅ Usuário Desbanido",
                        description=f"O usuário **{user}** (`{user.id}`) foi desbanido com sucesso!",
                        color=discord.Color.green()
                    )
                    embed.set_thumbnail(url=user.display_avatar.url)
                    embed.set_footer(text=f"Ação executada por {ctx.author}", icon_url=ctx.author.display_avatar.url)
                    await ctx.send(embed=embed)
                    return
                except Exception as e:
                    return await ctx.send(f"❌ Falhou ao tentar desbanir: {e}")

        await ctx.send("⚠️ Usuário com esse ID não está banido.")

    @commands.command(name="mute", aliases=["mutar", "silenciar"])
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, membro: discord.Member, tempo=None, *, motivo="Não especificado"):
        if not await self._check_permissions(ctx, membro):
            return

        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            try:
                mute_role = await ctx.guild.create_role(name="Muted", color=discord.Color.dark_gray())
                for channel in ctx.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False, add_reactions=False)
            except Exception as e:
                return await ctx.send(f"❌ Não consegui criar o cargo `Muted`: `{e}`")

        segundos = self._parse_tempo(tempo) if tempo else None
        if tempo and segundos is None:
            return await ctx.send("❌ Formato de tempo inválido! Use algo como `10m`, `2h`, `1d`.")

        try:
            await membro.send(f"🔇 Você foi **mutado** no servidor **{ctx.guild.name}** pelo motivo: **{motivo}**" + (f" ⏳ Duração: {tempo}" if tempo else ""))
        except:
            pass

        await membro.add_roles(mute_role, reason=f"{motivo} | Mutado por {ctx.author}")

        embed = discord.Embed(
            title="🔇 Membro Mutado",
            color=discord.Color.orange(),
            timestamp=ctx.message.created_at
        )
        embed.add_field(name="👤 Usuário", value=f"{membro} (`{membro.id}`)", inline=False)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.add_field(name="👮 Aplicado por", value=f"{ctx.author} (`{ctx.author.id}`)", inline=False)
        if tempo:
            embed.add_field(name="⏳ Duração", value=tempo, inline=False)
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text=f"Ação realizada por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

        if segundos:
            await asyncio.sleep(segundos)
            if mute_role in membro.roles:
                await membro.remove_roles(mute_role, reason="Tempo de mute expirado")
                embed_unmute = discord.Embed(
                    title="✅ Membro Desmutado",
                    description=f"{membro.mention} foi desmutado automaticamente (tempo expirado).",
                    color=discord.Color.green(),
                    timestamp=ctx.message.created_at
                )
                await ctx.send(embed=embed_unmute)
                try:
                    await membro.send(f"✅ Seu mute no servidor **{ctx.guild.name}** expirou.")
                except:
                    pass

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para usar este comando!")

    @commands.command(name="unmute", aliases=["desmutar"])
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, membro: discord.Member, *, motivo="Não especificado"):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role or mute_role not in membro.roles:
            return await ctx.send("❌ Este usuário não está mutado.")

        await membro.remove_roles(mute_role, reason=f"{motivo} | Desmutado por {ctx.author}")

        embed = discord.Embed(
            title="✅ Membro Desmutado",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 Usuário", value=f"{membro.mention}", inline=False)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.set_footer(text=f"Ação por {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)
        try:
            await membro.send(f"✅ Você foi desmutado em **{ctx.guild.name}**.\nMotivo: **{motivo}**")
        except:
            pass

    @commands.command(name="limpar", aliases=["clean", "clear"])
    @commands.has_permissions(manage_messages=True)
    async def limpar(self, ctx, quantidade: int):
        if quantidade < 1 or quantidade > 500:
            await ctx.send("❌ Escolha um número entre 1 e 500!", delete_after=5)
            return
        deleted = await ctx.channel.purge(limit=quantidade + 1)
        await ctx.send(f"✅ {len(deleted) - 1} mensagens foram apagadas!", delete_after=5)

    @limpar.error
    async def limpar_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para apagar mensagens!", delete_after=5)

    @commands.command(name="LDRA", aliases=["verificarrda"])
    @commands.has_permissions(manage_guild=True)
    async def lrda(self, ctx):
        if not ctx.guild.me.guild_permissions.view_audit_log:
            return await ctx.send("❌ Requer permissão para ver logs de auditoria.")

        logs = [entry async for entry in ctx.guild.audit_logs(limit=5)]
        log_message = "**Leitura do RDA.**\n"
        for log in logs:
            log_message += (
                f"Ação: {log.action}\n"
                f"Usuario: {log.user}\n"
                f"Alvo: {log.target}\n"
                f"Data: {log.created_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
                "-------------------------\n"
            )
        await ctx.send(log_message)

    @commands.command(name="msg")
    @commands.is_owner()
    async def enviar_msg(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        await channel.send(message)

    # ========== REACTION ROLES (SLASH) ==========

    @app_commands.command(name="rrcreate", description="Cria uma mensagem de reaction role")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        channel="Canal onde a mensagem será enviada",
        title="Título da mensagem",
        description="Descrição da mensagem",
        role1="Primeiro cargo para associar",
        emoji1="Emoji para o primeiro cargo",
        role2="Segundo cargo (opcional)",
        emoji2="Emoji para o segundo cargo (opcional)",
        role3="Terceiro cargo (opcional)",
        emoji3="Emoji para o terceiro cargo (opcional)",
        role4="Quarto cargo (opcional)",
        emoji4="Emoji para o quarto cargo (opcional)",
        role5="Quinto cargo (opcional)",
        emoji5="Emoji para o quinto cargo (opcional)"
    )
    async def rrcreate(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        role1: discord.Role,
        emoji1: str,
        role2: discord.Role = None,
        emoji2: str = None,
        role3: discord.Role = None,
        emoji3: str = None,
        role4: discord.Role = None,
        emoji4: str = None,
        role5: discord.Role = None,
        emoji5: str = None
    ):
        role_data = {}
        for emoji, role in [(emoji1, role1), (emoji2, role2), (emoji3, role3), (emoji4, role4), (emoji5, role5)]:
            if emoji and role:
                role_data[str(emoji)] = role.id

        if not role_data:
            return await interaction.response.send_message("❌ Você precisa fornecer pelo menos um par emoji/cargo válido.", ephemeral=True)

        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        instructions = "\n".join(f"{emoji} → {interaction.guild.get_role(role_id).mention}" for emoji, role_id in role_data.items())
        embed.add_field(name="Reaja para receber o cargo:", value=instructions, inline=False)
        embed.set_footer(text="Reaction Roles")

        await interaction.response.send_message(f"✅ Mensagem será criada em {channel.mention}!", ephemeral=True)
        message = await channel.send(embed=embed)

        for emoji in role_data.keys():
            try:
                await message.add_reaction(emoji)
            except:
                await interaction.followup.send(f"❌ Não consegui adicionar a reação {emoji}", ephemeral=True)

        async with AsyncSessionLocal() as session:
            try:
                new_rr = ReactionRoleMessage(
                    guild_id=str(interaction.guild.id),
                    message_id=str(message.id),
                    channel_id=str(channel.id),
                    role_data=role_data
                )
                session.add(new_rr)
                await session.commit()
            except Exception as e:
                await session.rollback()
                await interaction.followup.send(f"❌ Erro ao salvar no banco: {e}", ephemeral=True)

    @app_commands.command(name="rrlist", description="Lista todas as mensagens de reaction role no servidor")
    @app_commands.default_permissions(administrator=True)
    async def rrlist(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ReactionRoleMessage).filter_by(guild_id=str(interaction.guild.id)))
            rr_messages = result.scalars().all()

            if not rr_messages:
                return await interaction.response.send_message("ℹ️ Nenhuma mensagem de reaction role encontrada.", ephemeral=True)

            embed = discord.Embed(title="Mensagens de Reaction Role", color=discord.Color.green())
            for rr in rr_messages:
                channel = interaction.guild.get_channel(int(rr.channel_id))
                channel_info = f"Canal: {channel.mention}" if channel else f"Canal ID: {rr.channel_id}"
                roles_info = "\n".join(f"{emoji} → {interaction.guild.get_role(role_id).mention}" for emoji, role_id in rr.role_data.items())
                embed.add_field(name=f"Mensagem ID: {rr.message_id}", value=f"{channel_info}\n{roles_info}", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="rrdelete", description="Remove uma mensagem de reaction role")
    @app_commands.default_permissions(administrator=True)
    async def rrdelete(self, interaction: discord.Interaction, message_id: str):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ReactionRoleMessage).filter_by(guild_id=str(interaction.guild.id), message_id=message_id)
            )
            rr_message = result.scalars().first()

            if not rr_message:
                return await interaction.response.send_message("❌ Mensagem não encontrada.", ephemeral=True)

            try:
                channel = interaction.guild.get_channel(int(rr_message.channel_id))
                if channel:
                    msg = await channel.fetch_message(int(rr_message.message_id))
                    await msg.delete()
            except:
                pass

            await session.delete(rr_message)
            await session.commit()
            await interaction.response.send_message("✅ Reaction role removido com sucesso!", ephemeral=True)

    # ========== EVENTOS ==========

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ReactionRoleMessage).filter_by(message_id=str(payload.message_id)))
            rr_message = result.scalars().first()

            if rr_message:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                role_id = rr_message.role_data.get(str(payload.emoji))
                if role_id:
                    role = guild.get_role(role_id)
                    if role:
                        await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ReactionRoleMessage).filter_by(message_id=str(payload.message_id)))
            rr_message = result.scalars().first()

            if rr_message:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                role_id = rr_message.role_data.get(str(payload.emoji))
                if role_id:
                    role = guild.get_role(role_id)
                    if role and role in member.roles:
                        await member.remove_roles(role)

    # ========== FUNÇÕES AUXILIARES ==========

    async def _check_permissions(self, ctx, membro: discord.Member) -> bool:
        autor = ctx.author
        bot_user = ctx.guild.me

        if membro == autor:
            await ctx.send("❌ Você não pode fazer isso com você mesmo!")
            return False

        if membro == bot_user:
            await ctx.send("❌ Eu não posso fazer isso comigo mesmo!")
            return False

        if autor.top_role <= membro.top_role:
            await ctx.send("❌ Você não pode fazer isso com alguém com cargo **igual ou superior** ao seu!")
            return False

        if bot_user.top_role <= membro.top_role:
            await ctx.send("❌ Eu não consigo fazer isso com alguém com cargo **igual ou superior** ao meu!")
            return False

        return True

    def _parse_tempo(self, tempo: str) -> int:
        match = re.match(r"(\d+)([smhd])", tempo.lower())
        if match:
            valor, unidade = int(match.group(1)), match.group(2)
            unidades = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            return valor * unidades.get(unidade, 0)
        return None

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))