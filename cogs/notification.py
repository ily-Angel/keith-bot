from dbdata import AsyncSessionLocal, NotificationUser
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from sqlalchemy import select
import asyncio

import colorsys

class SuporteView(discord.ui.View):
    def __init__(self, timeout=100):
        super().__init__(timeout=timeout)
        
        
        self.add_item(discord.ui.Button(
            label="┃ Top.gg ",
            url="https://top.gg/bot/1367932530938089472",
            emoji="<:topgg:1406323879130955957>"
        ))
        
        
        self.add_item(discord.ui.Button(
            label="┃ Discord Bot List ",
            url="https://discordbotlist.com/bots/keith",
            emoji="<:discordbotlist:1406323822705119292>"
        ))
        
        
        self.add_item(discord.ui.Button(
            label="┃ Discord Bots ",
            url="https://discord.bots.gg/bots/1367932530938089472",
            emoji="<:botgg:1406323770238701638>"
        ))


    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if hasattr(self, "message"):
            await self.message.edit(view=self)

import time

async def gradiente(embed, msg, view, duracao=100):
    hue = random.random()
    passo = 0.03
    inicio = time.time()

    while not view.is_finished() and (time.time() - inicio < duracao):
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
        embed.color = discord.Color.from_rgb(int(r*255), int(g*255), int(b*255))
        await msg.edit(embed=embed)

        hue = (hue + passo) % 1 
        await asyncio.sleep(0.3)

class NotificationSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notification_loop.start()

    def cog_unload(self):
        self.notification_loop.cancel()

    @tasks.loop(minutes=5)
    async def notification_loop(self):

        embed = discord.Embed(
          title="Gostaria de dar uma ajudinha pro Keith?",
          description="Vote em mim para que eu fique famoso!",
          color=discord.Color.purple(),
          timestamp=discord.utils.utcnow()
        )
      
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(NotificationUser)
            )
            users = result.scalars().all()

            now = datetime.utcnow()

            for user in users:
                if now - user.last_sent >= timedelta(hours=13):
                    discord_user = self.bot.get_user(user.user_id)

                    if not discord_user:
                        continue

                    try:
                        await discord_user.send(
                            embed=embed, view=SuporteView()
                        )
                        user.last_sent = now
                    except discord.Forbidden:
                        pass

            await session.commit()

    @commands.command(name="forcarnotificacao")
    @commands.is_owner()
    async def force_notification(self, ctx):

        embed = discord.Embed(
          title="Gostaria de dar uma ajudinha pro Keith?",
          description="Vote em mim para que eu fique famoso!",
          color=discord.Color.purple(),
          timestamp=discord.utils.utcnow()
        )
      
      
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(NotificationUser)
            )
            users = result.scalars().all()
    
            if not users:
                await ctx.send("Nenhum usuário cadastrado para receber notificações.")
                return
    
            enviados = 0
            falhas = 0
            agora = datetime.utcnow()
    
            for user in users:
                discord_user = self.bot.get_user(user.user_id)
    
                if not discord_user:
                    falhas += 1
                    continue
    
                try:
                    await discord_user.send(
                        embed=embed, view=SuporteView()
                    )
                    user.last_sent = agora
                    enviados += 1
                except discord.Forbidden:
                    falhas += 1
    
            await session.commit()
    
        await ctx.send(
            f"📊 Notificação forçada concluída:\n"
            f"✅ Enviadas: {enviados}\n"
            f"❌ Falhas: {falhas}"
        )

    @commands.command(name="addnotificacao")
    @commands.is_owner()
    async def add_notification_user(self, ctx, member: discord.Member):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(NotificationUser).where(
                    NotificationUser.user_id == member.id
                )
            )
            user = result.scalar_one_or_none()

            if user:
                await ctx.send("Esse usuário já está cadastrado no sistema.")
                return

            session.add(
                NotificationUser(
                    user_id=member.id,
                    last_sent=datetime.utcnow()
                )
            )
            await session.commit()

        await ctx.send(f"{member.mention} foi adicionado ao sistema de notificações.")

    @commands.command(name="notificarme", aliases=["ativarnotificacao", "addnotif"])
    async def self_add_notification(self, ctx):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(NotificationUser).where(
                    NotificationUser.user_id == ctx.author.id
                )
            )
            user = result.scalar_one_or_none()

            if user:
                await ctx.send("Você já está cadastrado para receber notificações.")
                return

            session.add(
                NotificationUser(
                    user_id=ctx.author.id,
                    last_sent=datetime.utcnow()
                )
            )
            await session.commit()

        await ctx.send("Você foi cadastrado para receber notificações a cada 13 horas.")

        try:
            await ctx.author.send(
                "✅ Você se cadastrou com sucesso no sistema de notificações."
            )
        except discord.Forbidden:
            pass

    @commands.command(name="desativarnotif")
    async def self_remove_notification(self, ctx):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(NotificationUser).where(
                    NotificationUser.user_id == ctx.author.id
                )
            )
            user = result.scalar_one_or_none()

            if not user:
                await ctx.send("Você não está cadastrado para receber notificações.")
                return

            await session.delete(user)
            await session.commit()

        await ctx.send("❌ Você não receberá mais notificações automáticas.")

        try:
            await ctx.author.send(
                "Você saiu do sistema de notificações com sucesso."
            )
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(NotificationSystem(bot))