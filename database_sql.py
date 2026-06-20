from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey, Text, JSON
from datetime import datetime
from typing import Optional, List

class Base(DeclarativeBase):
    pass

class ModeOfTheBorderEditor(Base):
    __tablename__ = "mode_border_editor"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mode: Mapped[str] = mapped_column(String, default="")

class BorderOptions(Base):
    __tablename__ = 'border_options'
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gradient_yes_or_no: Mapped[str] = mapped_column(String, default="")
    solide_or_neon: Mapped[str] = mapped_column(String, default="")

class UserScm(Base):
    __tablename__ = 'userscm'
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bio_scm: Mapped[str] = mapped_column(String, default="")
    username: Mapped[str] = mapped_column(String, default="")
    password: Mapped[str] = mapped_column(String, default="")
    data_created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # ✅ CORRIGIDO: back_populates deve referenciar o nome do atributo na classe Posts
    posts: Mapped[List["Posts"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[List["Like"]] = relationship(back_populates="user")
    seguidores: Mapped[List["Follows"]] = relationship(back_populates="user", foreign_keys="[Follows.user_id]")

class Posts(Base):
    __tablename__ = 'posts'
    
    # ✅ CORRIGIDO: Mudado para Integer com autoincrement para evitar conflitos
    post_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ✅ CORRIGIDO: ForeignKey apontando para a tabela CORRETA 'userscm'
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("userscm.user_id", ondelete="CASCADE"))
    name_post: Mapped[str] = mapped_column(String, default="")
    name_file: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(Text, default="")  # ✅ Usar Text para textos longos
    extra_content: Mapped[str] = mapped_column(String, default="")
    gender_media: Mapped[dict] = mapped_column(JSON, default={})
    posted: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # ✅ CORRIGIDO: Relacionamentos corrigidos
    user: Mapped["UserScm"] = relationship(back_populates="posts")
    comments: Mapped[List["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    likes_rel: Mapped[List["Like"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    
class Comment(Base):
    __tablename__ = "comments"
    
    comment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ✅ CORRIGIDO: ForeignKey apontando para posts.post_id (BigInteger → Integer)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.post_id", ondelete="CASCADE"))
    # ✅ CORRIGIDO: ForeignKey apontando para userscm.user_id
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("userscm.user_id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text, default="")  # ✅ Usar Text para comentários
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    post: Mapped["Posts"] = relationship(back_populates="comments")
    user: Mapped["UserScm"] = relationship()

class Like(Base):
    __tablename__ = "likes"
    
    like_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ✅ CORRIGIDO: ForeignKey apontando para posts.post_id
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.post_id", ondelete="CASCADE"))
    # ✅ CORRIGIDO: ForeignKey apontando para userscm.user_id
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("userscm.user_id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    post: Mapped["Posts"] = relationship(back_populates="likes_rel")
    user: Mapped["UserScm"] = relationship(back_populates="likes")

class Follows(Base):
    __tablename__ = "seguidores"
    
    follow_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # ✅ CORRIGIDO: ForeignKey apontando para userscm.user_id
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("userscm.user_id", ondelete="CASCADE"))
    # ✅ CORRIGIDO: ForeignKey apontando para userscm.user_id (para o usuário seguido)
    follow_id_user: Mapped[int] = mapped_column(BigInteger, ForeignKey("userscm.user_id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # ✅ CORRIGIDO: Relacionamento corrigido
    user: Mapped["UserScm"] = relationship(back_populates="seguidores", foreign_keys=[user_id])
    # ✅ ADICIONADO: Relacionamento para o usuário seguido
    followed_user: Mapped["UserScm"] = relationship(foreign_keys=[follow_id_user])

class PostConfigurationEphemeral(Base):
    __tablename__ = 'ptcep'
    
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, primary_key=True)
    description_e: Mapped[str] = mapped_column(String, default="")
    name_post_e: Mapped[str] = mapped_column(String, default="")
    extra_content_e: Mapped[str] = mapped_column(String, default="")
    gender_media_e: Mapped[str] = mapped_column(JSON, default={"genders": []})
    name_file_e: Mapped[str] = mapped_column(String, default="")

class CustomizablePerfil(Base):
    __tablename__ = 'czplf'
    
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, primary_key=True)
    colors_faixa: Mapped[str] = mapped_column(String, default="#4F3EA5")
    colors_border: Mapped[str] = mapped_column(String, default="#000000FC")
    font_rw: Mapped[str] = mapped_column(String, default="fonts/Monad.otf")
    text_colors: Mapped[str] = mapped_column(String, default="#000000")
    bio_text_color: Mapped[str] = mapped_column(String, default="#000000")
    text_border_colors: Mapped[str] = mapped_column(String, default="#6200FF")
    color_plates: Mapped[str] = mapped_column(String, default="#6300F7FD")
    color_name_plate: Mapped[str] = mapped_column(String, default="#3E00A1")
    gender_for_pf: Mapped[str] = mapped_column(String, default="Masculino")

DATABASE_URL = "sqlite+aiosqlite:///./bancodb.db"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)  # ✅ echo=True para debug

AsyncSessionReze = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db_editor():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)