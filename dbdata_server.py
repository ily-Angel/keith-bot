from discord.ext.commands import when_mentioned_or
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey, JSON, select
from datetime import datetime
import asyncio

class Base(DeclarativeBase):
    pass

class BancoDeDadosParaMensagemDeBemVindoPersonalizada(Base):
    __tablename__ = 'data_for_message_g_and_w'

    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    cor_embed: Mapped[str] = mapped_column(String, default='')
    font_message: Mapped[str] = mapped_column(String, default='')
    message_main: Mapped[str] = mapped_column(String, default='')
    message_embed: Mapped[str] = mapped_column(String, default='')
    tamanho_da_imagem: Mapped[int] = mapped_column(Integer, default=0)
    largura_da_imagem: Mapped[int] = mapped_column(Integer, default=0)
    MODO: Mapped[str] = mapped_column(String, default='')
    cor_text1: Mapped[str] = mapped_column(String, default='')
    cor_text2: Mapped[str] = mapped_column(String, default='')
    size_text1: Mapped[int] = mapped_column(Integer, default=0)
    size_text2: Mapped[int] = mapped_column(Integer, default=0)
    text_content1: Mapped[str] = mapped_column(String, default='')
    text_content2: Mapped[str] = mapped_column(String, default='')
    translucidez_faixa: Mapped[int] = mapped_column(Integer, default=0)
    cor_faixa: Mapped[str] = mapped_column(String, default='')
    canal_bem_vindo: Mapped[int] = mapped_column(Integer, default=0)

class DataForExtrasForWelcomeMessage(Base):
    __tablename__ = 'data_for_extras_welcome_msg'

    guild_id: Mapped[int] = mapped_column(String, default='', primary_key=True)
    embed_true_false: Mapped[str] = mapped_column(String, default='')
    imagem_enter_embed: Mapped[str] = mapped_column(String, default='')
    text_for_embed: Mapped[str] = mapped_column(String, default='')
    color_for_embed: Mapped[str] = mapped_column(String, default='')
    footer_for_embed: Mapped[str] = mapped_column(String, default='')
    title_for_embed: Mapped[str] = mapped_column(String, default='')
    thumbnail_for_embed: Mapped[str] = mapped_column(String, default='')
    role_for_message_or_user: Mapped[str] = mapped_column(String, default='')
    role_: Mapped[int] = mapped_column(String, default='')
    user_: Mapped[int] = mapped_column(String, default='')

class DataForGoodbyeMessage(Base):
    __tablename__ = 'data_goodbye_message'

    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    cor_embed: Mapped[str] = mapped_column(String, default='')
    font_message: Mapped[str] = mapped_column(String, default='')
    message_main: Mapped[str] = mapped_column(String, default='')
    message_embed: Mapped[str] = mapped_column(String, default='')
    tamanho_da_imagem: Mapped[int] = mapped_column(Integer, default=0)
    largura_da_imagem: Mapped[int] = mapped_column(Integer, default=0)
    MODO: Mapped[str] = mapped_column(String, default='')
    cor_text1: Mapped[str] = mapped_column(String, default='')
    cor_text2: Mapped[str] = mapped_column(String, default='')
    size_text1: Mapped[int] = mapped_column(Integer, default=0)
    size_text2: Mapped[int] = mapped_column(Integer, default=0)
    text_content1: Mapped[str] = mapped_column(String, default='')
    text_content2: Mapped[str] = mapped_column(String, default='')
    translucidez_faixa: Mapped[int] = mapped_column(Integer, default=0)
    cor_faixa: Mapped[str] = mapped_column(String, default='')
    canal_bem_vindo: Mapped[int] = mapped_column(Integer, default=0)

class DataForExtrasForGoodbyeMessage(Base):
    __tablename__ = 'data_for_extras_goodbye_msg'

    guild_id: Mapped[int] = mapped_column(String, default='', primary_key=True)
    embed_true_false: Mapped[str] = mapped_column(String, default='')
    imagem_enter_embed: Mapped[str] = mapped_column(String, default='')
    text_for_embed: Mapped[str] = mapped_column(String, default='')
    color_for_embed: Mapped[str] = mapped_column(String, default='')
    footer_for_embed: Mapped[str] = mapped_column(String, default='')
    title_for_embed: Mapped[str] = mapped_column(String, default='')
    thumbnail_for_embed: Mapped[str] = mapped_column(String, default='')
    role_for_message_or_user: Mapped[str] = mapped_column(String, default='')
    role_: Mapped[int] = mapped_column(String, default='')
    user_: Mapped[int] = mapped_column(String, default='')

class PlaceholdersExtras(Base):
    __tablename__ = 'placeholders'

    guild_id: Mapped[int] = mapped_column(Integer, default=0, primary_key=True)
    member_count: Mapped[str] = mapped_column(String, default='')
    mention_emmber: Mapped[str] = mapped_column(String, default='')
    role_mention_quest: Mapped[str] = mapped_column(String, default='')
    role_mention: Mapped[str] = mapped_column(Integer, default=0)
    
class ChatForMessageUperLevelXp(Base):
    __tablename__ = 'chat_for_message_uper_level'
    
    guild_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, default=0)

DATABASE_URL = "sqlite+aiosqlite:///./serverconfigs.db"  # pode trocar por postgresql+asyncpg

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionServerConfigs = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


# =========================
# INIT DB
# =========================
async def init_db_server():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)