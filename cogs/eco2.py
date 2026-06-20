from cProfile import label
from code import interact
import random
from venv import create
from cv2 import add, clipLine
import discord
from discord import ButtonStyle, Interaction
from discord.ext import commands
from discord.ui import Button, View
from cogs.eco import interpretar_valor, get_user, add_saldo, retirar_saldo

class DificultSet(discord.ui.View):
    def __init__(self, ctx_author_id, quantidade):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_author_id
        self.quantidade = quantidade
        
    @discord.ui.button(label="Fácil (Lucro menor)", style=discord.ButtonStyle.green, custom_id="bg_easy_btn", row=1)
    async def easy_dificult(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!")

        dificult = "Easy"
        
        embed = discord.Embed(
            title="💣 BombGame!",
            color=discord.Color.light_grey(),
            timestamp=discord.utils.utcnow()
        )
        
        view = BombsButton(
            self.ctx_author_id, self.quantidade, dificult=dificult
        )
        
        await interaction.response.send_message(embed=embed, view=view)

    @discord.ui.button(label="Normal (Lucro mediano)", style=discord.ButtonStyle.blurple, custom_id="bg_mid_btn", row=2)
    async def mid_dificult(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!")
        
        dificult = "Mid"
        
        embed = discord.Embed(
            title="💣 BombGame!",
            color=discord.Color.light_grey(),
            timestamp=discord.utils.utcnow()
        )
        
        view = BombsButton(
            self.ctx_author_id, self.quantidade, dificult=dificult
        )
        
        await interaction.response.send_message(embed=embed, view=view)

    @discord.ui.button(label="Difícil (Lucro maior)", style=discord.ButtonStyle.red, custom_id="bg_hard_btn", row=3)
    async def hard_dificult(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!")
        
        dificult = "Hard"
        
        embed = discord.Embed(
            title="💣 BombGame!",
            color=discord.Color.light_grey(),
            timestamp=discord.utils.utcnow()
        )
        
        view = BombsButton(
            self.ctx_author_id, self.quantidade, dificult=dificult
        )
        
        await interaction.response.send_message(embed=embed, view=view)

class BombsButton(discord.ui.View):
    def __init__(self, ctx_autho_id, quantidade, dificult):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_autho_id
        self.quantidade = quantidade
        self.true_or_false_hard = [
            True, False, False, False
        ]
        self.true_or_false_mid = [
            True, False, False
        ]
        self.true_of_false_easy = [
            True, False
        ]
        self.dificult = dificult
        
        if self.dificult == "Easy":
            self.true_or_false = self.true_of_false_easy
            self.acress_multiplier = 0.05
        elif  self.dificult == "Mid":
            self.true_or_false = self.true_or_false_mid
            self.acress_multiplier = 0.08
        elif self.dificult == "Hard":
            self.true_or_false = self.true_or_false_hard
            self.acress_multiplier = 0.15
        self.correct_bombs = 0
        self.multiplier = 1
    
    async def false_author(self, interaction_, user_id_interact, ctx_author_id):
        
        if user_id_interact != ctx_author_id:
            await interaction_.response.send_message(
                "Somente o autor do comando pode clicar nesses botões!"
            , ephemeral=True
            )
            return False
        return True
            
    async def create_embed(self, true_or_false, user, correct_bombs):
        
        embed = discord.Embed(
            title="💣 Você foi bombardeado!",
            description=f"Você conseguiu marcar {correct_bombs} antes de explodir, a ganância acabou te matando né?",
            color=discord.Color.light_grey(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_footer(text=f"{user.name}", icon_url=user.avatar.url)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1410462821396774924/1444106697831612506/b89d3cf9119f0a0bcfe682ac99a20999.png?ex=692b80aa&is=692a2f2a&hm=8e61ed7e6e789930c32e365dec8d429fbb750a8cdf9651fbc5af4bcbc66e29b2&=&format=webp&quality=lossless&width=768&height=640")
        await retirar_saldo(user.id, self.quantidade)
        
        return embed
    
    async def edit_message(self, multipplier, user):
        
        embed = discord.Embed(
            title="📜 Status.",
            description=f"✖️ Multilplicador: {self.multiplier}\n💲 Lucro: {self.quantidade*self.multiplier}",
            color=discord.Color.light_grey(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_footer(text=f"{user.name}", icon_url=user.avatar.url)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1410462821396774924/1444111703020277931/68f5dcc3532a35c0702912d499159909.png?ex=692b8554&is=692a33d4&hm=72eb5685002dedcbcc1636defb7416e85f67948216c85fd152c7aa11a6a73b8b&=&format=webp&quality=lossless&width=689&height=672")
            
        return embed
        
    @discord.ui.button(label="1", style=discord.ButtonStyle.grey)
    async def button_bg1(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="2", style=discord.ButtonStyle.grey)
    async def button_bg2(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="3", style=discord.ButtonStyle.grey)
    async def button_bg3(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="4", style=discord.ButtonStyle.grey)
    async def button_bg4(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="5", style=discord.ButtonStyle.grey)
    async def button_bg5(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="6", style=discord.ButtonStyle.grey)
    async def button_bg6(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="7", style=discord.ButtonStyle.grey)
    async def button_bg7(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="8", style=discord.ButtonStyle.grey)
    async def button_bg8(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="9", style=discord.ButtonStyle.grey)
    async def button_bg9(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="10", style=discord.ButtonStyle.grey)
    async def button_bg10(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="11", style=discord.ButtonStyle.grey)
    async def button_bg11(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="12", style=discord.ButtonStyle.grey)
    async def button_bg12(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="13", style=discord.ButtonStyle.grey)
    async def button_bg13(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="14", style=discord.ButtonStyle.grey)
    async def button_bg14(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="15", style=discord.ButtonStyle.grey)
    async def button_bg15(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="16", style=discord.ButtonStyle.grey)
    async def button_bg16(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="17", style=discord.ButtonStyle.grey)
    async def button_bg17(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="18", style=discord.ButtonStyle.grey)
    async def button_bg18(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="19", style=discord.ButtonStyle.grey)
    async def button_bg19(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="20", style=discord.ButtonStyle.grey)
    async def button_bg20(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="21", style=discord.ButtonStyle.grey)
    async def button_bg21(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="22", style=discord.ButtonStyle.grey)
    async def button_bg22(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="23", style=discord.ButtonStyle.grey)
    async def button_bg23(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="24", style=discord.ButtonStyle.grey)
    async def button_bg24(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if not await self.false_author(interaction, interaction.user.id, self.ctx_author_id):
            return

        true_or_false = random.choice(self.true_or_false)
        button.disabled = True
        if true_or_false is False:
            button.style = discord.ButtonStyle.red
            for child in self.children:
                child.disabled = True
            embed = await self.create_embed(true_or_false, interaction.user, self.correct_bombs)            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            button.style = discord.ButtonStyle.green
            self.correct_bombs += 1
            self.multiplier += self.acress_multiplier
            embed = await self.edit_message(self.multiplier, interaction.user)

            await interaction.response.edit_message(embed=embed, view=self)
            
    @discord.ui.button(label="Sacar", style=discord.ButtonStyle.green)
    async def stop_bombgame(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        lucro = self.quantidade*self.multiplier
        await self.false_author(interaction, interaction.user.id, ctx_author_id=self.ctx_author_id)
        await add_saldo(interaction.user.id, lucro)
        
        embed = discord.Embed(
            title="💰 Dinheiro Sacado!",
            description=f"✅ Você acertou {self.correct_bombs} caixas que estavam sem bombas!\n🔢 Multiplicador: {self.multiplier}\n💸 Lucro Final: {self.quantidade*self.multiplier}",
            color=discord.Color.light_grey(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_footer(text=f"{interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1410462821396774924/1444111803939291341/c4ad97ecb76bc46b97e3d596b01e6d10.png?ex=692b856c&is=692a33ec&hm=b6e9003ed903543baccf330a476a1fb403b8cc379d8925f5995120c56cdbf869&=&format=webp&quality=lossless&width=638&height=425")
        
        await interaction.response.send_message(embed=embed)
             
class EconomicCommandsPart2(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
                       
    @commands.command(name="bombgame", aliases=["bg"])
    async def bombgame(self, ctx:commands.Context, quantidade:interpretar_valor = None):
        userdb = await get_user(ctx.author.id)
        
        if userdb.MDBs < quantidade:
            return await ctx.reply("❌ Não aposte uma quantidade maior que seu saldo!", ephemeral=True)
        
        if quantidade <= 0:
            return await ctx.reply("❌ Não aposte uma quantidade menor ou igual a zero!", ephemeral=True)
        
        embed = discord.Embed(
            title="🧨 Selecione a dificuldade.",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url)
        
        await ctx.reply(embed=embed, view=DificultSet(ctx.author.id, quantidade=quantidade))

async def setup(bot):
    await bot.add_cog(EconomicCommandsPart2(bot))